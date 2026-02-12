#!/usr/bin/env python3
"""
Export OpenAPI JSON schema from FastAPI application

Usage:
    python scripts/export_openapi.py [--output docs/01-main/openapi_export.json]
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def export_openapi():
    """Export OpenAPI schema from FastAPI app"""
    # Set dummy environment variables to avoid Settings validation errors
    import os
    os.environ.setdefault('DATABASE_URL', 'postgresql://dummy:dummy@localhost/dummy')
    os.environ.setdefault('JWT_SECRET_KEY', 'dummy-secret-key-for-openapi-export')
    
    # Import app after setting env vars
    from app.main import app
    
    # Get OpenAPI schema
    openapi_schema = app.openapi()
    
    return openapi_schema

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export OpenAPI JSON schema from FastAPI app')
    parser.add_argument('--output', '-o',
                       default='docs/01-main/openapi_export.json',
                       help='Output file path (default: docs/01-main/openapi_export.json)')
    
    args = parser.parse_args()
    
    print("Exporting OpenAPI schema...")
    
    try:
        schema = export_openapi()
        
        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        
        # Count routes
        paths = schema.get('paths', {})
        fm_routes = [p for p in paths.keys() if '/api/v1/books/' in p or '/api/v1/fm/' in p]
        treasury_routes = [p for p in paths.keys() if '/treasury/' in p]
        
        print(f"OpenAPI schema exported successfully!")
        print(f"   Output: {output_path}")
        print(f"   Total paths: {len(paths)}")
        print(f"   FM routes (books/*): {len(fm_routes)}")
        print(f"   Treasury routes (treasury/*): {len(treasury_routes)}")
        
        return 0
    except Exception as e:
        print(f"Error exporting OpenAPI schema: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
