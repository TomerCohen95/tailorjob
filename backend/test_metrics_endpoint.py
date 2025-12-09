#!/usr/bin/env python3
"""
Test script to verify /metrics endpoint is properly registered
"""
import sys
sys.path.insert(0, '.')

try:
    print("1. Importing FastAPI app...")
    from app.main import app
    
    print("2. Checking if setup_metrics was called...")
    from app.middleware.metrics import setup_metrics
    
    print("3. Listing all registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    
    print(f"\nFound {len(routes)} routes:")
    for route in sorted(set(routes)):
        print(f"  {route}")
    
    if '/metrics' in routes:
        print("\n✅ SUCCESS: /metrics endpoint IS registered!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: /metrics endpoint NOT found!")
        print("\nThis means setup_metrics() was not called or failed silently.")
        sys.exit(1)
        
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nThis means prometheus packages are not installed.")
    sys.exit(2)
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(3)