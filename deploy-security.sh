#!/bin/bash

# Security Infrastructure Deployment Script for Legal Mind Agent
# Creates Azure Key Vault, Content Safety, and configures Managed Identity

set -e  # Exit on any error

# Configuration
RESOURCE_GROUP="rg-grayspace004-1361"
LOCATION="eastus2"
KEY_VAULT_NAME="kv-legal-mind-$(date +%s | tail -c 5)"
CONTENT_SAFETY_NAME="cs-legal-mind-$(date +%s | tail -c 5)"
APP_SERVICE_NAME="legal-mind-agent"
MANAGED_IDENTITY_NAME="id-legal-mind-agent"

echo "🔐 Deploying Security Infrastructure for Legal Mind Agent"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Key Vault: $KEY_VAULT_NAME"
echo "Content Safety: $CONTENT_SAFETY_NAME"

# Check if already logged in to Azure
if ! az account show &>/dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Using subscription: $SUBSCRIPTION_ID"

# Create or verify resource group
echo "📦 Ensuring resource group exists..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# Create User-Assigned Managed Identity
echo "🆔 Creating Managed Identity..."
MANAGED_IDENTITY_ID=$(az identity create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$MANAGED_IDENTITY_NAME" \
    --location "$LOCATION" \
    --query id -o tsv)

MANAGED_IDENTITY_CLIENT_ID=$(az identity show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$MANAGED_IDENTITY_NAME" \
    --query clientId -o tsv)

MANAGED_IDENTITY_PRINCIPAL_ID=$(az identity show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$MANAGED_IDENTITY_NAME" \
    --query principalId -o tsv)

echo "✅ Managed Identity created: $MANAGED_IDENTITY_CLIENT_ID"

# Create Azure Key Vault
echo "🔑 Creating Azure Key Vault..."
VAULT_URI=$(az keyvault create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$KEY_VAULT_NAME" \
    --location "$LOCATION" \
    --enable-rbac-authorization true \
    --query properties.vaultUri -o tsv)

echo "✅ Key Vault created: $VAULT_URI"

# Assign Key Vault Secrets Officer role to Managed Identity
echo "🔐 Configuring Key Vault permissions..."
VAULT_RESOURCE_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"

az role assignment create \
    --role "Key Vault Secrets Officer" \
    --assignee "$MANAGED_IDENTITY_PRINCIPAL_ID" \
    --scope "$VAULT_RESOURCE_ID" \
    --output none

echo "✅ Key Vault permissions configured"

# Create Content Safety service
echo "🛡️  Creating Azure AI Content Safety service..."
CONTENT_SAFETY_ENDPOINT=$(az cognitiveservices account create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTENT_SAFETY_NAME" \
    --location "$LOCATION" \
    --kind "ContentSafety" \
    --sku "S0" \
    --yes \
    --query properties.endpoint -o tsv)

echo "✅ Content Safety service created: $CONTENT_SAFETY_ENDPOINT"

# Get Content Safety API keys
CONTENT_SAFETY_KEY=$(az cognitiveservices account keys list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTENT_SAFETY_NAME" \
    --query key1 -o tsv)

# Store secrets in Key Vault
echo "📝 Storing secrets in Key Vault..."

# Microsoft App credentials (use existing values or placeholders)
MICROSOFT_APP_ID="${MICROSOFT_APP_ID:-your-teams-app-id}"
MICROSOFT_APP_PASSWORD="${MICROSOFT_APP_PASSWORD:-your-teams-app-password}"
OPENAI_API_KEY="${OPENAI_API_KEY:-your-openai-api-key}"
AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-https://legal-mind.openai.azure.com/}"

az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "MICROSOFT-APP-ID" --value "$MICROSOFT_APP_ID" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "MICROSOFT-APP-PASSWORD" --value "$MICROSOFT_APP_PASSWORD" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "OPENAI-API-KEY" --value "$OPENAI_API_KEY" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "AZURE-OPENAI-ENDPOINT" --value "$AZURE_OPENAI_ENDPOINT" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "CONTENT-SAFETY-KEY" --value "$CONTENT_SAFETY_KEY" --output none
az keyvault secret set --vault-name "$KEY_VAULT_NAME" --name "CONTENT-SAFETY-ENDPOINT" --value "$CONTENT_SAFETY_ENDPOINT" --output none

echo "✅ Secrets stored in Key Vault"

# Configure App Service with Managed Identity (if exists)
if az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_SERVICE_NAME" &>/dev/null; then
    echo "🌐 Configuring App Service with Managed Identity..."
    
    # Assign managed identity to App Service
    az webapp identity assign \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --identities "$MANAGED_IDENTITY_ID" \
        --output none
    
    # Configure App Service settings
    az webapp config appsettings set \
        --resource-group "$RESOURCE_GROUP" \
        --name "$APP_SERVICE_NAME" \
        --settings \
            "AZURE_KEY_VAULT_URL=$VAULT_URI" \
            "AZURE_CLIENT_ID=$MANAGED_IDENTITY_CLIENT_ID" \
            "CONTENT_SAFETY_ENDPOINT=$CONTENT_SAFETY_ENDPOINT" \
            "AZURE_REGION=$LOCATION" \
        --output none
    
    echo "✅ App Service configured with security settings"
else
    echo "ℹ️  App Service $APP_SERVICE_NAME not found - will need manual configuration"
fi

# Create security configuration summary
echo "📋 Creating security configuration summary..."
cat > security-deployment-summary.json << EOF
{
    "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "resource_group": "$RESOURCE_GROUP",
    "location": "$LOCATION",
    "services": {
        "key_vault": {
            "name": "$KEY_VAULT_NAME",
            "uri": "$VAULT_URI",
            "rbac_enabled": true
        },
        "content_safety": {
            "name": "$CONTENT_SAFETY_NAME",
            "endpoint": "$CONTENT_SAFETY_ENDPOINT",
            "tier": "S0"
        },
        "managed_identity": {
            "name": "$MANAGED_IDENTITY_NAME",
            "client_id": "$MANAGED_IDENTITY_CLIENT_ID",
            "principal_id": "$MANAGED_IDENTITY_PRINCIPAL_ID"
        }
    },
    "app_service_settings": {
        "AZURE_KEY_VAULT_URL": "$VAULT_URI",
        "AZURE_CLIENT_ID": "$MANAGED_IDENTITY_CLIENT_ID",
        "CONTENT_SAFETY_ENDPOINT": "$CONTENT_SAFETY_ENDPOINT",
        "AZURE_REGION": "$LOCATION"
    },
    "secrets_stored": [
        "MICROSOFT-APP-ID",
        "MICROSOFT-APP-PASSWORD", 
        "OPENAI-API-KEY",
        "AZURE-OPENAI-ENDPOINT",
        "CONTENT-SAFETY-KEY",
        "CONTENT-SAFETY-ENDPOINT"
    ]
}
EOF

echo ""
echo "🎉 Security Infrastructure Deployment Complete!"
echo ""
echo "📋 Summary:"
echo "   Key Vault: $VAULT_URI"
echo "   Content Safety: $CONTENT_SAFETY_ENDPOINT"
echo "   Managed Identity: $MANAGED_IDENTITY_CLIENT_ID"
echo ""
echo "📝 Configuration saved to: security-deployment-summary.json"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update your application secrets in Key Vault:"
echo "      az keyvault secret set --vault-name '$KEY_VAULT_NAME' --name 'MICROSOFT-APP-ID' --value 'your-actual-app-id'"
echo "   2. Deploy your application with the updated settings"
echo "   3. Test the security endpoints at /security/status and /compliance/report"
echo ""
echo "🔐 Security features now available:"
echo "   ✓ Secure secrets management with Azure Key Vault"
echo "   ✓ Content safety filtering and PII protection" 
echo "   ✓ Regional compliance and data residency controls"
echo "   ✓ Comprehensive audit logging"
echo ""
