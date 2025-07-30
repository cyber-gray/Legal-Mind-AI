#!/bin/bash
# Complete Legal Mind Agent Azure Deployment Script
# This script will create all required Azure resources and deploy the bot

set -e

# Configuration (modify these as needed)
RESOURCE_GROUP="legal-mind-rg"
APP_NAME="legal-mind-agent"
REGISTRY_NAME="legalmindregistry"
# Azure AI Agents Service is available in specific regions - using East US 2
LOCATION="eastus2"
BOT_NAME="legal-mind-bot"
AGENTS_SERVICE_NAME="legal-mind-agents"
MODEL_ROUTER_SERVICE_NAME="legal-mind-router"

# Supported regions for Azure AI Agents Service and Model Router
SUPPORTED_AGENTS_REGIONS=("eastus2" "westus2" "northeurope" "uksouth" "australiaeast" "japaneast")
SUPPORTED_MODEL_ROUTER_REGIONS=("eastus2" "westus2" "northeurope" "uksouth")

echo "🚀 Starting complete Legal Mind Agent deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "App Name: $APP_NAME"
echo ""

# Validate region support for Azure AI Agents Service
echo "🔍 Validating regional availability..."
if [[ ! " ${SUPPORTED_AGENTS_REGIONS[@]} " =~ " ${LOCATION} " ]]; then
    echo "❌ Error: Azure AI Agents Service is not available in region: $LOCATION"
    echo "✅ Supported regions: ${SUPPORTED_AGENTS_REGIONS[*]}"
    echo "💡 Please update LOCATION variable to one of the supported regions"
    exit 1
fi

if [[ ! " ${SUPPORTED_MODEL_ROUTER_REGIONS[@]} " =~ " ${LOCATION} " ]]; then
    echo "⚠️  Warning: Model Router may not be available in region: $LOCATION"
    echo "✅ Supported regions: ${SUPPORTED_MODEL_ROUTER_REGIONS[*]}"
    echo "💡 Consider using a Model Router supported region for full functionality"
fi

echo "✅ Region $LOCATION supports Azure AI Agents Service"
echo ""

# Check Azure CLI login
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure CLI first: az login"
    exit 1
fi

# Create resource group
echo "📋 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure AI Agents service (Cognitive Services account)
echo "🤖 Creating Azure AI Agents service..."
az cognitiveservices account create \
    --name $AGENTS_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --kind "AIServices" \
    --sku "S0" \
    --custom-domain $AGENTS_SERVICE_NAME \
    --assign-identity

# Create Model Router service if supported in region
if [[ " ${SUPPORTED_MODEL_ROUTER_REGIONS[@]} " =~ " ${LOCATION} " ]]; then
    echo "🔀 Creating Model Router service..."
    az cognitiveservices account create \
        --name $MODEL_ROUTER_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --kind "AIServices" \
        --sku "S0" \
        --custom-domain $MODEL_ROUTER_SERVICE_NAME \
        --assign-identity
    
    # Get Model Router endpoint and key
    MODEL_ROUTER_ENDPOINT=$(az cognitiveservices account show \
        --name $MODEL_ROUTER_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.endpoint \
        --output tsv)
    
    MODEL_ROUTER_KEY=$(az cognitiveservices account keys list \
        --name $MODEL_ROUTER_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --query key1 \
        --output tsv)
    
    echo "✅ Model Router service created"
    echo "   Endpoint: $MODEL_ROUTER_ENDPOINT"
else
    echo "⚠️  Skipping Model Router - not available in $LOCATION"
    MODEL_ROUTER_ENDPOINT=""
    MODEL_ROUTER_KEY=""
fi

# Get Agents service endpoint and key
AGENTS_ENDPOINT=$(az cognitiveservices account show \
    --name $AGENTS_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)

AGENTS_KEY=$(az cognitiveservices account keys list \
    --name $AGENTS_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

echo "✅ Azure AI Agents service created"
echo "   Endpoint: $AGENTS_ENDPOINT"

# Create App Registration for Bot
echo "🔑 Creating App Registration..."
APP_REGISTRATION=$(az ad app create \
    --display-name "$BOT_NAME" \
    --sign-in-audience "AzureADandPersonalMicrosoftAccount")

APP_ID=$(echo $APP_REGISTRATION | jq -r '.appId')

# Create client secret
echo "🔐 Creating client secret..."
APP_SECRET=$(az ad app credential reset \
    --id $APP_ID \
    --credential-description "Legal Mind Bot Secret" \
    --query password \
    --output tsv)

echo "✅ App Registration created"
echo "   App ID: $APP_ID"

# Deploy the container application
echo "🚢 Deploying container application..."
export MICROSOFT_APP_ID=$APP_ID
export MICROSOFT_APP_PASSWORD=$APP_SECRET
export AZURE_AI_AGENTS_ENDPOINT=$AGENTS_ENDPOINT
export AZURE_AI_AGENTS_KEY=$AGENTS_KEY
if [[ -n "$MODEL_ROUTER_ENDPOINT" ]]; then
    export AZURE_MODEL_ROUTER_ENDPOINT=$MODEL_ROUTER_ENDPOINT
    export AZURE_MODEL_ROUTER_KEY=$MODEL_ROUTER_KEY
fi

# Run the App Service deployment
./deploy-app-service.sh $RESOURCE_GROUP $APP_NAME $REGISTRY_NAME

# Get the app URL
APP_URL="https://$APP_NAME.azurewebsites.net"

# Create Bot Service resource
echo "🤖 Creating Bot Service..."
az bot create \
    --resource-group $RESOURCE_GROUP \
    --name $BOT_NAME \
    --location "global" \
    --kind "webapp" \
    --description "Legal Mind AI Agent for Microsoft Teams" \
    --display-name "Legal Mind Agent" \
    --endpoint "$APP_URL/api/messages" \
    --msa-app-id $APP_ID \
    --sku "F0"

# Enable Teams channel
echo "📱 Enabling Microsoft Teams channel..."
az bot msteams create \
    --resource-group $RESOURCE_GROUP \
    --name $BOT_NAME

echo ""
echo "🎉 Legal Mind Agent deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Service: $APP_URL"
echo "   Health Check: $APP_URL/health" 
echo "   Bot Name: $BOT_NAME"
echo "   App ID: $APP_ID"
echo ""
echo "🔑 Environment Variables (save these securely):"
echo "   MICROSOFT_APP_ID=$APP_ID"
echo "   MICROSOFT_APP_PASSWORD=$APP_SECRET"
echo "   AZURE_AI_AGENTS_ENDPOINT=$AGENTS_ENDPOINT"
echo "   AZURE_AI_AGENTS_KEY=$AGENTS_KEY"
if [[ -n "$MODEL_ROUTER_ENDPOINT" ]]; then
    echo "   AZURE_MODEL_ROUTER_ENDPOINT=$MODEL_ROUTER_ENDPOINT" 
    echo "   AZURE_MODEL_ROUTER_KEY=$MODEL_ROUTER_KEY"
fi
echo ""
echo "📱 Next Steps:"
echo "1. Test the health endpoint: curl $APP_URL/health"
echo "2. Test bot in Bot Framework Emulator with App ID and Password"
echo "3. Create Teams app package and install in Teams"
echo "4. Configure additional channels if needed"
echo ""
echo "🔧 Troubleshooting:"
echo "   - View app logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "   - Check container status: az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "   - Monitor in Azure Portal: https://portal.azure.com"
