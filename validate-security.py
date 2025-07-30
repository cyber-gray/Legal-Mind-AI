#!/usr/bin/env python3
"""
Security Validation Script for Legal Mind Agent

Validates the security and compliance configuration of the deployed application.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from legal_mind.security import (
        initialize_security_framework,
        validate_deployment_security,
        get_security_status,
        DataResidencyRegion
    )
    SECURITY_AVAILABLE = True
except ImportError as e:
    print(f"❌ Security framework not available: {e}")
    SECURITY_AVAILABLE = False

async def validate_security_configuration() -> Dict[str, Any]:
    """Run comprehensive security validation"""
    
    validation_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "unknown",
        "validations": {},
        "recommendations": [],
        "critical_issues": []
    }
    
    if not SECURITY_AVAILABLE:
        validation_results["overall_status"] = "failed"
        validation_results["critical_issues"].append("Security framework not available")
        return validation_results
    
    try:
        print("🔍 Running security validation...")
        
        # Initialize security framework
        print("  Initializing security framework...")
        region = DataResidencyRegion.US_EAST_2  # Default region
        
        init_result = initialize_security_framework(
            primary_region=region,
            enable_content_safety=True,
            enable_key_vault=True
        )
        
        validation_results["validations"]["framework_initialization"] = init_result
        
        if not init_result["initialized"]:
            validation_results["critical_issues"].extend(init_result["errors"])
        
        # Get security status
        print("  Checking security component status...")
        security_status = get_security_status()
        validation_results["validations"]["security_status"] = security_status
        
        # Validate deployment security
        print("  Validating deployment security...")
        service_endpoints = {
            "app_service": os.environ.get("WEBSITE_HOSTNAME", "localhost:8000"),
            "azure_openai": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            "key_vault": os.environ.get("AZURE_KEY_VAULT_URL", ""),
            "content_safety": os.environ.get("CONTENT_SAFETY_ENDPOINT", "")
        }
        
        deployment_validation = validate_deployment_security(service_endpoints)
        validation_results["validations"]["deployment_security"] = deployment_validation
        
        if not deployment_validation["overall_secure"]:
            validation_results["critical_issues"].extend(deployment_validation["critical_issues"])
            validation_results["recommendations"].extend(deployment_validation["recommendations"])
        
        # Environment variable validation
        print("  Validating environment configuration...")
        env_validation = validate_environment_variables()
        validation_results["validations"]["environment"] = env_validation
        
        if env_validation["missing_critical"]:
            validation_results["critical_issues"].extend([
                f"Missing critical environment variable: {var}" 
                for var in env_validation["missing_critical"]
            ])
        
        # Determine overall status
        if validation_results["critical_issues"]:
            validation_results["overall_status"] = "failed"
        elif validation_results["recommendations"]:
            validation_results["overall_status"] = "warning"
        else:
            validation_results["overall_status"] = "passed"
        
        print(f"✅ Security validation complete: {validation_results['overall_status']}")
        
    except Exception as e:
        validation_results["overall_status"] = "error"
        validation_results["critical_issues"].append(f"Validation error: {e}")
        print(f"❌ Security validation error: {e}")
    
    return validation_results

def validate_environment_variables() -> Dict[str, Any]:
    """Validate required environment variables"""
    
    # Critical variables for security
    critical_vars = [
        "AZURE_KEY_VAULT_URL",
        "AZURE_CLIENT_ID",
        "CONTENT_SAFETY_ENDPOINT"
    ]
    
    # Important variables for functionality
    important_vars = [
        "MICROSOFT_APP_ID",
        "MICROSOFT_APP_PASSWORD",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_REGION"
    ]
    
    # Optional variables
    optional_vars = [
        "WEBSITE_HOSTNAME",
        "PORT"
    ]
    
    validation = {
        "critical_set": [],
        "critical_missing": [],
        "important_set": [],
        "important_missing": [],
        "optional_set": [],
        "missing_critical": []
    }
    
    # Check critical variables
    for var in critical_vars:
        if os.environ.get(var):
            validation["critical_set"].append(var)
        else:
            validation["critical_missing"].append(var)
            validation["missing_critical"].append(var)
    
    # Check important variables
    for var in important_vars:
        if os.environ.get(var):
            validation["important_set"].append(var)
        else:
            validation["important_missing"].append(var)
    
    # Check optional variables
    for var in optional_vars:
        if os.environ.get(var):
            validation["optional_set"].append(var)
    
    return validation

def print_validation_report(validation_results: Dict[str, Any]):
    """Print formatted validation report"""
    
    status = validation_results["overall_status"]
    
    print("\n" + "="*60)
    print("🔐 LEGAL MIND AGENT SECURITY VALIDATION REPORT")
    print("="*60)
    
    # Overall status
    status_emoji = {
        "passed": "✅",
        "warning": "⚠️",
        "failed": "❌",
        "error": "💥",
        "unknown": "❓"
    }
    
    print(f"\n📊 Overall Status: {status_emoji.get(status, '❓')} {status.upper()}")
    print(f"🕐 Validation Time: {validation_results['timestamp']}")
    
    # Critical issues
    if validation_results["critical_issues"]:
        print(f"\n🚨 Critical Issues ({len(validation_results['critical_issues'])}):")
        for issue in validation_results["critical_issues"]:
            print(f"   ❌ {issue}")
    
    # Recommendations
    if validation_results["recommendations"]:
        print(f"\n💡 Recommendations ({len(validation_results['recommendations'])}):")
        for rec in validation_results["recommendations"]:
            print(f"   💡 {rec}")
    
    # Component status
    print(f"\n🔧 Component Status:")
    
    if "security_status" in validation_results["validations"]:
        security_status = validation_results["validations"]["security_status"]
        
        print(f"   Framework: {'✅' if security_status['framework_initialized'] else '❌'}")
        
        for component, details in security_status.get("components", {}).items():
            available = details.get("available", False)
            print(f"   {component.replace('_', ' ').title()}: {'✅' if available else '❌'}")
            
            if not available and "error" in details:
                print(f"     Error: {details['error']}")
    
    # Environment validation
    if "environment" in validation_results["validations"]:
        env_validation = validation_results["validations"]["environment"]
        
        print(f"\n🌍 Environment Configuration:")
        print(f"   Critical vars set: {len(env_validation['critical_set'])}/{len(env_validation['critical_set']) + len(env_validation['critical_missing'])}")
        print(f"   Important vars set: {len(env_validation['important_set'])}/{len(env_validation['important_set']) + len(env_validation['important_missing'])}")
        
        if env_validation["critical_missing"]:
            print(f"   Missing critical: {', '.join(env_validation['critical_missing'])}")
    
    # Deployment security
    if "deployment_security" in validation_results["validations"]:
        deployment = validation_results["validations"]["deployment_security"]
        
        print(f"\n🌐 Deployment Security:")
        print(f"   Overall secure: {'✅' if deployment['overall_secure'] else '❌'}")
        
        for service, details in deployment.get("validations", {}).get("services", {}).items():
            compliant = details.get("compliant", False)
            print(f"   {service}: {'✅' if compliant else '❌'}")
    
    print("\n" + "="*60)
    
    # Next steps
    if status == "failed":
        print("🔧 REQUIRED ACTIONS:")
        print("   1. Run ./deploy-security.sh to set up security infrastructure")
        print("   2. Configure missing environment variables")
        print("   3. Re-run validation")
    elif status == "warning":
        print("🔧 RECOMMENDED ACTIONS:")
        print("   1. Review and address recommendations above")
        print("   2. Consider additional security hardening")
    else:
        print("🎉 SECURITY CONFIGURATION COMPLETE!")
        print("   Your Legal Mind Agent is ready for production deployment.")
    
    print("\n📋 Full report saved to: security-validation-report.json")

async def main():
    """Main validation routine"""
    
    print("🔐 Legal Mind Agent Security Validation")
    print("="*50)
    
    # Run validation
    validation_results = await validate_security_configuration()
    
    # Save detailed report
    with open("security-validation-report.json", "w") as f:
        json.dump(validation_results, f, indent=2)
    
    # Print summary report
    print_validation_report(validation_results)
    
    # Exit with appropriate code
    if validation_results["overall_status"] == "failed":
        sys.exit(1)
    elif validation_results["overall_status"] == "warning":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
