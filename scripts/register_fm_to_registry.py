#!/usr/bin/env python
"""
Register FM Service and all its modules with the Service Registry.

Run this script to publish FM capabilities to other microservices.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.service_registry import (
    init_service_registry,
    register_fm_modules,
    register_fm_integrations,
    get_registry_client,
    shutdown_service_registry,
)
from app.core.fm_registry_modules import FM_MODULES, FM_INTEGRATIONS


async def main():
    print("=" * 70)
    print("FM SERVICE REGISTRY REGISTRATION")
    print("=" * 70)
    
    try:
        # Step 1: Register service
        print("\n[1/3] Registering FM service with Service Registry...")
        await init_service_registry()
        print("      [OK] Service registered (fm_service on port 3011)")
        
        # Step 2: Register all modules
        print(f"\n[2/3] Registering {len(FM_MODULES)} FM modules...")
        await register_fm_modules()
        for module in FM_MODULES:
            print(f"      [OK] {module['module_name']}: {len(module['endpoints'])} endpoints")
        
        # Step 3: Register integrations
        print(f"\n[3/3] Registering {len(FM_INTEGRATIONS)} integrations...")
        await register_fm_integrations()
        for integration in FM_INTEGRATIONS:
            print(f"      [OK] {integration['target_service']}: {integration['purpose']}")
        
        # Verify registration
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        client = get_registry_client()
        
        # List services
        services = await client.list_services()
        print(f"\nRegistered services: {len(services)}")
        for svc in services:
            print(f"  - {svc.get('service_name', svc)}: {svc.get('url', 'N/A')}")
        
        # List FM modules
        modules = await client.get_modules()
        print(f"\nFM modules registered: {len(modules)}")
        
        print("\n" + "=" * 70)
        print("SUCCESS! FM service is now discoverable by other microservices.")
        print("=" * 70)
        print("\nOther services can now:")
        print("  - Discover FM via: GET http://localhost:3006/api/v1/registry/fm_service")
        print("  - Get FM modules:  GET http://localhost:3006/api/v1/registry/fm_service/modules")
        print("  - Find by event:   GET http://localhost:3006/api/v1/modules/by-event/journal_entry.posted")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await shutdown_service_registry()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
