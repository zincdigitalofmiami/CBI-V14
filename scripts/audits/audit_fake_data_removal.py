#!/usr/bin/env python3
"""
FAKE DATA REMOVAL AUDIT
Identify and remove all fake/placeholder data without disrupting existing views
"""

import os
import re
from pathlib import Path

class FakeDataAuditor:
    """Audit and remove fake data while preserving existing functionality"""
    
    def __init__(self):
        self.fake_patterns = [
            r'fake',
            r'mock', 
            r'demo',
            r'placeholder',
            r'simulated',
            r'dummy',
            r'hardcoded.*=.*\d+\.\d+',  # hardcoded numbers
            r'# Placeholder.*\d+',
            r'test.*=.*\d+',
            r'sample.*=.*\d+',
            r'example.*=.*\d+',
        ]
        
        # CRITICAL: Views that must NOT be disrupted
        self.protected_views = [
            'api.vw_ultimate_adaptive_signal',
            'api.vw_market_intelligence', 
            'models.vw_master_feature_set_v1',
            'models.zl_timesfm_training_v1',
            'models.zl_price_training_base',
            'models.zl_forecast_baseline_v1',
            'curated.vw_soybean_oil_quote',
            'curated.vw_biofuel_policy_us_daily',
            'signals.vw_weather_aggregates_daily',
            'signals.vw_master_signal_processor'
        ]
        
        self.fake_data_found = []
        self.files_to_fix = []
        
    def audit_file(self, filepath):
        """Audit a single file for fake data"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            fake_instances = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in self.fake_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip comments that are just explaining
                        if not (line.strip().startswith('#') and ('would be' in line.lower() or 'example' in line.lower())):
                            fake_instances.append({
                                'line_num': i,
                                'line': line.strip(),
                                'pattern': pattern,
                                'severity': self._classify_severity(line, pattern)
                            })
            
            if fake_instances:
                self.fake_data_found.append({
                    'file': str(filepath),
                    'instances': fake_instances
                })
                
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    def _classify_severity(self, line, pattern):
        """Classify severity of fake data"""
        # CRITICAL: Hardcoded numbers in calculations
        if re.search(r'=.*\d+\.\d+', line) and 'placeholder' in line.lower():
            return 'CRITICAL'
        
        # HIGH: Mock/fake data in production code
        if any(word in line.lower() for word in ['fake', 'mock', 'dummy']):
            return 'HIGH'
            
        # MEDIUM: Placeholder values
        if 'placeholder' in line.lower():
            return 'MEDIUM'
            
        # LOW: Test/demo code
        return 'LOW'
    
    def audit_directory(self, directory):
        """Audit all Python files in directory"""
        path = Path(directory)
        
        for py_file in path.rglob('*.py'):
            # Skip virtual environments and caches
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', '.git']):
                continue
                
            self.audit_file(py_file)
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("=" * 80)
        print("FAKE DATA REMOVAL AUDIT REPORT")
        print("=" * 80)
        
        if not self.fake_data_found:
            print("✅ NO FAKE DATA FOUND")
            return
        
        # Sort by severity
        critical_files = []
        high_files = []
        medium_files = []
        low_files = []
        
        for file_data in self.fake_data_found:
            max_severity = max(inst['severity'] for inst in file_data['instances'])
            
            if max_severity == 'CRITICAL':
                critical_files.append(file_data)
            elif max_severity == 'HIGH':
                high_files.append(file_data)
            elif max_severity == 'MEDIUM':
                medium_files.append(file_data)
            else:
                low_files.append(file_data)
        
        # Report critical issues first
        if critical_files:
            print("\n🚨 CRITICAL FAKE DATA (MUST FIX IMMEDIATELY):")
            for file_data in critical_files:
                print(f"\n📁 {file_data['file']}:")
                for inst in file_data['instances']:
                    if inst['severity'] == 'CRITICAL':
                        print(f"  Line {inst['line_num']}: {inst['line']}")
        
        if high_files:
            print("\n⚠️ HIGH PRIORITY FAKE DATA:")
            for file_data in high_files:
                print(f"\n📁 {file_data['file']}:")
                for inst in file_data['instances']:
                    if inst['severity'] == 'HIGH':
                        print(f"  Line {inst['line_num']}: {inst['line']}")
        
        if medium_files:
            print("\n🔶 MEDIUM PRIORITY PLACEHOLDER DATA:")
            for file_data in medium_files:
                print(f"\n📁 {file_data['file']}:")
                for inst in file_data['instances']:
                    if inst['severity'] == 'MEDIUM':
                        print(f"  Line {inst['line_num']}: {inst['line']}")
        
        # Summary
        total_files = len(self.fake_data_found)
        total_instances = sum(len(f['instances']) for f in self.fake_data_found)
        
        print(f"\n📊 SUMMARY:")
        print(f"  Files with fake data: {total_files}")
        print(f"  Total fake instances: {total_instances}")
        print(f"  Critical issues: {len(critical_files)}")
        print(f"  High priority: {len(high_files)}")
        
        print(f"\n🛡️ PROTECTED VIEWS (DO NOT MODIFY):")
        for view in self.protected_views:
            print(f"  ✅ {view}")
    
    def generate_fixes(self):
        """Generate specific fixes for fake data"""
        print("\n" + "=" * 80)
        print("RECOMMENDED FIXES")
        print("=" * 80)
        
        for file_data in self.fake_data_found:
            critical_instances = [i for i in file_data['instances'] if i['severity'] == 'CRITICAL']
            high_instances = [i for i in file_data['instances'] if i['severity'] == 'HIGH']
            
            if critical_instances or high_instances:
                print(f"\n📁 {file_data['file']}:")
                
                for inst in critical_instances + high_instances:
                    print(f"\n  ❌ Line {inst['line_num']}: {inst['line']}")
                    
                    # Suggest specific fixes
                    if 'zl_forecast_30d = current_zl * 1.02' in inst['line']:
                        print("  ✅ FIX: Use actual forecast from signals.vw_master_signal_processor")
                        print("      Replace with: zl_forecast_30d = get_signal_forecast(current_zl)")
                    
                    elif 'zl_crude_corr = 0.45' in inst['line']:
                        print("  ✅ FIX: Calculate real correlation from data")
                        print("      Replace with: zl_crude_corr = calculate_correlation('ZL', 'CL', days=30)")
                    
                    elif 'vix_norm = 1.1' in inst['line']:
                        print("  ✅ FIX: Use real VIX data from vix_daily table")
                        print("      Replace with: vix_norm = get_vix_normalized()")
                    
                    elif 'weather_z = 0.5' in inst['line']:
                        print("  ✅ FIX: Use actual weather data or mark as unavailable")
                        print("      Replace with: weather_z = get_weather_z_score() or None")
                    
                    elif 'np.random' in inst['line']:
                        print("  ✅ FIX: Replace with real data query")
                        print("      Use BigQuery to get actual signal values")
                    
                    elif "'win_rate': 68.5" in inst['line']:
                        print("  ✅ FIX: Calculate from backtesting results")
                        print("      Replace with: win_rate = calculate_historical_win_rate()")


if __name__ == "__main__":
    auditor = FakeDataAuditor()
    
    # Audit key directories
    directories_to_audit = [
        'forecast/',
        'cbi-v14-ingestion/',
        '.'  # Root directory Python files
    ]
    
    for directory in directories_to_audit:
        if os.path.exists(directory):
            print(f"🔍 Auditing {directory}...")
            auditor.audit_directory(directory)
    
    # Generate reports
    auditor.generate_report()
    auditor.generate_fixes()
    
    print("\n" + "=" * 80)
    print("⚠️ IMPORTANT: Do NOT modify any protected views without testing!")
    print("Always backup before making changes!")
    print("=" * 80)
