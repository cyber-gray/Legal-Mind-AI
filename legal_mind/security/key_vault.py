#!/usr/bin/env python3
"""
Azure Key Vault Configuration for Legal Mind Agent

Manages secure secrets retrieval using Azure Key Vault and Managed Identity,
eliminating the need for environment variables or .env files in production.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import os
import json

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.core.exceptions import AzureError
    AZURE_KEYVAULT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Azure Key Vault SDK not available: {e}")
    AZURE_KEYVAULT_AVAILABLE = False
    # Mock classes for development
    class SecretClient: pass
    class DefaultAzureCredential: pass
    class ManagedIdentityCredential: pass
    class AzureError(Exception): pass

logger = logging.getLogger(__name__)

class SecureConfig:
    """
    Secure configuration management using Azure Key Vault
    
    Features:
    - Managed Identity authentication (no secrets in code)
    - Automatic secret caching with TTL
    - Fallback to environment variables for local development
    - Regional compliance with data residency controls
    """
    
    def __init__(self, key_vault_url: Optional[str] = None, use_managed_identity: bool = True):
        """
        Initialize secure configuration
        
        Args:
            key_vault_url: Azure Key Vault URL (e.g., https://your-vault.vault.azure.net/)
            use_managed_identity: Use Managed Identity for authentication
        """
        self.key_vault_url = key_vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self.use_managed_identity = use_managed_identity
        self.secret_client = None
        self.secret_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_minutes = 30  # Cache secrets for 30 minutes
        
        # Regional compliance settings
        self.required_region = "eastus2"  # Enforce East US 2 for compliance
        self.data_residency_enforced = True
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure Key Vault client with Managed Identity"""
        if not AZURE_KEYVAULT_AVAILABLE or not self.key_vault_url:
            logger.warning("Azure Key Vault not available - using environment variables")
            return
        
        try:
            if self.use_managed_identity:
                # Use Managed Identity in production (Azure App Service, Container Apps)
                credential = ManagedIdentityCredential()
                logger.info("Using Managed Identity for Key Vault authentication")
            else:
                # Use Default Azure Credential for development
                credential = DefaultAzureCredential()
                logger.info("Using Default Azure Credential for Key Vault authentication")
            
            self.secret_client = SecretClient(
                vault_url=self.key_vault_url,
                credential=credential
            )
            
            # Test connection
            self._test_connection()
            logger.info(f"Successfully connected to Key Vault: {self.key_vault_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            self.secret_client = None
    
    def _test_connection(self) -> None:
        """Test Key Vault connectivity"""
        if self.secret_client:
            try:
                # Try to list secrets (minimal permission test)
                list(self.secret_client.list_properties_of_secrets())
                logger.debug("Key Vault connection test successful")
            except Exception as e:
                logger.warning(f"Key Vault connection test failed: {e}")
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret from Key Vault with caching and fallback
        
        Args:
            secret_name: Name of the secret in Key Vault
            fallback_env_var: Environment variable name for local development fallback
            
        Returns:
            Secret value or None if not found
        """
        # Check cache first
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret
        
        # Try Key Vault
        if self.secret_client:
            try:
                secret = self.secret_client.get_secret(secret_name)
                secret_value = secret.value
                
                # Cache the secret
                self._cache_secret(secret_name, secret_value)
                
                logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return secret_value
                
            except AzureError as e:
                logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.info(f"Using environment variable '{fallback_env_var}' for '{secret_name}'")
                return env_value
        
        logger.error(f"Secret '{secret_name}' not found in Key Vault or environment")
        return None
    
    def _get_cached_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from cache if not expired"""
        if secret_name in self.secret_cache:
            cache_entry = self.secret_cache[secret_name]
            expiry_time = cache_entry["expiry"]
            
            if datetime.utcnow() < expiry_time:
                logger.debug(f"Using cached secret '{secret_name}'")
                return cache_entry["value"]
            else:
                # Remove expired cache entry
                del self.secret_cache[secret_name]
        
        return None
    
    def _cache_secret(self, secret_name: str, secret_value: str) -> None:
        """Cache secret with TTL"""
        expiry_time = datetime.utcnow() + timedelta(minutes=self.cache_ttl_minutes)
        self.secret_cache[secret_name] = {
            "value": secret_value,
            "expiry": expiry_time
        }
    
    def get_bot_credentials(self) -> Dict[str, str]:
        """Get Bot Framework credentials"""
        return {
            "app_id": self.get_secret("microsoft-app-id", "MicrosoftAppId") or "",
            "app_password": self.get_secret("microsoft-app-password", "MicrosoftAppPassword") or "",
            "app_type": self.get_secret("microsoft-app-type", "MicrosoftAppType") or "MultiTenant",
            "app_tenant_id": self.get_secret("microsoft-app-tenant-id", "MicrosoftAppTenantId") or ""
        }
    
    def get_azure_ai_credentials(self) -> Dict[str, str]:
        """Get Azure AI services credentials"""
        return {
            "agents_endpoint": self.get_secret("azure-ai-agents-endpoint", "AZURE_AI_AGENTS_ENDPOINT") or "",
            "agents_key": self.get_secret("azure-ai-agents-key", "AZURE_AI_AGENTS_KEY") or "",
            "openai_endpoint": self.get_secret("azure-openai-endpoint", "AZURE_OPENAI_ENDPOINT") or "",
            "openai_key": self.get_secret("azure-openai-key", "AZURE_OPENAI_API_KEY") or "",
            "search_endpoint": self.get_secret("azure-search-endpoint", "AZURE_SEARCH_ENDPOINT") or "",
            "search_key": self.get_secret("azure-search-key", "AZURE_SEARCH_KEY") or ""
        }
    
    def validate_regional_compliance(self) -> Dict[str, bool]:
        """
        Validate regional compliance for data residency
        
        Returns:
            Dictionary with compliance status for each service
        """
        compliance_status = {}
        credentials = self.get_azure_ai_credentials()
        
        # Check each Azure service endpoint for regional compliance
        services_to_check = {
            "azure_ai_agents": credentials["agents_endpoint"],
            "azure_openai": credentials["openai_endpoint"], 
            "azure_search": credentials["search_endpoint"]
        }
        
        for service_name, endpoint in services_to_check.items():
            if endpoint:
                # Extract region from endpoint URL
                region_compliant = self._check_endpoint_region(endpoint)
                compliance_status[service_name] = region_compliant
                
                if not region_compliant:
                    logger.warning(f"Service {service_name} endpoint not in required region {self.required_region}")
            else:
                compliance_status[service_name] = False
                logger.warning(f"Service {service_name} endpoint not configured")
        
        return compliance_status
    
    def _check_endpoint_region(self, endpoint: str) -> bool:
        """Check if endpoint is in the required region"""
        if not self.data_residency_enforced:
            return True
        
        # Extract region from Azure endpoint URL
        # Format: https://service-name.region.azure.com or https://service-name.region.openai.azure.com
        try:
            parts = endpoint.lower().split('.')
            for part in parts:
                if self.required_region in part:
                    return True
            
            # Additional check for eastus2 variants
            if self.required_region == "eastus2":
                return any("eastus2" in part or "east-us-2" in part for part in parts)
            
        except Exception as e:
            logger.error(f"Error parsing endpoint region from {endpoint}: {e}")
        
        return False
    
    def get_content_safety_config(self) -> Dict[str, Any]:
        """Get content safety and PII filtering configuration"""
        return {
            "enable_content_filters": True,
            "content_filter_level": "strict",
            "enable_pii_detection": True,
            "pii_scrub_mode": "replace",  # replace, redact, or remove
            "allowed_content_categories": [
                "educational", "research", "legal_guidance"
            ],
            "blocked_content_categories": [
                "specific_legal_advice", "privileged_information"
            ]
        }
    
    def clear_cache(self) -> None:
        """Clear all cached secrets"""
        self.secret_cache.clear()
        logger.info("Secret cache cleared")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for health checks"""
        bot_creds = self.get_bot_credentials()
        ai_creds = self.get_azure_ai_credentials()
        compliance_status = self.validate_regional_compliance()
        
        return {
            "key_vault_configured": self.secret_client is not None,
            "key_vault_url": self.key_vault_url,
            "managed_identity_enabled": self.use_managed_identity,
            "cached_secrets_count": len(self.secret_cache),
            "bot_credentials_configured": bool(bot_creds["app_id"] and bot_creds["app_password"]),
            "azure_ai_configured": bool(ai_creds["agents_endpoint"] and ai_creds["agents_key"]),
            "regional_compliance": compliance_status,
            "data_residency_enforced": self.data_residency_enforced,
            "required_region": self.required_region,
            "content_safety_enabled": self.get_content_safety_config()["enable_content_filters"]
        }

# Global configuration instance
_secure_config: Optional[SecureConfig] = None

def get_secure_config() -> SecureConfig:
    """Get the global secure configuration instance"""
    global _secure_config
    if _secure_config is None:
        # Initialize with production settings
        key_vault_url = os.getenv("AZURE_KEY_VAULT_URL", "https://legal-mind-vault.vault.azure.net/")
        _secure_config = SecureConfig(key_vault_url=key_vault_url, use_managed_identity=True)
    return _secure_config
