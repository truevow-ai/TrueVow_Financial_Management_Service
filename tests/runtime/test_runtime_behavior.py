"""
Runtime Behavior Test Suite
Tests actual API endpoints with real HTTP requests
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_api_endpoint(method, endpoint, params=None, data=None, expected_status=200):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            status = "✅ PASS" if response.status_code == expected_status else "❌ FAIL"
            print(f"\n{status} {method} {endpoint}")
            print(f"   Status: {response.status_code} (expected: {expected_status})")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list):
                    print(f"   Result: {len(result)} items returned")
                    if result:
                        print(f"   First item keys: {list(result[0].keys())[:5]}")
                elif isinstance(result, dict):
                    print(f"   Result: {json.dumps({k: v for k, v in list(result.items())[:5]}, indent=2)}")
            else:
                print(f"   Response: {response.text[:200]}")
            
            return response.status_code == expected_status
            
        except httpx.ConnectError as e:
            print(f"\n❌ FAIL {method} {endpoint}")
            print(f"   Error: Cannot connect to backend API at {BASE_URL}")
            print(f"   Is the server running?")
            return False
        except Exception as e:
            print(f"\n❌ FAIL {method} {endpoint}")
            print(f"   Error: {str(e)[:200]}")
            return False

async def run_runtime_tests():
    print("=" * 80)
    print("RUNTIME BEHAVIOR TEST SUITE")
    print("=" * 80)
    print("\nTesting actual API endpoints with HTTP requests...")
    print(f"Base URL: {BASE_URL}")
    
    results = []
    
    # AR Endpoints
    print("\n" + "=" * 80)
    print("TESTING AR (ACCOUNTS RECEIVABLE) ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET", 
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/ar/invoices",
        params={"limit": 10},
        expected_status=200
    ))
    
    # AP Endpoints
    print("\n" + "=" * 80)
    print("TESTING AP (ACCOUNTS PAYABLE) ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/ap/bills",
        params={"limit": 10},
        expected_status=200
    ))
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/ap/vendors",
        params={"limit": 10},
        expected_status=200
    ))
    
    # Treasury Endpoints
    print("\n" + "=" * 80)
    print("TESTING TREASURY ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/treasury/bank-accounts",
        params={"limit": 10},
        expected_status=200
    ))
    
    # Payroll Endpoints
    print("\n" + "=" * 80)
    print("TESTING PAYROLL ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/payroll/employees",
        params={"limit": 10},
        expected_status=200
    ))
    
    # GL Endpoints
    print("\n" + "=" * 80)
    print("TESTING GENERAL LEDGER ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/gl/accounts",
        params={"limit": 20},
        expected_status=200
    ))
    
    # Reporting Endpoints
    print("\n" + "=" * 80)
    print("TESTING REPORTING ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/reporting/trial-balance",
        params={
            "legal_entity_id": "17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c",
            "book_id": "17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c"
        },
        expected_status=200
    ))
    
    # Intercompany Endpoints
    print("\n" + "=" * 80)
    print("TESTING INTERCOMPANY ENDPOINTS")
    print("=" * 80)
    
    results.append(await test_api_endpoint(
        "GET",
        "/api/v1/intercompany/transfers",
        params={"limit": 10},
        expected_status=200
    ))
    
    # Summary
    print("\n" + "=" * 80)
    print("RUNTIME TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n✅ OVERALL: RUNTIME TESTS PASSED")
    elif success_rate >= 50:
        print("\n⚠️  OVERALL: PARTIAL SUCCESS - Some endpoints need attention")
    else:
        print("\n❌ OVERALL: RUNTIME TESTS FAILED - Backend server may not be running")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(run_runtime_tests())
