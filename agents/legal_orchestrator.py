"""
Legal-Mind-AI Multi-Agent Orchestrator
Based on Azure AI Foundry healthcare orchestrator pattern
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog

# Semantic Kernel imports
import semantic_kernel as sk
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Import configuration and services
from config import settings
from agents.orchestrator import QueryContext, AgentResponse

logger = structlog.get_logger(__name__)

@dataclass
class AgentConfig:
    """Configuration for a specialized agent"""
    agent_id: str
    name: str
    description: str
    specialization: List[str]
    fallback_agent_id: Optional[str] = None

class LegalAgentType(Enum):
    """Types of legal agents available"""
    POLICY_EXPERT = "policy_expert"
    NEWS_MONITOR = "news_monitor"
    DOCUMENT_ANALYZER = "document_analyzer"
    REPORT_GENERATOR = "report_generator"
    COORDINATOR = "coordinator"

class LegalMindOrchestrator:
    """
    Multi-agent orchestrator for Legal-Mind-AI
    Based on Azure AI Foundry healthcare orchestrator pattern
    """
    
    def __init__(self):
        self.kernel = sk.Kernel()
        self.agents: Dict[str, AgentConfig] = {}
        self._initialize_kernel()
        self._configure_agents()
        self._register_plugins()
        
        logger.info("Legal-Mind orchestrator initialized", 
                   agents=list(self.agents.keys()))
    
    def _initialize_kernel(self):
        """Initialize Semantic Kernel with Azure AI services"""
        try:
            # For now, we'll use the existing orchestrator as the backend
            # In Phase 2, we'll integrate with actual Azure AI services
            logger.info("Kernel initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize kernel", error=str(e))
            raise
    
    def _configure_agents(self):
        """Configure specialized legal agents"""
        
        # Get agent configurations from environment
        agent_configs = settings.get_agent_configs()
        main_agent_id = settings.azure.agent_id
        
        # Policy Expert Agent
        self.agents[LegalAgentType.POLICY_EXPERT.value] = AgentConfig(
            agent_id=agent_configs.get("policy_expert") or main_agent_id,
            name="Policy Expert",
            description="Specialized in AI policy, regulations, and compliance guidance",
            specialization=["eu ai act", "nist", "gdpr", "policy", "regulation", "compliance", "framework"],
            fallback_agent_id=main_agent_id
        )
        
        # News Monitor Agent
        self.agents[LegalAgentType.NEWS_MONITOR.value] = AgentConfig(
            agent_id=agent_configs.get("news_monitor") or main_agent_id,
            name="News Monitor",
            description="Tracks latest AI policy news and regulatory updates",
            specialization=["news", "latest", "recent", "current", "update", "development"],
            fallback_agent_id=main_agent_id
        )
        
        # Document Analyzer Agent
        self.agents[LegalAgentType.DOCUMENT_ANALYZER.value] = AgentConfig(
            agent_id=agent_configs.get("document_analyzer") or main_agent_id,
            name="Document Analyzer",
            description="Analyzes legal documents and policy texts",
            specialization=["document", "analyze", "review", "search", "find", "lookup"],
            fallback_agent_id=main_agent_id
        )
        
        # Report Generator Agent
        self.agents[LegalAgentType.REPORT_GENERATOR.value] = AgentConfig(
            agent_id=agent_configs.get("report_generator") or main_agent_id,
            name="Report Generator",
            description="Generates compliance reports and documentation",
            specialization=["report", "generate", "create report", "pdf", "email", "summary"],
            fallback_agent_id=main_agent_id
        )
        
        logger.info("Agents configured", 
                   agent_count=len(self.agents),
                   main_agent=main_agent_id)
    
    def _register_plugins(self):
        """Register Semantic Kernel plugins"""
        try:
            # Register orchestration plugins
            self.kernel.add_plugin(
                LegalRoutingPlugin(self.agents), 
                plugin_name="LegalRouting"
            )
            self.kernel.add_plugin(
                AgentExecutionPlugin(self), 
                plugin_name="AgentExecution"
            )
            
            logger.info("Plugins registered successfully")
            
        except Exception as e:
            logger.error("Failed to register plugins", error=str(e))
    
    async def process_query(self, context: QueryContext) -> str:
        """
        Process user query using multi-agent orchestration
        """
        try:
            logger.info("Processing query", 
                       query=context.query[:100], 
                       user_id=context.user_id)
            
            # Step 1: Route query to appropriate agent(s)
            routing_decision = await self._route_query(context.query)
            
            # Step 2: Execute with selected agent(s)
            response = await self._execute_with_agents(routing_decision, context)
            
            # Step 3: Format and return response
            formatted_response = self._format_response(response, context)
            
            logger.info("Query processed successfully", 
                       agent_used=routing_decision.get("primary_agent"),
                       response_length=len(formatted_response))
            
            return formatted_response
            
        except Exception as e:
            logger.error("Error processing query", error=str(e))
            return self._generate_error_response(str(e))
    
    async def _route_query(self, query: str) -> Dict[str, Any]:
        """Route query to appropriate agent(s) based on content analysis"""
        
        query_lower = query.lower()
        agent_scores = {}
        
        # Score each agent based on keyword matching
        for agent_type, agent_config in self.agents.items():
            score = 0
            for keyword in agent_config.specialization:
                if keyword in query_lower:
                    score += 1
            agent_scores[agent_type] = score
        
        # Determine primary and secondary agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        routing_decision = {
            "primary_agent": sorted_agents[0][0] if sorted_agents[0][1] > 0 else LegalAgentType.POLICY_EXPERT.value,
            "confidence": sorted_agents[0][1] if sorted_agents else 0,
            "query_type": self._classify_query_type(query_lower),
            "requires_multi_agent": self._requires_multi_agent(query_lower),
            "secondary_agents": [agent for agent, score in sorted_agents[1:3] if score > 0]
        }
        
        logger.info("Query routed", 
                   primary_agent=routing_decision["primary_agent"],
                   confidence=routing_decision["confidence"],
                   query_type=routing_decision["query_type"])
        
        return routing_decision
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query for better processing"""
        if any(word in query for word in ["news", "latest", "recent", "current"]):
            return "news_inquiry"
        elif any(word in query for word in ["report", "generate", "create", "pdf"]):
            return "report_request"
        elif any(word in query for word in ["search", "find", "lookup", "document"]):
            return "document_search"
        elif any(word in query for word in ["policy", "regulation", "compliance", "act", "framework"]):
            return "policy_guidance"
        else:
            return "general_inquiry"
    
    def _requires_multi_agent(self, query: str) -> bool:
        """Determine if query requires multiple agents"""
        multi_agent_indicators = [
            "comprehensive", "detailed report", "analysis and news", 
            "current status", "latest updates on", "full overview"
        ]
        return any(indicator in query for indicator in multi_agent_indicators)
    
    async def _execute_with_agents(self, routing_decision: Dict[str, Any], context: QueryContext) -> Dict[str, Any]:
        """Execute query with selected agent(s)"""
        
        primary_agent_type = routing_decision["primary_agent"]
        primary_agent = self.agents[primary_agent_type]
        
        try:
            # Execute with primary agent
            primary_response = await self._call_agent(primary_agent, context)
            
            result = {
                "primary_response": primary_response,
                "primary_agent": primary_agent_type,
                "secondary_responses": []
            }
            
            # Execute with secondary agents if needed
            if routing_decision["requires_multi_agent"] and routing_decision["secondary_agents"]:
                for secondary_agent_type in routing_decision["secondary_agents"][:2]:  # Limit to 2 secondary
                    secondary_agent = self.agents[secondary_agent_type]
                    try:
                        secondary_response = await self._call_agent(secondary_agent, context)
                        result["secondary_responses"].append({
                            "agent_type": secondary_agent_type,
                            "response": secondary_response
                        })
                    except Exception as e:
                        logger.warning("Secondary agent failed", 
                                     agent=secondary_agent_type, error=str(e))
            
            return result
            
        except Exception as e:
            logger.error("Agent execution failed", 
                        agent=primary_agent_type, error=str(e))
            # Fallback to main agent if configured
            if primary_agent.fallback_agent_id and primary_agent.fallback_agent_id != primary_agent.agent_id:
                fallback_response = await self._call_agent_by_id(primary_agent.fallback_agent_id, context)
                return {
                    "primary_response": fallback_response,
                    "primary_agent": "fallback",
                    "secondary_responses": [],
                    "fallback_used": True
                }
            raise
    
    async def _call_agent(self, agent: AgentConfig, context: QueryContext) -> str:
        """Call a specific agent with the query"""
        return await self._call_agent_by_id(agent.agent_id, context)
    
    async def _call_agent_by_id(self, agent_id: str, context: QueryContext) -> str:
        """Call agent by ID - placeholder for actual Azure AI implementation"""
        
        # For Phase 1, we'll simulate agent responses with fallback to existing orchestrator
        # In Phase 2, this will be replaced with actual Azure AI agent calls
        
        try:
            # Import and use existing orchestrator as fallback
            from agents.orchestrator import orchestrator
            
            # Create a temporary context for the legacy orchestrator
            temp_context = QueryContext(
                user_id=context.user_id,
                query=context.query,
                priority=context.priority,
                output_format=context.output_format
            )
            
            # Get response from existing system
            response = await orchestrator.process_query(temp_context)
            
            logger.info("Agent called successfully", 
                       agent_id=agent_id, 
                       response_length=len(response))
            
            return response
            
        except Exception as e:
            logger.error("Agent call failed", agent_id=agent_id, error=str(e))
            return f"❌ Agent {agent_id} is currently unavailable. Please try again later."
    
    def _format_response(self, result: Dict[str, Any], context: QueryContext) -> str:
        """Format the multi-agent response for display"""
        
        primary_response = result["primary_response"]
        
        # If only primary response, return it directly
        if not result["secondary_responses"]:
            if result.get("fallback_used"):
                return f"🔄 **Response** (via fallback agent)\n\n{primary_response}"
            return primary_response
        
        # Format multi-agent response
        formatted = f"🤖 **Legal-Mind-AI Multi-Agent Analysis**\n\n"
        
        # Add primary response
        agent_name = self.agents[result["primary_agent"]].name
        formatted += f"## 📋 **{agent_name} Analysis**\n\n{primary_response}\n\n"
        
        # Add secondary responses
        for secondary in result["secondary_responses"]:
            agent_name = self.agents[secondary["agent_type"]].name
            formatted += f"## 📚 **{agent_name} Insights**\n\n{secondary['response']}\n\n"
        
        formatted += "---\n*Generated by Legal-Mind-AI Multi-Agent System*"
        
        return formatted
    
    def _generate_error_response(self, error: str) -> str:
        """Generate user-friendly error response"""
        return f"""❌ **I encountered an issue processing your request**

**Error Details:** {error}

**What you can try:**
• Rephrase your question
• Ask about specific AI policies (EU AI Act, NIST Framework, GDPR)
• Use `/help` to see available commands
• Contact support if the issue persists

I'm here to help with AI governance and policy questions! 🤖"""


# Semantic Kernel Plugins

class LegalRoutingPlugin:
    """Plugin for intelligent query routing"""
    
    def __init__(self, agents: Dict[str, AgentConfig]):
        self.agents = agents
    
    @kernel_function(description="Route legal queries to appropriate specialized agents")
    async def route_query(self, query: str) -> str:
        """Route query to the most appropriate agent"""
        return f"Query routed for: {query}"


class AgentExecutionPlugin:
    """Plugin for executing agent workflows"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    @kernel_function(description="Execute multi-agent workflows for complex legal queries")
    async def execute_workflow(self, query: str, workflow_type: str = "standard") -> str:
        """Execute a multi-agent workflow"""
        return f"Workflow executed: {workflow_type} for {query}"


# Global orchestrator instance
legal_orchestrator = LegalMindOrchestrator()
