#!/usr/bin/env python3
"""
Comprehensive Reverse Engineering Audit
Maps all data connections, dependencies, and data flow paths
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ConnectionAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.connections = defaultdict(list)
        self.tables = set()
        self.models = set()
        self.views = set()
        self.datasets = set()
        self.scripts = []
        self.sql_files = []
        
    def find_all_references(self):
        """Find all BigQuery table/model/view references"""
        print("🔍 Scanning for BigQuery references...")
        
        # Scan SQL files
        sql_dir = self.project_root / "bigquery_sql"
        if sql_dir.exists():
            for sql_file in sql_dir.rglob("*.sql"):
                self.sql_files.append(sql_file)
                self.analyze_sql_file(sql_file)
        
        # Scan Python scripts
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                self.scripts.append(py_file)
                self.analyze_python_file(py_file)
    
    def analyze_sql_file(self, file_path: Path):
        """Extract all references from SQL file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract table references: `project.dataset.table`
            table_pattern = r'`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`'
            for match in re.finditer(table_pattern, content):
                project, dataset, table = match.groups()
                ref = f"{project}.{dataset}.{table}"
                self.tables.add(ref)
                self.datasets.add(f"{project}.{dataset}")
                self.connections[ref].append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'type': 'SQL',
                    'context': self.get_context(content, match.start())
                })
            
            # Extract model references: MODEL `project.dataset.model`
            model_pattern = r'MODEL\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`'
            for match in re.finditer(model_pattern, content, re.IGNORECASE):
                project, dataset, model = match.groups()
                ref = f"{project}.{dataset}.{model}"
                self.models.add(ref)
                self.connections[ref].append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'type': 'SQL_MODEL',
                    'context': self.get_context(content, match.start())
                })
            
            # Extract view references: FROM/JOIN views
            view_pattern = r'(FROM|JOIN)\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`'
            for match in re.finditer(view_pattern, content, re.IGNORECASE):
                op, project, dataset, view = match.groups()
                ref = f"{project}.{dataset}.{view}"
                if view.startswith('vw_'):
                    self.views.add(ref)
                    self.connections[ref].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'type': f'SQL_{op}',
                        'context': self.get_context(content, match.start())
                    })
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def analyze_python_file(self, file_path: Path):
        """Extract BigQuery references from Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract table references in Python strings
            table_pattern = r'["\']([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)["\']'
            for match in re.finditer(table_pattern, content):
                project, dataset, table = match.groups()
                ref = f"{project}.{dataset}.{table}"
                self.tables.add(ref)
                self.connections[ref].append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'type': 'PYTHON',
                    'context': self.get_context(content, match.start())
                })
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def get_context(self, content: str, pos: int, window: int = 50) -> str:
        """Get context around a position"""
        start = max(0, pos - window)
        end = min(len(content), pos + window)
        snippet = content[start:end].replace('\n', ' ')
        return snippet.strip()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive audit report"""
        report = {
            'summary': {
                'total_tables': len(self.tables),
                'total_models': len(self.models),
                'total_views': len(self.views),
                'total_datasets': len(self.datasets),
                'sql_files_analyzed': len(self.sql_files),
                'python_files_analyzed': len(self.scripts)
            },
            'datasets': sorted(list(self.datasets)),
            'tables': {
                table: self.connections.get(table, [])
                for table in sorted(self.tables)
            },
            'models': {
                model: self.connections.get(model, [])
                for model in sorted(self.models)
            },
            'views': {
                view: self.connections.get(view, [])
                for view in sorted(self.views)
            },
            'data_flow': self.trace_data_flow(),
            'critical_paths': self.identify_critical_paths()
        }
        return report
    
    def trace_data_flow(self) -> Dict:
        """Trace data flow paths"""
        flows = {}
        
        # Training data flow
        training_table = "cbi-v14.models_v4.training_dataset_super_enriched"
        if training_table in self.tables:
            flows['training'] = {
                'source': training_table,
                'consumers': [
                    ref for ref in self.connections[training_table]
                    if ref['type'] == 'SQL'
                ]
            }
        
        # Model flow
        model_flows = {}
        for model in self.models:
            consumers = []
            for table, refs in self.connections.items():
                for ref in refs:
                    if 'MODEL' in ref['context'].upper() and model in ref['context']:
                        consumers.append(table)
            model_flows[model] = consumers
        
        flows['models'] = model_flows
        
        # Forecast flow
        forecast_table = "cbi-v14.predictions_uc1.production_forecasts"
        if forecast_table in self.tables:
            flows['forecasts'] = {
                'source': forecast_table,
                'consumers': [
                    ref for ref in self.connections[forecast_table]
                ]
            }
        
        return flows
    
    def identify_critical_paths(self) -> List[Dict]:
        """Identify critical dependency paths"""
        critical = []
        
        # Path 1: Training → Models → Forecasts
        training = "cbi-v14.models_v4.training_dataset_super_enriched"
        models = [m for m in self.models if 'bqml' in m.lower()]
        forecasts = "cbi-v14.predictions_uc1.production_forecasts"
        
        if training in self.tables and forecasts in self.tables:
            critical.append({
                'path': 'Training → Models → Forecasts',
                'components': [
                    {'type': 'table', 'name': training},
                    {'type': 'models', 'names': models},
                    {'type': 'table', 'name': forecasts}
                ],
                'status': 'CRITICAL'
            })
        
        # Path 2: Big8 Signal → Forecasts
        big8_view = "cbi-v14.api.vw_big8_composite_signal"
        if big8_view in self.views:
            critical.append({
                'path': 'Big8 Signal → Forecasts',
                'components': [
                    {'type': 'view', 'name': big8_view},
                    {'type': 'table', 'name': forecasts}
                ],
                'status': 'CRITICAL'
            })
        
        return critical
    
    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE CONNECTION AUDIT REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        summary = report['summary']
        print(f"  Tables: {summary['total_tables']}")
        print(f"  Models: {summary['total_models']}")
        print(f"  Views: {summary['total_views']}")
        print(f"  Datasets: {summary['total_datasets']}")
        print(f"  SQL Files: {summary['sql_files_analyzed']}")
        print(f"  Python Files: {summary['python_files_analyzed']}")
        
        print(f"\n📁 DATASETS:")
        for dataset in report['datasets']:
            print(f"  - {dataset}")
        
        print(f"\n🔗 CRITICAL PATHS:")
        for path in report['critical_paths']:
            print(f"\n  {path['path']} ({path['status']}):")
            for comp in path['components']:
                if comp['type'] == 'models':
                    for model in comp['names']:
                        print(f"    → {comp['type']}: {model}")
                else:
                    print(f"    → {comp['type']}: {comp['name']}")
        
        print(f"\n📋 TOP TABLES (by reference count):")
        table_counts = {
            table: len(refs)
            for table, refs in report['tables'].items()
        }
        for table, count in sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {table}: {count} references")
        
        print(f"\n🤖 MODELS:")
        for model in report['models']:
            refs = report['models'][model]
            print(f"  {model}: {len(refs)} references")
            for ref in refs[:3]:  # Show first 3
                print(f"    - {ref['file']} ({ref['type']})")
        
        print(f"\n👁️  VIEWS:")
        for view in report['views']:
            refs = report['views'][view]
            print(f"  {view}: {len(refs)} references")


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auditor = ConnectionAuditor(project_root)
    
    print("🚀 Starting Comprehensive Connection Audit...")
    auditor.find_all_references()
    
    report = auditor.generate_report()
    auditor.print_report(report)
    
    # Save JSON report
    report_path = Path(project_root) / "docs" / "data-datasets" / "connection_audit_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Full report saved to: {report_path}")
    print("\n✅ Audit complete!")


if __name__ == "__main__":
    main()

