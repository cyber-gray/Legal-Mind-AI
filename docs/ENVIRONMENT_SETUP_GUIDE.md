# Legal-Mind-AI Environment Variables Setup Guide

## 🚨 **REQUIRED VARIABLES FOR NEW SYSTEM**

### **1. Azure OpenAI Configuration (MANDATORY)**

To make the new streamlined Legal-Mind-AI system work, you **MUST** fill in these variables:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_CHAT_COMPLETION_MODEL=gpt-4
```

**How to get these:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" section
4. Copy **Key 1** as your `AZURE_OPENAI_API_KEY`
5. Copy the **Endpoint** URL as your `AZURE_OPENAI_ENDPOINT`
6. Note your **Deployment Name** (usually "gpt-4", "gpt-4o", etc.) for `AZURE_OPENAI_CHAT_COMPLETION_MODEL`

---

## ✅ **OPTIONAL VARIABLES FOR ENHANCED FUNCTIONALITY**

### **2. Search Capabilities (Recommended)**

For real-time legal research and news monitoring:

#### **Option A: Google Custom Search (Recommended)**
```env
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id_here
```

**Setup Instructions:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Custom Search API
3. Create a Custom Search Engine at [cse.google.com](https://cse.google.com)
4. Configure it to "Search the entire web"
5. Get your API key and Search Engine ID

**Cost**: Free tier (100 queries/day), then $5/1000 queries

#### **Option B: News API (For news-focused queries)**
```env
NEWS_API_KEY=your_news_api_key_here
```

**Setup Instructions:**
1. Go to [NewsAPI.org](https://newsapi.org)
2. Sign up for a free account
3. Get your API key

**Cost**: Free tier (1000 requests/day)

### **3. Azure AI Projects Integration (Optional)**

For enhanced Azure AI capabilities:

```env
AI_PROJECT_CONNECTION_STRING=your_ai_project_connection_string_here
BING_CONNECTION_NAME=your_bing_connection_name_here
```

**Note**: Your existing Bing Search resource is being retired on August 11, 2025, so this is less critical.

---

## 🎯 **CURRENT STATUS OF YOUR VARIABLES**

Based on your existing `.env` file:

### **✅ Already Configured:**
- `AZURE_SEARCH_ENDPOINT` - You have Azure AI Search set up
- `AZURE_SEARCH_API_KEY` - Your search credentials are configured
- `MICROSOFT_APP_ID` & `MICROSOFT_APP_PASSWORD` - Teams integration ready

### **❌ Missing (CRITICAL):**
- `AZURE_OPENAI_API_KEY` - **REQUIRED** for the new system
- `AZURE_OPENAI_ENDPOINT` - **REQUIRED** for the new system

### **⚠️ Recommended Additions:**
- `GOOGLE_SEARCH_API_KEY` - For reliable web search
- `GOOGLE_SEARCH_ENGINE_ID` - For reliable web search
- `NEWS_API_KEY` - For news monitoring

---

## 🚀 **IMMEDIATE ACTION PLAN**

### **Step 1: Get Azure OpenAI Working (CRITICAL)**
1. Find your Azure OpenAI resource in Azure Portal
2. Copy the API key and endpoint
3. Update these variables in your `.env` file:
   ```env
   AZURE_OPENAI_API_KEY=your_actual_key_here
   AZURE_OPENAI_ENDPOINT=https://your-actual-endpoint.openai.azure.com/
   ```

### **Step 2: Test the System**
```bash
cd "/Users/toonitemowo/AI-Legal Agent/Legal-Mind-v2/agents"
python legal-mind.py
```

### **Step 3: Add Search Capability (Recommended)**
Set up Google Custom Search for the best search experience:
1. Follow the Google Custom Search setup instructions above
2. Add the API key and engine ID to your `.env` file

---

## 🔧 **TESTING YOUR CONFIGURATION**

After updating the required variables, run this command to test:

```bash
cd "/Users/toonitemowo/AI-Legal Agent/Legal-Mind-v2/agents"
python legal-mind.py
```

**Expected Output:**
- System initialization messages
- Agent plugin registration
- Test queries with results from each specialist agent

**If you see errors:**
- Check your Azure OpenAI credentials are correct
- Verify your endpoint URL format
- Ensure your deployment name matches exactly

---

## 📊 **SYSTEM CAPABILITIES BY CONFIGURATION**

### **Minimum Configuration (Azure OpenAI only):**
- ✅ PolicyAnalyst agent (regulatory analysis)
- ✅ ComplianceExpert agent (framework compliance)
- ✅ ResearchAgent agent (legal research)  
- ✅ ComparativeAnalyst agent (cross-jurisdiction analysis)
- ❌ Real-time web search (limited to knowledge base)

### **Enhanced Configuration (+ Search APIs):**
- ✅ All agents above
- ✅ Real-time web search for current legal developments
- ✅ News monitoring capabilities
- ✅ Up-to-date regulatory information

---

## 🆘 **SUPPORT**

If you encounter issues:

1. **Azure OpenAI Connection Issues**: Verify your resource is deployed and accessible
2. **Search API Issues**: Check API quotas and permissions
3. **System Errors**: Check the logs for specific error messages

The system is designed to gracefully handle missing optional variables, but **Azure OpenAI configuration is mandatory** for the new streamlined system to work.
