#!/bin/bash
# Azure App Service Configuration Script for Legal Mind Agent
# This script configures the App Service with proper Azure AI Foundry and Model Router settings
#
# Usage:
#   export AZURE_AI_AGENTS_KEY="your-azure-ai-api-key"
#   export AZURE_MODEL_ROUTER_KEY="your-model-router-api-key"
#   ./configure-app-service.sh
#
# The script will use environment variables for sensitive data (API keys)
# while keeping non-sensitive configuration values as defaults.

set -e

# Configuration variables
RESOURCE_GROUP="rg-grayspace004-1361"
APP_NAME="legal-mind-agent"

# Azure AI Foundry Project Configuration
AZURE_AI_AGENTS_ENDPOINT="${AZURE_AI_AGENTS_ENDPOINT:-https://legal-mind-resource.services.ai.azure.com/api/projects/legal-mind}"
AZURE_AI_AGENTS_KEY="${AZURE_AI_AGENTS_KEY:?Error: AZURE_AI_AGENTS_KEY environment variable is required}"

# Model Router Configuration  
AZURE_MODEL_ROUTER_ENDPOINT="${AZURE_MODEL_ROUTER_ENDPOINT:-https://legal-mind-resource.cognitiveservices.azure.com/openai/deployments/model-router/chat/completions?api-version=2025-01-01-preview}"
AZURE_MODEL_ROUTER_KEY="${AZURE_MODEL_ROUTER_KEY:?Error: AZURE_MODEL_ROUTER_KEY environment variable is required}"

# Project metadata
AZURE_PROJECT_ID="legal-mind"
AZURE_RESOURCE_ID="/subscriptions/cc42b0ae-9cac-4f7d-9e3b-cba401789d2f/resourceGroups/rg-grayspace004-1361/providers/Microsoft.CognitiveServices/accounts/legal-mind-resource/projects/legal-mind"

echo "🔧 Configuring Legal Mind Agent App Service..."
echo "App Name: $APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Configure Azure AI settings
echo "📡 Setting Azure AI Foundry and Model Router configuration..."
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings \
        AZURE_AI_AGENTS_ENDPOINT="$AZURE_AI_AGENTS_ENDPOINT" \
        AZURE_AI_AGENTS_KEY="$AZURE_AI_AGENTS_KEY" \
        AZURE_MODEL_ROUTER_ENDPOINT="$AZURE_MODEL_ROUTER_ENDPOINT" \
        AZURE_MODEL_ROUTER_KEY="$AZURE_MODEL_ROUTER_KEY" \
        AZURE_PROJECT_ID="$AZURE_PROJECT_ID" \
        AZURE_RESOURCE_ID="$AZURE_RESOURCE_ID"

echo "✅ Azure AI configuration completed!"

# Optional: Configure Microsoft Teams Bot settings (uncomment and fill in when available)
# echo "🤖 Setting Microsoft Teams Bot configuration..."
# az webapp config appsettings set \
#     --resource-group "$RESOURCE_GROUP" \
#     --name "$APP_NAME" \
#     --settings \
#         MICROSOFT_APP_ID="your-bot-app-id" \
#         MICROSOFT_APP_PASSWORD="your-bot-password"

# Restart the app service to apply changes
echo "🔄 Restarting App Service to apply configuration..."
az webapp restart --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"

echo ""
echo "✅ Configuration completed successfully!"
echo "🌐 App URL: https://$APP_NAME.azurewebsites.net"
echo "🔍 Health Check: https://$APP_NAME.azurewebsites.net/health"
echo ""
echo "📋 Configured Settings:"
echo "   ✅ Azure AI Agents Endpoint"
echo "   ✅ Azure AI Agents API Key"
echo "   ✅ Model Router Endpoint" 
echo "   ✅ Model Router API Key"
echo "   ✅ Azure Project ID"
echo "   ✅ Azure Resource ID"
echo ""
echo "🔧 Next Steps:"
echo "1. Configure Microsoft Teams Bot registration (if needed)"
echo "2. Set up webhook endpoint: https://$APP_NAME.azurewebsites.net/api/messages"
echo "3. Test the bot functionality in Microsoft Teams"
