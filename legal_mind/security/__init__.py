#!/usr/bin/env python3
"""
Security and Compliance Package for Legal Mind Agent

This package provides comprehensive security, compliance, and data protection
capabilities for the Legal Mind AI Agent, including:

- Azure Key Vault integration for secure secrets management
- Content safety filtering and PII protection
- Regional compliance and data residency controls
- Audit logging and compliance reporting

Usage:
    from legal_mind.security import (
        get_secure_config,
        get_compliance_coordinator,
        get_regional_compliance_manager
    )
    
    # Initialize security components
    config = get_secure_config()
    compliance = get_compliance_coordinator()
    regional = get_regional_compliance_manager()
"""

import logging
from typing import Optional

# Import main classes for easy access
from .key_vault import SecureConfig, get_secure_config
from .content_safety import (
    ContentSafetyFilter,
    PIIScrubber,
    ComplianceCoordinator,
    get_compliance_coordinator
)
from .regional_compliance import (
    RegionalComplianceManager,
    DataResidencyRegion,
    ComplianceJurisdiction,
    get_regional_compliance_manager
)

logger = logging.getLogger(__name__)

# Package version
__version__ = "1.0.0"

# Export main functionality
__all__ = [
    # Main manager functions
    "get_secure_config",
    "get_compliance_coordinator", 
    "get_regional_compliance_manager",
    
    # Core classes
    "SecureConfig",
    "ContentSafetyFilter",
    "PIIScrubber",
    "ComplianceCoordinator",
    "RegionalComplianceManager",
    
    # Enums
    "DataResidencyRegion",
    "ComplianceJurisdiction",
    
    # Utility functions
    "initialize_security_framework",
    "validate_deployment_security",
    "get_security_status"
]

# Global security framework state
_security_initialized = False

def initialize_security_framework(
    primary_region: DataResidencyRegion = DataResidencyRegion.US_EAST_2,
    enable_content_safety: bool = True,
    enable_key_vault: bool = True
) -> dict:
    """
    Initialize the complete security framework
    
    Args:
        primary_region: Primary data residency region
        enable_content_safety: Enable content safety filtering
        enable_key_vault: Enable Azure Key Vault integration
        
    Returns:
        Initialization status and configuration
    """
    global _security_initialized
    
    try:
        init_status = {
            "initialized": False,
            "components": {},
            "errors": [],
            "warnings": []
        }
        
        # Initialize secure configuration
        if enable_key_vault:
            try:
                config = get_secure_config()
                init_status["components"]["key_vault"] = {
                    "status": "initialized",
                    "vault_url": getattr(config, 'vault_url', 'not_configured'),
                    "managed_identity": getattr(config, 'use_managed_identity', False)
                }
                logger.info("Azure Key Vault integration initialized")
            except Exception as e:
                init_status["errors"].append(f"Key Vault initialization failed: {e}")
                init_status["components"]["key_vault"] = {"status": "failed", "error": str(e)}
        
        # Initialize content safety and compliance
        if enable_content_safety:
            try:
                compliance = get_compliance_coordinator()
                init_status["components"]["content_safety"] = {
                    "status": "initialized",
                    "content_safety_enabled": compliance.content_filter is not None,
                    "pii_scrubbing_enabled": compliance.pii_scrubber is not None
                }
                logger.info("Content safety and PII protection initialized")
            except Exception as e:
                init_status["errors"].append(f"Content safety initialization failed: {e}")
                init_status["components"]["content_safety"] = {"status": "failed", "error": str(e)}
        
        # Initialize regional compliance
        try:
            regional = get_regional_compliance_manager()
            regional.primary_region = primary_region
            init_status["components"]["regional_compliance"] = {
                "status": "initialized",
                "primary_region": primary_region.value,
                "applicable_jurisdictions": [
                    j.value for j in regional.region_jurisdictions.get(primary_region, [])
                ]
            }
            logger.info(f"Regional compliance initialized for {primary_region.value}")
        except Exception as e:
            init_status["errors"].append(f"Regional compliance initialization failed: {e}")
            init_status["components"]["regional_compliance"] = {"status": "failed", "error": str(e)}
        
        # Overall initialization status
        init_status["initialized"] = len(init_status["errors"]) == 0
        
        if init_status["initialized"]:
            _security_initialized = True
            logger.info("Security framework initialized successfully")
        else:
            logger.error(f"Security framework initialization failed: {init_status['errors']}")
        
        return init_status
        
    except Exception as e:
        logger.error(f"Critical error during security framework initialization: {e}")
        return {
            "initialized": False,
            "components": {},
            "errors": [f"Critical initialization error: {e}"],
            "warnings": []
        }

def validate_deployment_security(service_endpoints: dict) -> dict:
    """
    Validate security configuration for deployment
    
    Args:
        service_endpoints: Dictionary of service name -> endpoint URL mappings
        
    Returns:
        Security validation results
    """
    validation = {
        "overall_secure": True,
        "validations": {},
        "recommendations": [],
        "critical_issues": []
    }
    
    try:
        # Validate regional compliance
        regional = get_regional_compliance_manager()
        regional_validation = regional.validate_service_deployment(service_endpoints)
        validation["validations"]["regional_compliance"] = regional_validation
        
        if not regional_validation["compliant"]:
            validation["overall_secure"] = False
            validation["critical_issues"].extend(regional_validation["violations"])
            validation["recommendations"].extend(regional_validation["recommendations"])
        
        # Validate secure configuration
        try:
            config = get_secure_config()
            config_validation = {
                "key_vault_configured": hasattr(config, 'vault_url') and config.vault_url is not None,
                "managed_identity_enabled": getattr(config, 'use_managed_identity', False),
                "secrets_cached": len(getattr(config, '_cache', {})) > 0
            }
            validation["validations"]["secure_config"] = config_validation
            
            if not config_validation["key_vault_configured"]:
                validation["recommendations"].append("Configure Azure Key Vault for secrets management")
            
        except Exception as e:
            validation["validations"]["secure_config"] = {"error": str(e)}
            validation["recommendations"].append("Fix secure configuration issues")
        
        # Validate content safety
        try:
            compliance = get_compliance_coordinator()
            content_validation = {
                "content_safety_enabled": compliance.content_filter is not None,
                "pii_scrubbing_enabled": compliance.pii_scrubber is not None,
                "audit_logging_enabled": compliance.audit_logger is not None
            }
            validation["validations"]["content_safety"] = content_validation
            
            if not all(content_validation.values()):
                validation["recommendations"].append("Enable all content safety and PII protection features")
                
        except Exception as e:
            validation["validations"]["content_safety"] = {"error": str(e)}
            validation["recommendations"].append("Fix content safety configuration")
        
    except Exception as e:
        validation["overall_secure"] = False
        validation["critical_issues"].append(f"Security validation error: {e}")
    
    return validation

def get_security_status() -> dict:
    """
    Get current security framework status
    
    Returns:
        Current status of all security components
    """
    status = {
        "framework_initialized": _security_initialized,
        "timestamp": logging.Formatter().formatTime(),
        "components": {}
    }
    
    # Check secure config status
    try:
        config = get_secure_config()
        status["components"]["secure_config"] = {
            "available": True,
            "vault_configured": hasattr(config, 'vault_url') and config.vault_url is not None,
            "cached_secrets": len(getattr(config, '_cache', {}))
        }
    except Exception as e:
        status["components"]["secure_config"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check compliance coordinator status
    try:
        compliance = get_compliance_coordinator()
        status["components"]["compliance"] = {
            "available": True,
            "content_safety_active": compliance.content_filter is not None,
            "pii_scrubbing_active": compliance.pii_scrubber is not None
        }
    except Exception as e:
        status["components"]["compliance"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check regional compliance status
    try:
        regional = get_regional_compliance_manager()
        status["components"]["regional_compliance"] = {
            "available": True,
            "primary_region": regional.primary_region.value,
            "tracked_conversations": len(regional.conversation_storage_regions),
            "compliance_violations": len(regional.compliance_violations)
        }
    except Exception as e:
        status["components"]["regional_compliance"] = {
            "available": False,
            "error": str(e)
        }
    
    return status

# Initialize logging for security package
logging.getLogger(__name__).setLevel(logging.INFO)
