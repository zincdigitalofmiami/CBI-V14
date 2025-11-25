#!/usr/bin/env python3
"""
Model Status Checker - Workaround for INFORMATION_SCHEMA.MODELS limitation
Uses ML.* functions which work reliably without INFORMATION_SCHEMA access
"""

from google.cloud import bigquery
from datetime import datetime

def check_model_status(model_name, client):
    """Check if a model exists using ML functions (workaround for INFORMATION_SCHEMA.MODELS)"""
    model_path = f'cbi-v14.models_v4.{model_name}'
    
    # Method 1: Try ML.TRIAL_INFO (for hyperparameter-tuned models)
    try:
        query = f'''
        SELECT COUNT(*) as trial_count
        FROM ML.TRIAL_INFO(MODEL `{model_path}`)
        '''
        result = client.query(query).to_dataframe()
        trial_count = result['trial_count'].iloc[0] if len(result) > 0 else 0
        return {
            'exists': True,
            'method': 'ML.TRIAL_INFO',
            'trial_count': trial_count,
            'status': 'EXISTS'
        }
    except Exception as e:
        error_str = str(e)
        if 'not found' in error_str.lower():
            if 'not yet trained' in error_str.lower():
                return {
                    'exists': False,
                    'method': 'ML.TRIAL_INFO',
                    'status': 'TRAINING',
                    'trial_count': 0
                }
            else:
                return {
                    'exists': False,
                    'method': 'ML.TRIAL_INFO',
                    'status': 'NOT_EXISTS',
                    'trial_count': 0
                }
    
    # Method 2: Try ML.TRAINING_INFO (for non-hyperparameter models)
    try:
        query = f'''
        SELECT COUNT(*) as iter_count
        FROM ML.TRAINING_INFO(MODEL `{model_path}`)
        '''
        result = client.query(query).to_dataframe()
        iter_count = result['iter_count'].iloc[0] if len(result) > 0 else 0
        return {
            'exists': True,
            'method': 'ML.TRAINING_INFO',
            'iterations': iter_count,
            'status': 'EXISTS'
        }
    except:
        pass
    
    return {
        'exists': False,
        'method': 'UNKNOWN',
        'status': 'NOT_EXISTS'
    }


def main():
    """Check status of all 4 models"""
    client = bigquery.Client(project='cbi-v14')
    
    print('='*70)
    print('📊 MODEL STATUS CHECK (Workaround for INFORMATION_SCHEMA.MODELS)')
    print('='*70)
    print(f'Checked at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    models = ['bqml_1w_mean', 'bqml_1m_mean', 'bqml_3m_mean', 'bqml_6m_mean']
    
    results = {}
    for model_name in models:
        status = check_model_status(model_name, client)
        results[model_name] = status
        
        icon = '✅' if status['exists'] else '🔄' if status['status'] == 'TRAINING' else '❌'
        extra = ''
        
        if status['exists']:
            if 'trial_count' in status and status['trial_count'] > 0:
                extra = f" ({status['trial_count']} trials)"
            elif 'iterations' in status and status['iterations'] > 0:
                extra = f" ({status['iterations']} iterations)"
        
        print(f'{icon} {model_name}:')
        print(f'   Status: {status["status"]}')
        print(f'   Method: {status["method"]}{extra}')
        print()
    
    print('='*70)
    print('✅ Status check complete')
    print('='*70)
    print()
    print('Note: This uses ML.* functions which work reliably')
    print('without requiring INFORMATION_SCHEMA.MODELS access.')


if __name__ == '__main__':
    main()










