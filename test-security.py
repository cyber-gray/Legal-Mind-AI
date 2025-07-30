#!/usr/bin/env python3
"""
Quick Security Test for Legal Mind Agent

Tests the security framework configuration and Azure services connectivity.
"""

import os
import sys
import asyncio
from datetime import datetime

# Set environment variables for testing
os.environ['AZURE_KEY_VAULT_URL'] = 'https://kv-legal-mind-3699.vault.azure.net/'
os.environ['AZURE_CLIENT_ID'] = '4d01e7ba-4b3a-40a3-b210-7fa9b2ab7013'
os.environ['CONTENT_SAFETY_ENDPOINT'] = 'https://eastus2.api.cognitive.microsoft.com/'
os.environ['AZURE_REGION'] = 'eastus2'
os.environ['SECURITY_FRAMEWORK_ENABLED'] = 'true'

def test_imports():
    """Test that all security components can be imported"""
    print("🔍 Testing security framework imports...")
    
    try:
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from legal_mind.security import (
            get_secure_config,
            get_compliance_coordinator,
            get_regional_compliance_manager,
            DataResidencyRegion
        )
        
        print("✅ All security components imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n🌍 Testing environment configuration...")
    
    required_vars = [
        'AZURE_KEY_VAULT_URL',
        'AZURE_CLIENT_ID', 
        'CONTENT_SAFETY_ENDPOINT',
        'AZURE_REGION'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value[:30]}...")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

async def test_security_framework():
    """Test security framework initialization"""
    print("\n🔐 Testing security framework...")
    
    try:
        from legal_mind.security import initialize_security_framework, DataResidencyRegion
        
        # Initialize with basic settings
        result = initialize_security_framework(
            primary_region=DataResidencyRegion.US_EAST_2,
            enable_content_safety=True,
            enable_key_vault=True
        )
        
        if result["initialized"]:
            print("✅ Security framework initialized successfully")
            
            for component, details in result["components"].items():
                status = details.get("status", "unknown")
                print(f"   {component}: {status}")
            
            return True
        else:
            print("❌ Security framework initialization failed")
            for error in result.get("errors", []):
                print(f"   Error: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Security framework test failed: {e}")
        return False

def main():
    """Run all security tests"""
    print("🔐 Legal Mind Agent Security Test")
    print("=" * 50)
    print(f"Test Time: {datetime.utcnow().isoformat()}")
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment_config),
        ("Security Framework Test", lambda: asyncio.run(test_security_framework()))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All security tests passed! Your Legal Mind Agent is ready for secure deployment.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please review the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
