# Azure AI Foundry Integration Guide

## 🚀 Quick Start with Azure AI Foundry

This guide helps you leverage the new Azure AI Foundry integration for enhanced multi-agent legal analysis.

---

## 📋 Prerequisites

- ✅ Azure subscription with AI Services
- ✅ Azure AI Foundry project created
- ✅ 5 legal specialist agents created in Foundry
- ✅ Azure CLI authentication configured

---

## 🏗️ Setup Process

### 1. Create Azure AI Foundry Project

1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com)
2. Create new project: **"Legal-Mind"** (or your preferred name)
3. Note your project endpoint: `https://your-project.services.ai.azure.com/api/projects/Your-Project`

### 2. Create Specialized Agents

Create these 5 agents in your Azure AI Foundry project:

| Agent Name | Purpose | Suggested Instructions |
|------------|---------|----------------------|
| **Legal-Mind-Agent** | Coordinator & synthesis | "You coordinate legal analysis by managing multiple specialist agents and synthesizing comprehensive legal advice..." |
| **Policy-Expert-Agent** | Policy analysis | "You specialize in analyzing legal policies, regulatory frameworks, and policy implications..." |
| **News-Monitor-Agent** | Research & precedents | "You conduct comprehensive legal research, analyze case law, and identify relevant precedents..." |
| **Document-Analyzer-Agent** | Compliance assessment | "You assess regulatory compliance, identify risks, and provide compliance recommendations..." |
| **Report-Generator-Agent** | Comparative analysis | "You perform cross-jurisdictional legal analysis and compare legal frameworks..." |

### 3. Configure Agent Mapping

Update the agent IDs in `legal_mind_experimental.py`:

```python
self.foundry_agent_mapping = {
    self.COORDINATOR: "asst_your_legal_mind_agent_id",
    self.POLICY_ANALYST: "asst_your_policy_expert_agent_id", 
    self.RESEARCH_AGENT: "asst_your_news_monitor_agent_id",
    self.COMPLIANCE_EXPERT: "asst_your_document_analyzer_agent_id",
    self.COMPARATIVE_ANALYST: "asst_your_report_generator_agent_id"
}
```

---

## 🔧 Configuration

### Environment Variables
```env
# Azure AI Foundry (Primary)
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/Your-Project

# Azure OpenAI (Fallback)
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure Storage (Persistence)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### Authentication
```bash
# Azure CLI (Development)
az login

# Or use Managed Identity (Production)
# No additional setup needed - handled automatically
```

---

## 🚀 Usage

### Initialize with Foundry Integration
```python
from legal_mind_experimental import EnhancedLegalMindOrchestrator

# Initialize with Azure AI Foundry
orchestrator = EnhancedLegalMindOrchestrator(use_foundry=True)
await orchestrator.initialize()

# Process legal query
responses = await orchestrator.process_group_chat(
    "What are the GDPR compliance requirements for a US SaaS company processing EU data?"
)
```

### Interactive Mode
```bash
python legal_mind_experimental.py
```

---

## 🔍 Portal Features

### View Conversations
1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com/projects/Legal-Mind)
2. Go to **Agents** section - see your 5 specialized agents
3. Go to **Threads** section - view all conversation threads
4. Click any thread to see full conversation history

### Thread Benefits
- ✅ **Full Visibility**: Complete conversation history in Azure portal
- ✅ **Persistence**: Threads persist across system restarts
- ✅ **Traceability**: Audit trail for compliance and analysis
- ✅ **Collaboration**: Share threads with team members
- ✅ **Analytics**: Built-in usage and performance metrics

---

## 📊 Monitoring & Analytics

### System Performance
- **Thread Creation**: Real Azure AI Foundry threads
- **Response Time**: ~15-20 seconds per agent
- **Success Rate**: 100% with automatic fallback
- **Quality Scoring**: Built-in response quality assessment

### Portal Analytics
- View conversation statistics in Azure portal
- Monitor agent usage and performance
- Track thread creation and management
- Analyze response patterns and quality

---

## 🔄 Dual-Mode Operation

### Foundry Mode (Primary)
- Uses Azure AI Foundry agents and threads
- Full portal visibility and management
- Enterprise-grade features and analytics
- Automatic thread creation and persistence

### Direct Mode (Fallback)
- Falls back to direct Azure OpenAI calls
- Maintains functionality during Foundry issues
- Uses same agent logic with OpenAI API
- Transparent fallback - no user impact

---

## 🛠️ Troubleshooting

### Common Issues

#### Agent Not Found
```
Error: Foundry agent PolicyAnalyst not available, falling back to direct mode
```
**Solution**: Verify agent IDs in `foundry_agent_mapping` match your Azure AI Foundry agents

#### Authentication Error
```
Error: DefaultAzureCredential failed to authenticate
```
**Solution**: Run `az login` or configure managed identity

#### Thread Creation Failed
```
Error: Failed to create thread
```
**Solution**: Check project endpoint URL and permissions

### Verification Commands
```bash
# Test Azure CLI authentication
az account show

# Test project endpoint
curl -H "Authorization: Bearer $(az account get-access-token --query accessToken -o tsv)" \
     "https://your-project.services.ai.azure.com/api/projects/Your-Project/threads"
```

---

## 🎯 Best Practices

### Agent Management
- **Consistent Naming**: Use descriptive, consistent agent names
- **Clear Instructions**: Provide detailed agent instructions for best results
- **Regular Updates**: Keep agent instructions current with legal requirements

### Thread Management
- **Thread Lifecycle**: Threads persist automatically - no cleanup needed
- **Conversation Context**: Each query creates new thread for isolation
- **History Access**: Use Azure portal for thread history and analysis

### Performance Optimization
- **Concurrent Processing**: System handles multiple agents efficiently
- **Quality Monitoring**: Monitor quality scores for optimization opportunities
- **Fallback Testing**: Regularly test fallback mode functionality

---

## 📚 Additional Resources

- **[Main Documentation](./README.md)**: Complete system overview
- **[Integration Checkpoint](./AZURE_AI_FOUNDRY_INTEGRATION_CHECKPOINT.md)**: Detailed implementation notes
- **[Azure AI Foundry Docs](https://docs.microsoft.com/azure/ai-studio/)**: Official Azure documentation
- **[Semantic Kernel Guide](https://learn.microsoft.com/semantic-kernel/)**: Semantic Kernel documentation

---

**🏆 Success!** You now have a fully integrated Azure AI Foundry legal analysis system with portal visibility, thread persistence, and enterprise-grade capabilities!
