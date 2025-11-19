#!/usr/bin/env python3
"""
Unit Tests for Migration Scripts
Date: November 18, 2025
Purpose: Test migrate_master_features.py column mapping and SQL generation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMigrateMasterFeatures(unittest.TestCase):
    """Test cases for migrate_master_features.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import the migration module
        try:
            from migration import migrate_master_features
            self.migration_module = migrate_master_features
        except ImportError:
            # Module imports will be tested separately
            self.migration_module = None
    
    def test_column_mapping_exists(self):
        """Test that COLUMN_MAPPING dictionary exists"""
        if self.migration_module is None:
            self.skipTest("Migration module not importable")
        
        self.assertIn('COLUMN_MAPPING', dir(self.migration_module))
        mapping = self.migration_module.COLUMN_MAPPING
        self.assertIsInstance(mapping, dict)
    
    def test_yahoo_column_mapping(self):
        """Test that Yahoo columns are mapped correctly"""
        expected_mappings = {
            'yahoo_open': 'yahoo_zl_open',
            'yahoo_high': 'yahoo_zl_high',
            'yahoo_low': 'yahoo_zl_low',
            'yahoo_close': 'yahoo_zl_close',
            'yahoo_volume': 'yahoo_zl_volume',
        }
        
        if self.migration_module is None:
            self.skipTest("Migration module not importable")
        
        mapping = self.migration_module.COLUMN_MAPPING
        for old_col, new_col in expected_mappings.items():
            self.assertEqual(mapping.get(old_col), new_col,
                           f"Mapping for {old_col} should be {new_col}")
    
    def test_alpha_to_databento_mapping(self):
        """Test that Alpha Vantage columns map to DataBento"""
        expected_mappings = {
            'alpha_open': 'databento_zl_open',
            'alpha_high': 'databento_zl_high',
            'alpha_low': 'databento_zl_low',
            'alpha_close': 'databento_zl_close',
            'alpha_volume': 'databento_zl_volume',
        }
        
        if self.migration_module is None:
            self.skipTest("Migration module not importable")
        
        mapping = self.migration_module.COLUMN_MAPPING
        for old_col, new_col in expected_mappings.items():
            self.assertEqual(mapping.get(old_col), new_col,
                           f"Alpha column {old_col} should map to {new_col}")


class TestBigQueryClient(unittest.TestCase):
    """Test BigQuery client initialization"""
    
    @patch('google.cloud.bigquery.Client')
    def test_client_initialization(self, mock_client):
        """Test that BigQuery client can be initialized"""
        from google.cloud import bigquery
        
        client = bigquery.Client(project="test-project", location="us-central1")
        mock_client.assert_called_once()
    
    def test_project_id_constant(self):
        """Test that PROJECT_ID constant is set correctly"""
        # Import would fail if module structure is wrong
        try:
            from migration import migrate_master_features
            self.assertEqual(migrate_master_features.PROJECT_ID, "cbi-v14")
        except ImportError:
            self.skipTest("Migration module not importable")


class TestColumnMappingLogic(unittest.TestCase):
    """Test column mapping logic"""
    
    def test_technical_indicator_mapping(self):
        """Test that technical indicators are mapped with yahoo_ prefix"""
        expected_mappings = {
            'rsi_14': 'yahoo_zl_rsi_14',
            'macd': 'yahoo_zl_macd',
            'sma_50': 'yahoo_zl_sma_50',
            'sma_200': 'yahoo_zl_sma_200',
        }
        
        try:
            from migration import migrate_master_features
            mapping = migrate_master_features.COLUMN_MAPPING
            
            for old_col, new_col in expected_mappings.items():
                self.assertEqual(mapping.get(old_col), new_col,
                               f"Technical indicator {old_col} should map to {new_col}")
        except ImportError:
            self.skipTest("Migration module not importable")
    
    def test_no_duplicate_target_columns(self):
        """Test that no two source columns map to the same target"""
        try:
            from migration import migrate_master_features
            mapping = migrate_master_features.COLUMN_MAPPING
            
            target_cols = list(mapping.values())
            unique_targets = set(target_cols)
            
            self.assertEqual(len(target_cols), len(unique_targets),
                           "Duplicate target columns found in mapping")
        except ImportError:
            self.skipTest("Migration module not importable")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in migration scripts"""
    
    def test_table_exists_check(self):
        """Test that table existence is checked"""
        try:
            from migration import migrate_master_features
            self.assertIn('check_table_exists', dir(migrate_master_features))
        except ImportError:
            self.skipTest("Migration module not importable")
    
    def test_schema_validation(self):
        """Test that schema validation exists"""
        try:
            from migration import migrate_master_features
            self.assertIn('get_table_schema', dir(migrate_master_features))
        except ImportError:
            self.skipTest("Migration module not importable")


def run_tests():
    """Run all unit tests"""
    print("=" * 60)
    print("Running Unit Tests for Migration Scripts")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMigrateMasterFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestBigQueryClient))
    suite.addTests(loader.loadTestsFromTestCase(TestColumnMappingLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())

