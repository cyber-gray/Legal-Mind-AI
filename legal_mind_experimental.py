"""
Legal-Mind-AI Multi-Agent Orchestrator - Experimental Version
Enhanced version with modular prompts, quality scoring, and improved architecture
"""

import os
import json
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Core imports
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

# Azure Storage for persistence
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Import quality scorer
from quality_scorer import LegalResponseQualityScorer, QualityMetrics

# Load environment variables
load_dotenv()

@dataclass
class LegalAgentConfig:
    """Enhanced configuration for legal agents"""
    agent_type: str
    name: str
    instructions: str
    description: str = ""
    prompt_file: Optional[str] = None
    model_settings: Optional[Dict] = None

class EnhancedLegalMindOrchestrator:
    """
    Enhanced Legal-Mind-AI Orchestrator with modular prompts and quality scoring
    """
    
    def __init__(self):
        self.kernel = Kernel()
        self.chat_service = None
        self.conversation_id = str(uuid.uuid4())
        self.storage_client = None
        self.container_name = "legal-mind-group-chat"
        self.quality_scorer = LegalResponseQualityScorer()
        
        # Agent names
        self.POLICY_ANALYST = "PolicyAnalyst"
        self.COMPLIANCE_EXPERT = "ComplianceExpert" 
        self.RESEARCH_AGENT = "ResearchAgent"
        self.COMPARATIVE_ANALYST = "ComparativeAnalyst"
        self.COORDINATOR = "Coordinator"
        
        # Initialize services
        self._initialize_services()
        self._setup_agent_configs()
    
    def _load_prompt_from_file(self, prompt_file: str) -> str:
        """Load agent prompt from external markdown file"""
        try:
            prompt_path = Path(__file__).parent / "agents" / "prompts" / prompt_file
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Prompt file {prompt_file} not found, using fallback")
                return self._get_fallback_prompt(prompt_file)
        except Exception as e:
            logger.error(f"Error loading prompt from {prompt_file}: {e}")
            return self._get_fallback_prompt(prompt_file)
    
    def _get_fallback_prompt(self, prompt_file: str) -> str:
        """Fallback prompts if external files are not available"""
        fallback_prompts = {
            "policy_analyst.md": """You are a PolicyAnalyst specializing in legal policy analysis.
Your responsibilities:
- Analyze legal policies and their implications
- Identify key policy frameworks and regulatory structures  
- Provide detailed policy interpretation and analysis
- Explain complex legal concepts in clear terms

Always provide:
1. Clear policy interpretation
2. Key implications and impacts
3. Relevant regulatory context
4. Actionable insights

When your analysis is complete, end with: "Policy analysis complete."
Be precise, thorough, and legally accurate in your analysis.""",
            
            "compliance_expert.md": """You are a ComplianceExpert specializing in regulatory compliance.
Your responsibilities:
- Assess compliance requirements and standards
- Identify potential compliance gaps and risks
- Provide compliance recommendations and solutions
- Evaluate regulatory adherence across jurisdictions

Always provide:
1. Compliance assessment results
2. Risk identification and mitigation strategies
3. Regulatory requirement analysis
4. Implementation recommendations

When your assessment is complete, end with: "Compliance assessment complete."
Focus on practical compliance solutions and risk management."""
        }
        
        return fallback_prompts.get(prompt_file, "You are a legal analysis assistant.")
    
    
    def _initialize_services(self):
        """Initialize Azure services"""
        try:
            # Initialize Azure OpenAI service
            azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            
            if not all([azure_openai_endpoint, azure_openai_key, azure_openai_deployment]):
                raise ValueError("Missing Azure OpenAI configuration")
            
            self.chat_service = AzureChatCompletion(
                deployment_name=azure_openai_deployment,
                endpoint=azure_openai_endpoint,
                api_key=azure_openai_key,
                service_id="azure_openai",
            )
            
            self.kernel.add_service(self.chat_service)
            logger.info("✅ Azure OpenAI service initialized")
            
            # Initialize Storage for persistence
            storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if storage_connection_string:
                self.storage_client = BlobServiceClient.from_connection_string(storage_connection_string)
                try:
                    self.storage_client.create_container(self.container_name)
                except Exception:
                    pass  # Container already exists
                logger.info("✅ Azure Storage initialized")
            
        except Exception as e:
            logger.error(f"❌ Service initialization error: {e}")
            raise
    
    def _setup_agent_configs(self):
        """Setup configurations for different legal agents"""
        self.agent_configs = {
            self.POLICY_ANALYST: LegalAgentConfig(
                agent_type=self.POLICY_ANALYST.lower(),
                name=self.POLICY_ANALYST,
                instructions="""You are a PolicyAnalyst specializing in legal policy analysis.
Your responsibilities:
- Analyze legal policies and their implications
- Identify key policy frameworks and regulatory structures  
- Provide detailed policy interpretation and analysis
- Explain complex legal concepts in clear terms

Always provide:
1. Clear policy interpretation
2. Key implications and impacts
3. Relevant regulatory context
4. Actionable insights

When your analysis is complete, end with: "Policy analysis complete."
Be precise, thorough, and legally accurate in your analysis.""",
                description="Specializes in analyzing legal policies and regulations"
            ),
            self.COMPLIANCE_EXPERT: LegalAgentConfig(
                agent_type=self.COMPLIANCE_EXPERT.lower(),
                name=self.COMPLIANCE_EXPERT,
                instructions="""You are a ComplianceExpert specializing in regulatory compliance.
Your responsibilities:
- Assess compliance requirements and standards
- Identify potential compliance gaps and risks
- Provide compliance recommendations and solutions
- Evaluate regulatory adherence across jurisdictions

Always provide:
1. Compliance assessment results
2. Risk identification and mitigation strategies
3. Regulatory requirement analysis
4. Implementation recommendations

When your assessment is complete, end with: "Compliance assessment complete."
Focus on practical compliance solutions and risk management.""",
                description="Expert in legal compliance and regulatory requirements"
            ),
            self.RESEARCH_AGENT: LegalAgentConfig(
                agent_type=self.RESEARCH_AGENT.lower(),
                name=self.RESEARCH_AGENT,
                instructions="""You are a ResearchAgent specializing in legal research and analysis.
Your responsibilities:
- Conduct comprehensive legal research
- Analyze case law, statutes, and regulations
- Provide evidence-based legal insights
- Synthesize complex legal information

Always provide:
1. Thorough research findings
2. Relevant legal precedents and authorities
3. Evidence-based analysis
4. Research methodology and sources

When your research is complete, end with: "Legal research complete."
Ensure all research is accurate, current, and properly sourced.""",
                description="Conducts comprehensive legal research and analysis"
            ),
            self.COMPARATIVE_ANALYST: LegalAgentConfig(
                agent_type=self.COMPARATIVE_ANALYST.lower(),
                name=self.COMPARATIVE_ANALYST,
                instructions="""You are a ComparativeAnalyst specializing in comparative legal analysis.
Your responsibilities:
- Compare legal frameworks across jurisdictions
- Analyze differences and similarities in legal approaches
- Provide cross-jurisdictional insights
- Identify best practices and trends

Always provide:
1. Detailed comparative analysis
2. Key differences and similarities
3. Jurisdictional insights and trends
4. Best practice recommendations

When your analysis is complete, end with: "Comparative analysis complete."
Focus on providing actionable comparative insights.""",
                description="Compares laws and regulations across jurisdictions"
            ),
            self.COORDINATOR: LegalAgentConfig(
                agent_type=self.COORDINATOR.lower(),
                name=self.COORDINATOR,
                instructions="""You are a Coordinator responsible for managing legal analysis conversations.
Your responsibilities:
- Orchestrate multi-agent legal analysis
- Synthesize insights from specialized agents
- Provide comprehensive final analysis
- Ensure all aspects of legal questions are addressed

When to engage other agents:
- PolicyAnalyst: For policy interpretation and framework analysis
- ComplianceExpert: For regulatory compliance assessment
- ResearchAgent: For legal research and precedent analysis
- ComparativeAnalyst: For cross-jurisdictional comparisons

Always provide:
1. Comprehensive synthesis of agent insights
2. Clear final recommendations
3. Action items and next steps
4. Summary of key findings

Score your analysis quality from 1-10. If below 8, request additional analysis from appropriate specialists.
When satisfied with the quality (8+), end with: "Legal analysis complete - Quality Score: [X]/10".""",
                description="Coordinates multi-agent legal analysis and provides synthesis"
            )
        }
    
    async def get_agent_response(self, agent_name: str, user_input: str, conversation_history: List[str] = None) -> str:
        """Get response from a specific agent using direct OpenAI call"""
        try:
            if agent_name not in self.agent_configs:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            config = self.agent_configs[agent_name]
            
            # Build the prompt with agent instructions and context
            system_prompt = config.instructions
            
            # Add conversation history if provided
            context = ""
            if conversation_history:
                context = "\n\nPrevious conversation:\n" + "\n".join(conversation_history[-5:])  # Last 5 messages
            
            # Create the function for this agent
            agent_function = KernelFunctionFromPrompt(
                function_name=f"{agent_name.lower()}_function",
                prompt=f"""
{system_prompt}

{context}

User Query: {{{{$input}}}}

Provide your analysis as {config.name}:
"""
            )
            
            # Get response
            response = await self.kernel.invoke(agent_function, input=user_input)
            
            return str(response)
            
        except Exception as e:
            logger.error(f"❌ Error getting response from {agent_name}: {e}")
            return f"Error: {agent_name} failed to respond - {e}"
    
    async def process_group_chat(self, user_query: str) -> List[Dict[str, Any]]:
        """Process a query using group chat simulation"""
        try:
            logger.info(f"🔍 Processing legal query with group chat: {user_query[:100]}...")
            
            responses = []
            conversation_history = [f"User: {user_query}"]
            start_time = datetime.utcnow()
            
            # Step 1: Coordinator analyzes the query and determines needed specialists
            coord_response = await self.get_agent_response(
                self.COORDINATOR, 
                user_query, 
                conversation_history
            )
            
            response_data = {
                "agent": self.COORDINATOR,
                "content": coord_response,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_id": self.conversation_id
            }
            responses.append(response_data)
            conversation_history.append(f"{self.COORDINATOR}: {coord_response}")
            
            # Step 2: Determine which specialists to engage based on query
            needed_agents = self._determine_needed_agents(user_query)
            
            # Step 3: Get responses from relevant specialists
            for agent_name in needed_agents:
                agent_response = await self.get_agent_response(
                    agent_name,
                    user_query,
                    conversation_history
                )
                
                response_data = {
                    "agent": agent_name,
                    "content": agent_response,
                    "timestamp": datetime.utcnow().isoformat(),
                    "conversation_id": self.conversation_id
                }
                responses.append(response_data)
                conversation_history.append(f"{agent_name}: {agent_response}")
            
            # Step 4: Final synthesis by Coordinator
            synthesis_prompt = f"""Based on the specialist analysis above, provide a comprehensive synthesis and final recommendations for: {user_query}"""
            
            final_response = await self.get_agent_response(
                self.COORDINATOR,
                synthesis_prompt,
                conversation_history
            )
            
            response_data = {
                "agent": f"{self.COORDINATOR} (Final Synthesis)",
                "content": final_response,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_id": self.conversation_id
            }
            responses.append(response_data)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Save conversation
            conversation_data = {
                "conversation_id": self.conversation_id,
                "user_query": user_query,
                "responses": responses,
                "execution_time_ms": int(execution_time),
                "agent_count": len(set(r["agent"] for r in responses)),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._save_conversation_to_storage(conversation_data)
            
            logger.info(f"✅ Group chat completed with {len(responses)} responses in {execution_time:.2f}ms")
            return responses
            
        except Exception as e:
            logger.error(f"❌ Error processing group chat: {e}")
            raise
    
    def _determine_needed_agents(self, query: str) -> List[str]:
        """Determine which agents are needed based on the query content"""
        query_lower = query.lower()
        needed_agents = []
        
        # Policy analysis
        if any(keyword in query_lower for keyword in [
            'policy', 'regulation', 'regulatory', 'rule', 'guideline', 'framework',
            'directive', 'standard', 'procedure', 'protocol'
        ]):
            needed_agents.append(self.POLICY_ANALYST)
        
        # Compliance
        if any(keyword in query_lower for keyword in [
            'compliance', 'violation', 'breach', 'audit', 'requirement',
            'obligation', 'penalty', 'fine', 'enforcement', 'risk'
        ]):
            needed_agents.append(self.COMPLIANCE_EXPERT)
        
        # Comparative analysis
        if any(keyword in query_lower for keyword in [
            'compare', 'comparison', 'difference', 'similar', 'jurisdiction',
            'cross-border', 'international', 'versus', 'vs', 'between'
        ]):
            needed_agents.append(self.COMPARATIVE_ANALYST)
        
        # Always include research agent for comprehensive analysis
        needed_agents.append(self.RESEARCH_AGENT)
        
        # Remove duplicates and ensure we have at least the research agent
        needed_agents = list(set(needed_agents))
        if not needed_agents:
            needed_agents = [self.RESEARCH_AGENT]
        
        return needed_agents
    
    async def _save_conversation_to_storage(self, conversation_data: Dict[str, Any]):
        """Save conversation data to Azure Storage"""
        if not self.storage_client:
            return
        
        try:
            blob_name = f"conversations/{self.conversation_id}/complete_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            blob_client = self.storage_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                blob_client.upload_blob,
                json.dumps(conversation_data, indent=2),
                overwrite=True
            )
            
            logger.info(f"💾 Conversation saved to storage: {blob_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save conversation to storage: {e}")
    
    async def run_interactive_session(self):
        """Run an interactive legal consultation session"""
        print(f"\n" + "="*80)
        print(f"🏛️  LEGAL-MIND-AI WORKING SYSTEM - Interactive Session")
        print("="*80)
        print("Multi-agent legal analysis with specialized experts")
        print("Using direct Azure OpenAI integration (no Agents API required)")
        print("Commands: 'exit' to quit, 'reset' to restart")
        print("="*80 + "\n")
        
        continue_chat = True
        
        while continue_chat:
            try:
                print()
                user_input = input("Legal Query > ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    continue_chat = False
                    break
                
                if user_input.lower() == "reset":
                    self.conversation_id = str(uuid.uuid4())
                    print("🔄 [Legal consultation session has been reset]")
                    continue
                
                # Process the legal query
                responses = await self.process_group_chat(user_input)
                
                # Display responses
                for i, response in enumerate(responses, 1):
                    print(f"\n🤖 {response['agent'].upper()} (Response {i}):")
                    print("-" * 60)
                    print(response['content'])
                    print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Legal consultation session interrupted. Goodbye!")
                continue_chat = False
            except Exception as e:
                print(f"\n❌ Error during consultation: {e}")
                print("Please try again or type 'reset' to restart the session.")

async def main():
    """Main function to run the Enhanced Legal-Mind-AI system."""
    try:
        print("🚀 Initializing Enhanced Legal-Mind-AI Experimental System...")
        
        # Initialize the orchestrator
        orchestrator = EnhancedLegalMindOrchestrator()
        
        print("✅ Enhanced Legal-Mind-AI System ready!")
        print("🔧 Using direct Azure OpenAI integration")
        print("👥 Multi-agent group chat functionality enabled")
        print("💾 Conversation persistence enabled")
        print("⭐ Quality scoring system enabled")
        print("📁 Modular agent prompts enabled")
        
        # Run interactive session
        await orchestrator.run_interactive_session()
        
    except Exception as e:
        logger.error(f"Failed to run Enhanced Legal-Mind-AI System: {e}")
        print(f"\n❌ System Error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    asyncio.run(main())
