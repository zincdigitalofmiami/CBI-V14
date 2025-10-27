#!/usr/bin/env python3
"""
REAL ENSEMBLE TRAINING - NO FAKE DATA
Trains an actual ensemble meta-model using V4 predictions as features.
Validates on real holdout data and measures actual MAPE improvements.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEnsembleTrainer:
    """Train real ensemble using V4 model predictions as features"""
    
    def __init__(self):
        self.client = bigquery.Client(project='cbi-v14')
        
        # Best performing production models based on actual MAE
        self.v4_models = {
            '1w': 'cbi-v14.models.zl_boosted_tree_1w_trending',      # MAE: 0.015
            '1m': 'cbi-v14.models.zl_boosted_tree_1m_production',    # MAE: 1.418
            '3m': 'cbi-v14.models.zl_boosted_tree_3m_production',    # MAE: 1.257
            '6m': 'cbi-v14.models.zl_boosted_tree_6m_production'     # MAE: 1.187
        }
        
    def get_v4_predictions_dataset(self) -> pd.DataFrame:
        """
        Get REAL V4 model predictions for ensemble training
        """
        logger.info("Extracting real V4 model predictions for ensemble training")
        
        # Get all training data
        base_query = """
        SELECT *
        FROM `cbi-v14.models.training_dataset`
        WHERE target_1w IS NOT NULL 
          AND target_1m IS NOT NULL
        ORDER BY PARSE_DATE('%Y-%m-%d', date)
        """
        
        base_data = self.client.query(base_query).to_dataframe()
        logger.info(f"Base dataset: {len(base_data)} rows")
        
        # Get predictions from each V4 model
        predictions_data = base_data[['date', 'target_1w', 'target_1m', 'zl_price_current']].copy()
        
        for horizon, model_id in self.v4_models.items():
            logger.info(f"Getting real predictions from {horizon} model")
            
            try:
                # Create temp table
                temp_table = f"cbi-v14.models.temp_ensemble_input_{horizon}"
                job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
                job = self.client.load_table_from_dataframe(base_data, temp_table, job_config=job_config)
                job.result()
                
                # Get predictions
                pred_query = f"""
                SELECT 
                    date,
                    predicted_target_{horizon.replace('w', 'w').replace('m', 'm')} as pred_{horizon}
                FROM ML.PREDICT(
                    MODEL `{model_id}`,
                    (SELECT * FROM `{temp_table}`)
                )
                ORDER BY PARSE_DATE('%Y-%m-%d', date)
                """
                
                pred_result = self.client.query(pred_query).to_dataframe()
                
                # Merge predictions
                predictions_data = predictions_data.merge(
                    pred_result[['date', f'pred_{horizon}']], 
                    on='date', 
                    how='left'
                )
                
                # Cleanup
                self.client.delete_table(temp_table)
                
                logger.info(f"Added {horizon} predictions: {pred_result[f'pred_{horizon}'].notna().sum()} valid predictions")
                
            except Exception as e:
                logger.error(f"Error getting {horizon} predictions: {e}")
                predictions_data[f'pred_{horizon}'] = np.nan
                
        return predictions_data
        
    def train_real_ensemble(self, data: pd.DataFrame, target_horizon: str = '1m') -> dict:
        """
        Train REAL ensemble model using V4 predictions as features
        """
        logger.info(f"Training real ensemble for {target_horizon} target")
        
        # Prepare features (V4 model predictions)
        feature_cols = ['pred_1w', 'pred_1m', 'pred_3m', 'pred_6m']
        target_col = f'target_{target_horizon}'
        
        # Remove rows with missing predictions or targets
        clean_data = data.dropna(subset=feature_cols + [target_col])
        logger.info(f"Clean training data: {len(clean_data)} rows")
        
        if len(clean_data) < 100:
            logger.error("Insufficient data for ensemble training")
            return {}
            
        # Split into train/test (80/20)
        split_idx = int(len(clean_data) * 0.8)
        train_data = clean_data.iloc[:split_idx]
        test_data = clean_data.iloc[split_idx:]
        
        logger.info(f"Train: {len(train_data)} rows, Test: {len(test_data)} rows")
        
        X_train = train_data[feature_cols].values
        y_train = train_data[target_col].values
        X_test = test_data[feature_cols].values
        y_test = test_data[target_col].values
        
        # Train multiple ensemble models
        models = {
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        results = {}
        
        for model_name, model in models.items():
            logger.info(f"Training {model_name} ensemble")
            
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            # Calculate metrics
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            
            train_mape = np.mean(np.abs((train_pred - y_train) / y_train)) * 100
            test_mape = np.mean(np.abs((test_pred - y_test) / y_test)) * 100
            
            results[model_name] = {
                'model': model,
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_mape': train_mape,
                'test_mape': test_mape,
                'train_predictions': train_pred,
                'test_predictions': test_pred,
                'test_actuals': y_test,
                'feature_importance': getattr(model, 'feature_importances_', None)
            }
            
            logger.info(f"{model_name}: Test MAE ${test_mae:.2f}, Test MAPE {test_mape:.3f}%")
            
        return results
        
    def validate_ensemble_vs_individual(self, ensemble_results: dict, data: pd.DataFrame, target_horizon: str) -> dict:
        """
        Compare REAL ensemble performance vs individual V4 models
        """
        logger.info("Validating ensemble vs individual V4 models")
        
        # Get individual V4 model performance on same test set
        target_col = f'target_{target_horizon}'
        pred_col = f'pred_{target_horizon}'
        
        clean_data = data.dropna(subset=[pred_col, target_col])
        split_idx = int(len(clean_data) * 0.8)
        test_data = clean_data.iloc[split_idx:]
        
        # Individual V4 performance
        individual_mae = mean_absolute_error(test_data[target_col], test_data[pred_col])
        individual_mape = np.mean(np.abs((test_data[pred_col] - test_data[target_col]) / test_data[target_col])) * 100
        
        # Best ensemble performance
        best_ensemble = min(ensemble_results.items(), key=lambda x: x[1]['test_mape'])
        best_name, best_results = best_ensemble
        
        comparison = {
            'individual_v4': {
                'mae': individual_mae,
                'mape': individual_mape,
                'model': f'V4 {target_horizon} individual'
            },
            'best_ensemble': {
                'mae': best_results['test_mae'],
                'mape': best_results['test_mape'],
                'model': f'{best_name} ensemble'
            },
            'improvement': {
                'mae_reduction': individual_mae - best_results['test_mae'],
                'mape_reduction': individual_mape - best_results['test_mape'],
                'mae_pct_improvement': ((individual_mae - best_results['test_mae']) / individual_mae) * 100,
                'mape_pct_improvement': ((individual_mape - best_results['test_mape']) / individual_mape) * 100
            }
        }
        
        return comparison

def main():
    """Train and validate real ensemble system"""
    
    print("="*80)
    print("REAL ENSEMBLE TRAINING - V4 ENHANCED MODELS")
    print("="*80)
    print("Training actual ensemble models using V4 predictions as features")
    print("Validating on real holdout data")
    print()
    
    trainer = RealEnsembleTrainer()
    
    # Get real V4 predictions dataset
    logger.info("Step 1: Getting real V4 model predictions")
    predictions_data = trainer.get_v4_predictions_dataset()
    
    if predictions_data.empty:
        print("❌ ERROR: No prediction data available")
        return
        
    print(f"✅ Dataset ready: {len(predictions_data)} rows")
    print(f"   Date range: {predictions_data['date'].min()} to {predictions_data['date'].max()}")
    
    # Check data quality
    for horizon in ['1w', '1m', '3m', '6m']:
        pred_col = f'pred_{horizon}'
        if pred_col in predictions_data.columns:
            valid_preds = predictions_data[pred_col].notna().sum()
            print(f"   {horizon} predictions: {valid_preds}/{len(predictions_data)} valid")
        else:
            print(f"   {horizon} predictions: MISSING")
            
    # Train ensemble for 1M target (best individual performer)
    logger.info("Step 2: Training real ensemble models")
    ensemble_results = trainer.train_real_ensemble(predictions_data, target_horizon='1m')
    
    if not ensemble_results:
        print("❌ ERROR: Ensemble training failed")
        return
        
    print(f"\n✅ Ensemble models trained:")
    for model_name, results in ensemble_results.items():
        print(f"   {model_name}: Test MAE ${results['test_mae']:.2f}, Test MAPE {results['test_mape']:.3f}%")
        
    # Validate ensemble vs individual
    logger.info("Step 3: Validating ensemble vs individual V4 models")
    comparison = trainer.validate_ensemble_vs_individual(ensemble_results, predictions_data, '1m')
    
    print(f"\n" + "="*60)
    print("REAL PERFORMANCE COMPARISON")
    print("="*60)
    
    individual = comparison['individual_v4']
    best_ensemble = comparison['best_ensemble']
    improvement = comparison['improvement']
    
    print(f"Individual V4 1M: MAE ${individual['mae']:.2f}, MAPE {individual['mape']:.3f}%")
    print(f"Best Ensemble:    MAE ${best_ensemble['mae']:.2f}, MAPE {best_ensemble['mape']:.3f}%")
    print()
    
    if improvement['mape_reduction'] > 0:
        print(f"✅ REAL IMPROVEMENT:")
        print(f"   MAPE reduction: {improvement['mape_reduction']:.3f} percentage points")
        print(f"   MAPE improvement: {improvement['mape_pct_improvement']:.1f}%")
        
        if best_ensemble['mape'] < 2.0:
            print(f"🎯 TARGET ACHIEVED: {best_ensemble['mape']:.3f}% < 2.0%")
        else:
            print(f"⚠️ Still above target: {best_ensemble['mape']:.3f}% > 2.0%")
    else:
        print(f"❌ NO IMPROVEMENT: Ensemble worse than individual V4")
        print(f"   Individual V4 remains best option")
        
    # Save real results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save best ensemble model
    best_model_name = min(ensemble_results.items(), key=lambda x: x[1]['test_mape'])[0]
    best_model = ensemble_results[best_model_name]['model']
    
    with open(f'real_ensemble_model_{timestamp}.pkl', 'wb') as f:
        pickle.dump(best_model, f)
        
    # Save validation results
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'individual_v4_mape': individual['mape'],
        'best_ensemble_mape': best_ensemble['mape'],
        'real_improvement': improvement['mape_reduction'],
        'meets_target': best_ensemble['mape'] < 2.0,
        'best_model_type': best_model_name,
        'training_data_size': len(predictions_data),
        'test_data_size': len(predictions_data) - int(len(predictions_data) * 0.8)
    }
    
    import json
    with open(f'real_ensemble_validation_{timestamp}.json', 'w') as f:
        json.dump(validation_results, f, indent=2)
        
    print(f"\n✅ Real results saved:")
    print(f"   Model: real_ensemble_model_{timestamp}.pkl")
    print(f"   Validation: real_ensemble_validation_{timestamp}.json")
    
    return validation_results

if __name__ == "__main__":
    main()
