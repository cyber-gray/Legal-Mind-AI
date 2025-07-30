# App Service Stability Configuration Summary

## Issue Resolution

### 1. Worker Process Failed to Start
- **Root Cause**: Oryx build system 1.5GB site limit exceeded by ML/AI libraries
- **Solution**: Custom Docker container with optimized base image
- **Implementation**: `Dockerfile` with python:3.11-slim base, system dependencies pre-installed

### 2. Cold Start > 60s  
- **Root Cause**: Python 3.11 + Semantic Kernel + Azure AI Agents library load time
- **Solution**: Always-on equivalent + health endpoint warm-up
- **Implementation**: 
  - App Service: Always-on enabled via `deploy-app-service.sh`
  - Container Apps: `minReplicas: 1` in `container-app.yaml`
  - Health endpoint with component pre-warming in `main.py`

### 3. Missing Dependencies
- **Root Cause**: aiohttp compilation issues, dependency conflicts
- **Solution**: Pinned wheel versions, pre-built wheels in container
- **Implementation**: `requirements.txt` with specific versions (aiohttp==3.11.11, etc.)

## Deployment Options

### Option A: Azure App Service Custom Container (Recommended)
```bash
./deploy-app-service.sh <resource-group> <app-name> <registry-name>
```

**Features**:
- Premium plan (P1V3) for >1.5GB memory
- Always On enabled (prevents cold starts)
- Health check endpoint configured
- Custom container bypasses Oryx limitations
- Application Insights ready

### Option B: Azure Container Apps
```bash
./deploy-container-app.sh <resource-group> <app-name>
```

**Features**:
- Serverless scaling with always-on (minReplicas: 1)
- Advanced health probes (startup, liveness, readiness)
- Container-native environment
- Built-in monitoring and logging

## Configuration Files

### Core Files
- `Dockerfile`: Production container with ML/AI dependencies
- `requirements.txt`: Pinned versions (40+ packages)
- `main.py`: Enhanced health endpoint with warm-up
- `runtime.txt`: Python 3.11 specification

### Deployment Scripts
- `deploy-app-service.sh`: App Service with custom container
- `deploy-container-app.sh`: Container Apps deployment
- `container-app.yaml`: Container Apps configuration
- `app-insights-monitoring.json`: Monitoring setup

## Testing Local Development

### Build and Test Container
```bash
# Build image
docker build -t legal-mind-agent .

# Run locally
docker run -p 3978:3978 \
  -e MICROSOFT_APP_ID="your-app-id" \
  -e MICROSOFT_APP_PASSWORD="your-password" \
  -e AZURE_AI_AGENTS_ENDPOINT="your-endpoint" \
  legal-mind-agent

# Test health endpoint
curl http://localhost:3978/health
```

### Expected Health Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "bot_framework": "ready",
    "azure_ai_agents": "ready",
    "legal_tools": "ready"
  },
  "environment": "production",
  "uptime": "00:05:23"
}
```

## Environment Variables Required

### Bot Framework
- `MICROSOFT_APP_ID`: Bot registration app ID
- `MICROSOFT_APP_PASSWORD`: Bot registration password

### Azure AI Agents  
- `AZURE_AI_AGENTS_ENDPOINT`: Agents service endpoint
- `AZURE_AI_AGENTS_KEY`: Service authentication key (optional)

### Optional
- `PORT`: Service port (default: 3978)
- `ENVIRONMENT`: Environment name (default: production)

## Monitoring Setup

### Application Insights
- Availability tests every 5 minutes
- Warm-up pings every 1 minute
- Custom metrics for bot interactions
- Alert rules for failures and performance

### Health Checks
- Container: Every 30s with 120s startup grace
- App Service: Built-in health check path `/health`
- Container Apps: Startup, liveness, readiness probes

## Performance Characteristics

### Startup Time
- Cold start: ~45-60s (initial container start)
- Warm start: ~2-3s (always-on prevents this)
- Health check: <1s response time

### Memory Usage
- Base container: ~200MB
- With ML libraries loaded: ~800MB-1.2GB
- Peak usage: ~1.5-2GB (handled by Premium plans)

### Scaling
- App Service: Vertical scaling only
- Container Apps: Horizontal scaling (0-10 replicas)

## Troubleshooting

### Container Build Issues
```bash
# Check build logs
az acr task logs --registry <registry-name>

# Test locally first
docker build -t test-legal-mind .
docker run -p 3978:3978 test-legal-mind
```

### Deployment Issues
```bash
# Check app logs
az webapp log tail --name <app-name> --resource-group <rg>

# Check container status
az webapp show --name <app-name> --resource-group <rg> --query state
```

### Performance Issues
```bash
# Monitor health endpoint
curl https://<app-name>.azurewebsites.net/health

# Check Application Insights metrics
# Navigate to Azure Portal > Application Insights > Performance
```

## Next Steps After Deployment

1. **Configure Bot Registration**: Update messaging endpoint
2. **Test Teams Integration**: Deploy app package and test
3. **Set up CI/CD**: GitHub Actions or Azure DevOps
4. **Monitor Performance**: Application Insights dashboards
5. **Scale if Needed**: Adjust plan or replica count

## Security Considerations

- Non-root container user
- Minimal base image (python:3.11-slim)
- Environment variable injection
- HTTPS endpoints only
- Application Insights telemetry
