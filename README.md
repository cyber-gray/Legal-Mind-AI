# Legal-Mind-AI v2.0 🤖⚖️

🚀 **Advanced AI Policy and Governance Assistant with Microsoft Semantic Kernel Integration**

Legal-Mind-AI is a sophisticated AI-powered assistant designed to help organizations navigate the complex landscape of AI governance, policy compliance, and regulatory requirements. This enhanced version features Microsoft Semantic Kernel integration for advanced plugin-based orchestration and intelligent query routing.

## 🌟 Key Features

### 🧠 **Dual Orchestration Systems**
- **Original Orchestrator**: Proven multi-agent system for AI policy guidance
- **Semantic Kernel Orchestrator**: Advanced plugin-based system with intelligent query routing and planning

### 📊 **Multi-Agent Architecture**
- **Policy Expert**: EU AI Act, GDPR, NIST AI RMF compliance guidance
- **News Monitor**: Real-time AI regulation and policy news tracking
- **Legal Search**: Document and regulation search capabilities  
- **Report Generator**: Automated PDF report generation and email delivery

### 🔌 **Plugin-Based Extensibility**
- Modular plugin architecture with Microsoft Semantic Kernel
- Easy plugin development and registration system
- Dynamic capability discovery and intelligent routing

### 🌐 **Real-Time Information**
- News API integration for latest AI policy developments
- Web search capabilities for current legal information
- RSS feed monitoring for regulatory updates

### 🏢 **Enterprise Integration**
- Microsoft Teams Bot Framework support
- Azure AI Projects integration
- Email delivery system for reports
- PDF generation for compliance documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Azure AI Projects account (recommended)
- API keys for news services (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cyber-gray/Legal-Mind-AI.git
   cd Legal-Mind-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv v2env
   source v2env/bin/activate  # On Windows: v2env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   python setup_environment.py
   ```

5. **Test the system**
   ```bash
   python test_enhanced_semantic_kernel.py
   ```

### Quick Test
```bash
# Test with original orchestrator
python console_test.py

# Test with Semantic Kernel orchestrator  
python console_test.py --orchestrator semantic

# Interactive comparison
python console_test.py --compare
```

2. **Create virtual environment**
   ```bash
   python -m venv v2env
   source v2env/bin/activate  # On Windows: v2env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Required - Azure AI Services
   AZURE_PROJECT_ENDPOINT=your_azure_endpoint
   AZURE_AGENT_ID=your_agent_id
   
   # Required - Microsoft Teams
   MICROSOFT_APP_ID=your_teams_app_id
   MICROSOFT_APP_PASSWORD=your_teams_app_password
   
   # Optional - Enhanced Features
   SENDGRID_API_KEY=your_sendgrid_key
   NEWS_API_KEY=your_news_api_key
   BING_SEARCH_KEY=your_bing_key
   ```

5. **Start the application**
   ```bash
   python start.py
   ```

### Azure Setup

1. **Create Azure AI Project**
   - Go to Azure Portal
   - Create a new AI Services resource
   - Note the endpoint and create an agent
   - Add the endpoint and agent ID to your `.env` file

2. **Configure Knowledge Base** (Optional)
   - Set up Azure AI Search
   - Index your legal documents and policies
   - Update search configuration in `.env`

### Teams Bot Setup

1. **Register Bot Application**
   - Go to Microsoft Bot Framework portal
   - Create new bot registration
   - Note App ID and generate App Password
   - Set messaging endpoint: `https://your-domain.com/api/messages`

2. **Add to Teams**
   - Create Teams app manifest
   - Install app in your Teams environment
   - Start chatting with @Legal-Mind-AI

## 💬 Usage

### Basic Queries
```
What are the main requirements of the EU AI Act?
How does NIST AI Risk Management Framework apply to my system?
What's the difference between high-risk and low-risk AI systems?
```

### Special Commands

- **`/help`** - Show detailed help and examples
- **`/news [topic]`** - Get latest AI policy news
  ```
  /news EU AI Act
  /news facial recognition regulation
  /news  (for general AI policy news)
  ```
- **`/report [topic]`** - Generate comprehensive analysis report
  ```
  /report biometric surveillance compliance
  /report GDPR AI requirements summary
  ```
- **`/email your@email.com [topic]`** - Send analysis via email
  ```
  /email john@company.com risk assessment requirements
  ```

### Example Conversations

**Policy Analysis:**
```
User: What are the obligations for high-risk AI systems under the EU AI Act?

Legal-Mind-AI: The EU AI Act establishes several key obligations for high-risk AI systems:

1. **Quality Management System** (Article 17)
   - Implement comprehensive QMS covering entire lifecycle
   - Document processes, procedures, and instructions
   
2. **Data Governance** (Article 10)
   - Ensure training data is relevant, representative, and free of errors
   - Address potential biases in datasets
   
3. **Technical Documentation** (Article 11)
   - Maintain detailed documentation of system design and operation
   - Include risk assessment and mitigation measures
   
[... detailed analysis continues ...]
```

**Latest News:**
```
User: /news AI regulation updates

Legal-Mind-AI: 📰 Latest AI Policy News:

1. **EU AI Act Implementation Guidelines Published**
   Source: European Commission
   The European Commission has released detailed guidelines for implementing the AI Act, including specific requirements for high-risk AI systems...
   🔗 Read more

2. **NIST Updates AI Risk Management Framework**
   Source: NIST
   The National Institute of Standards and Technology has published version 1.1 of its AI Risk Management Framework...
   🔗 Read more

[... more news items ...]
```

## 🔧 Configuration

### Agent Specialization

You can configure specialized agents for different tasks:

```env
# Individual agent IDs (optional - falls back to main agent)
POLICY_EXPERT_AGENT_ID=your_policy_expert_agent
NEWS_MONITOR_AGENT_ID=your_news_agent
DOCUMENT_ANALYZER_AGENT_ID=your_doc_analyzer_agent
REPORT_GENERATOR_AGENT_ID=your_report_agent
```

### News Sources

The system monitors multiple sources:
- News API
- Bing News Search
- RSS feeds from tech publications
- Government and regulatory websites

### Email Configuration

Choose between SendGrid (recommended) or SMTP:

```env
# SendGrid (recommended)
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=legalmind@yourcompany.com

# Or SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
```

## 📋 Supported Regulations & Frameworks

- **EU AI Act** - Comprehensive AI regulation
- **NIST AI Risk Management Framework** - US AI governance guidelines
- **ISO/IEC 23053** - Framework for AI risk management
- **ISO/IEC 23894** - AI risk management standard
- **Canada's AIDA** - Artificial Intelligence and Data Act
- **GDPR** - AI-related data protection requirements
- **FTC AI Guidance** - US Federal Trade Commission guidance
- **Sector-specific regulations** (Healthcare, Finance, etc.)

## 🔍 Troubleshooting

### Common Issues

1. **Bot not responding in Teams**
   - Check MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD
   - Verify messaging endpoint is correct
   - Ensure bot is properly installed in Teams

2. **Azure connection issues**
   - Verify AZURE_PROJECT_ENDPOINT is correct
   - Check Azure credentials and permissions
   - Ensure agent ID is valid

3. **News not updating**
   - Check NEWS_API_KEY and BING_SEARCH_KEY
   - Verify internet connectivity
   - Check API quota limits

4. **Email not sending**
   - Verify email service configuration
   - Check SendGrid/SMTP credentials
   - Ensure recipient email is valid

### Logs

Check application logs:
```bash
tail -f legal_mind_ai.log
```

### Health Check

Verify the service is running:
```bash
curl http://localhost:3978/health
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛡️ Security & Privacy

- All sensitive data is masked in logs
- API keys are stored securely in environment variables
- User conversations are not permanently stored
- PDF reports include disclaimer about verification

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact your system administrator
- Check the documentation wiki

---

**Legal-Mind-AI** - Making AI policy accessible, one question at a time. 🚀
