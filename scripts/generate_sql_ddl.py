#!/usr/bin/env python3
"""
Generate SQL DDL files from SQLAlchemy models for direct database execution

This script generates SQL CREATE TABLE statements that can be run directly
in the Financial Management database (Supabase SQL editor or psql).

Usage:
    python scripts/generate_sql_ddl.py [--output database/schema.sql]
"""

import sys
from pathlib import Path
from sqlalchemy.schema import CreateTable

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def generate_ddl():
    """Generate DDL from all models"""
    # Import models directly without loading settings
    import os
    # Set a dummy DATABASE_URL to avoid Settings validation errors
    os.environ.setdefault('DATABASE_URL', 'postgresql://dummy:dummy@localhost/dummy')
    os.environ.setdefault('JWT_SECRET_KEY', 'dummy-secret-key-for-ddl-generation')
    
    from app.core.database import Base
    from sqlalchemy import create_engine
    
    # Create a dummy engine just for DDL generation (we don't connect)
    # Use postgresql dialect for proper SQL syntax
    from sqlalchemy.dialects import postgresql
    engine = create_engine('postgresql://', strategy='mock', executor=lambda *args, **kwargs: None)
    
    ddl_statements = []
    ddl_statements.append("-- TrueVow Financial Management Service - Database Schema")
    ddl_statements.append("-- Generated SQL DDL for Financial Management Database")
    ddl_statements.append("-- Database: TrueVow_Financial_Management_Service")
    ddl_statements.append("-- Date: 2026-01-24")
    ddl_statements.append("")
    ddl_statements.append("-- Enable UUID extension if not already enabled")
    ddl_statements.append("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    ddl_statements.append("")
    ddl_statements.append("-- =====================================================")
    ddl_statements.append("-- TABLES")
    ddl_statements.append("-- =====================================================")
    ddl_statements.append("")
    
    # Generate DDL for each table
    for table in Base.metadata.sorted_tables:
        # Generate CREATE TABLE statement
        create_table = CreateTable(table).compile(dialect=postgresql.dialect())
        ddl_statements.append(f"-- Table: {table.name}")
        ddl_statements.append(str(create_table))
        ddl_statements.append("")
        
        # Generate indexes if any
        for index in table.indexes:
            create_index = index.compile(dialect=postgresql.dialect())
            ddl_statements.append(f"-- Index: {index.name}")
            ddl_statements.append(str(create_index))
            ddl_statements.append("")
    
    return "\n".join(ddl_statements)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SQL DDL from SQLAlchemy models')
    parser.add_argument('--output', '-o', 
                       default='infra/database/schema.sql',
                       help='Output file path (default: infra/database/schema.sql)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TrueVow FM Service - SQL DDL Generator")
    print("=" * 60)
    print()
    print("Generating SQL DDL from models...")
    
    try:
        ddl = generate_ddl()
        
        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ddl)
        
        print(f"SQL DDL generated successfully!")
        print(f"   Output: {output_path}")
        print()
        print("Next steps:")
        print("   1. Review the generated SQL file")
        print("   2. Connect to your Financial Management database")
        print("   3. Run the SQL file:")
        print(f"      psql <connection_string> -f {output_path}")
        print("   OR")
        print("   4. Copy and paste into Supabase SQL Editor")
        
        return 0
    except Exception as e:
        print(f"Error generating DDL: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
