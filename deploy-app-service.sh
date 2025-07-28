#!/bin/bash
# Azure App Service Custom Container Deployment Script for Legal Mind Agent
# Usage: ./deploy-app-service.sh <resource-group> <app-name> <registry-name>

set -e

# Configuration
RESOURCE_GROUP=${1:-"legal-mind-rg"}
APP_NAME=${2:-"legal-mind-agent"}
REGISTRY_NAME=${3:-"legalmindregistry"}
APP_SERVICE_PLAN="legal-mind-plan"
# Azure AI Agents Service is available in specific regions - using East US 2
LOCATION="eastus2"

echo "🚀 Deploying Legal Mind Agent to Azure App Service Custom Container..."
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "Registry: $REGISTRY_NAME"
echo ""

# Check if logged in to Azure
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure CLI first: az login"
    exit 1
fi

# Create resource group if it doesn't exist
echo "📋 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry if it doesn't exist
echo "🐳 Creating container registry..."
az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true

# Build and push container image
echo "🔨 Building and pushing container image..."
az acr build --registry $REGISTRY_NAME --image $APP_NAME:latest .

# Create App Service Plan (Premium for Custom Container + Always On)
echo "📊 Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku P1V3 \
    --is-linux

# Get registry credentials
echo "🔑 Getting registry credentials..."
REGISTRY_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Create App Service with Custom Container
echo "🚢 Creating App Service..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --name $APP_NAME \
    --deployment-container-image-name $REGISTRY_SERVER/$APP_NAME:latest

# Configure container registry
echo "🔧 Configuring container registry..."
az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $REGISTRY_SERVER/$APP_NAME:latest \
    --docker-registry-server-url https://$REGISTRY_SERVER \
    --docker-registry-server-user $REGISTRY_USERNAME \
    --docker-registry-server-password $REGISTRY_PASSWORD

# Configure App Settings
echo "⚙️ Configuring app settings..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
        PORT=80 \
        PYTHONUNBUFFERED=1 \
        MICROSOFT_APP_ID="$MICROSOFT_APP_ID" \
        MICROSOFT_APP_PASSWORD="$MICROSOFT_APP_PASSWORD" \
        AZURE_AI_AGENTS_ENDPOINT="$AZURE_AI_AGENTS_ENDPOINT" \
        AZURE_AI_AGENTS_KEY="$AZURE_AI_AGENTS_KEY" \
        AZURE_MODEL_ROUTER_ENDPOINT="$AZURE_MODEL_ROUTER_ENDPOINT" \
        AZURE_MODEL_ROUTER_KEY="$AZURE_MODEL_ROUTER_KEY" \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
        DOCKER_ENABLE_CI=true

# Enable Always On (Critical for preventing cold starts)
echo "🔥 Enabling Always On..."
az webapp config set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --always-on true

# Configure health check
echo "🏥 Configuring health check..."
az webapp config set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --generic-configurations '{"healthCheckPath": "/health"}'

# Enable Application Logging
echo "📊 Enabling logging..."
az webapp log config \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --application-logging filesystem \
    --level information

# Get the app URL
APP_URL=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName --output tsv)

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 App URL: https://$APP_URL"
echo "🔍 Health Check: https://$APP_URL/health"
echo ""
echo "📋 Next steps:"
echo "1. Configure your bot registration endpoint to: https://$APP_URL/api/messages"
echo "2. Set up Application Insights monitoring using app-insights-monitoring.json"
echo "3. Enable continuous deployment if needed"
echo "4. Test your bot in Microsoft Teams"
echo ""
echo "💡 Environment variables needed:"
echo "   export MICROSOFT_APP_ID='your-bot-app-id'"
echo "   export MICROSOFT_APP_PASSWORD='your-bot-password'"
echo "   export AZURE_AI_AGENTS_ENDPOINT='your-agents-endpoint'"
echo "   export AZURE_AI_AGENTS_KEY='your-agents-key'"
echo "   export AZURE_MODEL_ROUTER_ENDPOINT='your-router-endpoint' (optional)"
echo "   export AZURE_MODEL_ROUTER_KEY='your-router-key' (optional)"
echo ""
echo "🔧 App Service Features Enabled:"
echo "   ✅ Always On (prevents cold starts)"  
echo "   ✅ Health Check (/health endpoint)"
echo "   ✅ Custom Container (avoids Oryx build issues)"
echo "   ✅ Premium Plan (>1.5GB memory limit)"
echo "   ✅ Application Logging enabled"
