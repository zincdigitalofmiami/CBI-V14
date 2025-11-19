#!/usr/bin/env python3
"""
Execute BigQuery Schema Statements Individually
Handles multi-statement SQL files properly
"""

import re
import subprocess
import sys
from pathlib import Path

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
SCHEMA_FILE = "PRODUCTION_READY_BQ_SCHEMA.sql"

def parse_sql_file(file_path):
    """Parse SQL file into individual CREATE statements"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by CREATE statements
    statements = []
    current_stmt = []
    in_statement = False
    
    for line in content.split('\n'):
        if line.strip().startswith('CREATE OR REPLACE TABLE') or line.strip().startswith('CREATE OR REPLACE VIEW'):
            if current_stmt:
                statements.append('\n'.join(current_stmt))
            current_stmt = [line]
            in_statement = True
        elif in_statement:
            current_stmt.append(line)
            # Check if statement is complete (ends with );
            if line.strip().endswith(');'):
                statements.append('\n'.join(current_stmt))
                current_stmt = []
                in_statement = False
    
    # Add last statement if exists
    if current_stmt:
        statements.append('\n'.join(current_stmt))
    
    return statements

def execute_statement(statement):
    """Execute a single BigQuery statement"""
    # Extract table name for logging
    match = re.search(r'CREATE OR REPLACE (?:TABLE|VIEW)\s+(\S+)', statement)
    table_name = match.group(1) if match else "unknown"
    
    print(f"  Creating: {table_name}")
    
    # Write statement to temp file
    temp_file = "/tmp/bq_temp_statement.sql"
    with open(temp_file, 'w') as f:
        f.write(statement)
    
    # Execute
    cmd = [
        'bq', 'query',
        '--use_legacy_sql=false',
        f'--project_id={PROJECT_ID}',
        f'--location={LOCATION}'
    ]
    
    try:
        with open(temp_file, 'r') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode == 0:
            print(f"    ✓ Created {table_name}")
            return True
        else:
            print(f"    ❌ Failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"    ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Executing BigQuery Schema Statements")
    print("=" * 60)
    print()
    
    # Parse SQL file
    print(f"📋 Parsing {SCHEMA_FILE}...")
    statements = parse_sql_file(SCHEMA_FILE)
    print(f"   Found {len(statements)} CREATE statements")
    print()
    
    # Execute each statement
    success_count = 0
    failure_count = 0
    
    for i, statement in enumerate(statements, 1):
        if execute_statement(statement):
            success_count += 1
        else:
            failure_count += 1
    
    # Summary
    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total statements: {len(statements)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print()
    
    if failure_count == 0:
        print("✅ ALL STATEMENTS EXECUTED SUCCESSFULLY")
        return 0
    else:
        print(f"⚠️  {failure_count} STATEMENTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

