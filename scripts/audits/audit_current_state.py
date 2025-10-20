#!/usr/bin/env python3
"""
Comprehensive System Audit - CBI-V14
Following CURSOR_RULES: Check everything before making changes
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys
import os

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class SystemAuditor:
    """Methodical audit of current system state"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.audit_results = {}
        
    def audit_bigquery_tables(self):
        """Audit all BigQuery tables - check existence, size, data quality"""
        print("=== BIGQUERY TABLE AUDIT ===")
        
        # Get all tables
        tables = list(self.client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
        print(f"Found {len(tables)} tables in {DATASET_ID}")
        
        table_audit = {}
        
        for table in tables:
            table_name = table.table_id
            print(f"\nAuditing table: {table_name}")
            
            try:
                # Get basic stats
                if table.table_type == 'TABLE':
                    query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        COUNT(DISTINCT DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', CAST(time AS STRING)))) as unique_dates
                    FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
                    WHERE time IS NOT NULL
                    """
                    try:
                        result = self.client.query(query).to_dataframe()
                        if not result.empty:
                            table_audit[table_name] = {
                                'type': 'TABLE',
                                'rows': int(result.iloc[0]['row_count']),
                                'unique_dates': int(result.iloc[0]['unique_dates']),
                                'status': 'DATA_FOUND'
                            }
                        else:
                            table_audit[table_name] = {'type': 'TABLE', 'status': 'EMPTY'}
                    except:
                        # Try simpler query for tables without time column
                        simple_query = f"SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
                        try:
                            result = self.client.query(simple_query).to_dataframe()
                            table_audit[table_name] = {
                                'type': 'TABLE',
                                'rows': int(result.iloc[0]['row_count']),
                                'status': 'DATA_FOUND' if result.iloc[0]['row_count'] > 0 else 'EMPTY'
                            }
                        except Exception as e:
                            table_audit[table_name] = {'type': 'TABLE', 'status': f'ERROR: {str(e)[:100]}'}
                            
                elif table.table_type == 'VIEW':
                    # Test if view works
                    test_query = f"SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}` LIMIT 1"
                    try:
                        result = self.client.query(test_query).to_dataframe()
                        table_audit[table_name] = {
                            'type': 'VIEW',
                            'rows': int(result.iloc[0]['row_count']),
                            'status': 'WORKING'
                        }
                    except Exception as e:
                        table_audit[table_name] = {'type': 'VIEW', 'status': f'BROKEN: {str(e)[:100]}'}
                        
                print(f"  Status: {table_audit[table_name]['status']}")
                if 'rows' in table_audit[table_name]:
                    print(f"  Rows: {table_audit[table_name]['rows']}")
                    
            except Exception as e:
                table_audit[table_name] = {'status': f'AUDIT_ERROR: {str(e)}'}
                print(f"  AUDIT ERROR: {e}")
        
        self.audit_results['tables'] = table_audit
        return table_audit
        
    def audit_csv_files(self):
        """Audit CSV files in data directory"""
        print("\n=== CSV FILES AUDIT ===")
        
        csv_dir = "/Users/zincdigital/CBI-V14/data/csv"
        csv_audit = {}
        
        if os.path.exists(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            print(f"Found {len(csv_files)} CSV files")
            
            for csv_file in csv_files:
                file_path = os.path.join(csv_dir, csv_file)
                try:
                    # Quick check of file
                    df = pd.read_csv(file_path, nrows=5)  # Just first 5 rows
                    csv_audit[csv_file] = {
                        'columns': list(df.columns),
                        'sample_rows': len(df),
                        'file_size_mb': round(os.path.getsize(file_path) / (1024*1024), 2),
                        'status': 'READABLE'
                    }
                    print(f"  {csv_file}: {len(df.columns)} columns, {csv_audit[csv_file]['file_size_mb']} MB")
                except Exception as e:
                    csv_audit[csv_file] = {'status': f'ERROR: {str(e)[:100]}'}
                    print(f"  {csv_file}: ERROR - {e}")
        else:
            print("CSV directory not found")
            csv_audit = {'error': 'Directory not found'}
        
        self.audit_results['csv_files'] = csv_audit
        return csv_audit
        
    def audit_ingestion_scripts(self):
        """Audit ingestion scripts - check existence and basic syntax"""
        print("\n=== INGESTION SCRIPTS AUDIT ===")
        
        script_dir = "/Users/zincdigital/CBI-V14/cbi-v14-ingestion"
        script_audit = {}
        
        if os.path.exists(script_dir):
            python_files = [f for f in os.listdir(script_dir) if f.endswith('.py')]
            print(f"Found {len(python_files)} Python files")
            
            for script_file in python_files:
                file_path = os.path.join(script_dir, script_file)
                try:
                    # Check if file is executable and has main()
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    is_executable = os.access(file_path, os.X_OK)
                    has_main = 'if __name__ == "__main__"' in content
                    has_bigquery = 'bigquery' in content.lower()
                    
                    script_audit[script_file] = {
                        'executable': is_executable,
                        'has_main': has_main,
                        'uses_bigquery': has_bigquery,
                        'lines': len(content.split('\n')),
                        'status': 'READY' if is_executable and has_main else 'NOT_READY'
                    }
                    
                    print(f"  {script_file}: {script_audit[script_file]['status']} ({script_audit[script_file]['lines']} lines)")
                    
                except Exception as e:
                    script_audit[script_file] = {'status': f'ERROR: {str(e)[:100]}'}
                    print(f"  {script_file}: ERROR - {e}")
        else:
            print("Ingestion directory not found")
            script_audit = {'error': 'Directory not found'}
            
        self.audit_results['scripts'] = script_audit
        return script_audit
        
    def audit_forecast_service(self):
        """Test current forecast service status"""
        print("\n=== FORECAST SERVICE AUDIT ===")
        
        import requests
        
        service_audit = {}
        
        # Test local service
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            service_audit['local_health'] = {
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
                'status': 'WORKING' if response.status_code == 200 else 'UNHEALTHY'
            }
        except Exception as e:
            service_audit['local_health'] = {'status': f'NOT_RUNNING: {str(e)[:100]}'}
        
        # Test forecast endpoint
        if service_audit['local_health'].get('status') == 'WORKING':
            try:
                response = requests.post("http://localhost:8080/forecast/run", timeout=30)
                service_audit['forecast_endpoint'] = {
                    'status_code': response.status_code,
                    'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
                    'status': 'WORKING' if response.status_code == 200 else 'BROKEN'
                }
            except Exception as e:
                service_audit['forecast_endpoint'] = {'status': f'ERROR: {str(e)[:100]}'}
        
        self.audit_results['forecast_service'] = service_audit
        print(f"  Local health: {service_audit['local_health']['status']}")
        if 'forecast_endpoint' in service_audit:
            print(f"  Forecast endpoint: {service_audit['forecast_endpoint']['status']}")
            
        return service_audit
        
    def run_complete_audit(self):
        """Run comprehensive system audit"""
        print(f"CBI-V14 SYSTEM AUDIT - {datetime.now()}")
        print("=" * 60)
        
        # Audit all components
        self.audit_bigquery_tables()
        self.audit_csv_files()  
        self.audit_ingestion_scripts()
        self.audit_forecast_service()
        
        # Summary
        print("\n" + "=" * 60)
        print("AUDIT SUMMARY")
        print("=" * 60)
        
        # Tables summary
        tables = self.audit_results.get('tables', {})
        working_tables = sum(1 for t in tables.values() if t.get('status') in ['DATA_FOUND', 'WORKING'])
        total_rows = sum(t.get('rows', 0) for t in tables.values() if 'rows' in t)
        
        print(f"BigQuery Tables: {working_tables}/{len(tables)} working")
        print(f"Total Data Rows: {total_rows:,}")
        
        # Scripts summary  
        scripts = self.audit_results.get('scripts', {})
        ready_scripts = sum(1 for s in scripts.values() if s.get('status') == 'READY')
        
        print(f"Ingestion Scripts: {ready_scripts}/{len(scripts)} ready")
        
        # Service summary
        service = self.audit_results.get('forecast_service', {})
        service_status = service.get('local_health', {}).get('status', 'UNKNOWN')
        
        print(f"Forecast Service: {service_status}")
        
        # Overall health
        overall_health = "EXCELLENT" if working_tables > 10 and ready_scripts > 5 and "WORKING" in service_status else "NEEDS_WORK"
        print(f"Overall System Health: {overall_health}")
        
        return self.audit_results

if __name__ == "__main__":
    auditor = SystemAuditor()
    results = auditor.run_complete_audit()






