#!/bin/bash
# Azure Container App Deployment Script for Legal Mind Agent
# Usage: ./deploy-container-app.sh <resource-group> <environment> <registry-name>

set -e

# Configuration
RESOURCE_GROUP=${1:-"legal-mind-rg"}
APP_NAME=${2:-"legal-mind-agent"}
REGISTRY_NAME="legalmindregistry"
CONTAINER_APP_ENV="legal-mind-env"
# Azure AI Agents Service is available in specific regions - using East US 2
LOCATION="eastus2"

echo "🚀 Deploying Legal Mind Agent to Azure Container Apps..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Environment: $ENVIRONMENT"
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

# Create Container Apps environment if it doesn't exist
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Get registry credentials
echo "🔑 Getting registry credentials..."
REGISTRY_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Deploy Container App
echo "🚢 Deploying Container App..."
az containerapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --image $REGISTRY_SERVER/$APP_NAME:latest \
    --registry-server $REGISTRY_SERVER \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --target-port 80 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        PORT=80 \
        PYTHONUNBUFFERED=1 \
    --secrets \
        microsoft-app-id="$MICROSOFT_APP_ID" \
        microsoft-app-password="$MICROSOFT_APP_PASSWORD" \
        azure-ai-agents-endpoint="$AZURE_AI_AGENTS_ENDPOINT"

# Get the app URL
APP_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 App URL: https://$APP_URL"
echo "🔍 Health Check: https://$APP_URL/health"
echo ""
echo "📋 Next steps:"
echo "1. Configure your bot registration endpoint to: https://$APP_URL/api/messages"
echo "2. Set up Application Insights monitoring using app-insights-monitoring.json"
echo "3. Test your bot in Microsoft Teams"
echo ""
echo "💡 Environment variables needed:"
echo "   export MICROSOFT_APP_ID='your-bot-app-id'"
echo "   export MICROSOFT_APP_PASSWORD='your-bot-password'"
echo "   export AZURE_AI_AGENTS_ENDPOINT='your-agents-endpoint'"
