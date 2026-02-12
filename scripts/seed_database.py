#!/usr/bin/env python3
"""
Script to seed database with initial data

Usage:
    python scripts/seed_database.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env.local before importing app modules
from dotenv import load_dotenv
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.local")

# Set dummy JWT_SECRET_KEY if not present (for seed script only)
if "JWT_SECRET_KEY" not in os.environ:
    os.environ["JWT_SECRET_KEY"] = "dummy-secret-key-for-seeding-only"

from app.core.seed.commands import seed_database
from app.core.logging import logger


async def main():
    """Main function"""
    import argparse
    parser = argparse.ArgumentParser(description="Seed database with initial data")
    parser.add_argument("--step", type=str, help="Run specific step: legal_entity, book, dimension, period")
    args = parser.parse_args()
    
    print("=" * 60)
    print("TrueVow FM Service - Database Seeding")
    print("=" * 60)
    print()
    
    seed_file = "app/core/seed/seed_data.yaml"
    
    try:
        if args.step:
            print(f"[INFO] Running step: {args.step}")
        else:
            print(f"[INFO] Loading seed data from {seed_file}...")
        await seed_database(seed_file=seed_file, user_id=None, step=args.step)
        print("\n[SUCCESS] Database seeding completed successfully!")
        if not args.step:
            print("\nSeeded data:")
            print("  - Legal entities (UAE, Nevis, Pakistan)")
            print("  - Books (ACCRUAL and CASH per entity)")
            print("  - Dimensions (COST_CENTER, DEPARTMENT, LOCATION, etc.)")
            print("  - Dimension values")
    except Exception as e:
        print(f"\n[ERROR] Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
