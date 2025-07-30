#!/usr/bin/env python3
"""
Legal Mind Teams Bot Implementation

Teams-specific bot implementation with enhanced messaging patterns,
suggested actions, and proper Bot Framework integration.
"""

import logging
from typing import List, Tuple
from datetime import datetime

from botbuilder.core import (
    ActivityHandler, 
    TurnContext, 
    MessageFactory,
    CardAction,
    ActionTypes,
    Activity,
    ActivityTypes
)
from botbuilder.schema import (
    ChannelAccount,
    SuggestedActions
)

from ..orchestrator.thread_session import get_thread_session
from ..agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

class LegalMindTeamsBot(ActivityHandler):
    """
    Legal Mind Teams Bot with specialized agent coordination
    
    Enhanced Teams integration with:
    - Proper message handling patterns
    - Suggested actions for UX
    - Typing indicators for responsiveness
    - Multi-agent routing and coordination
    """
    
    def __init__(self):
        """Initialize the Legal Mind Teams bot"""
        super().__init__()
        self.agent_registry = AgentRegistry()
        logger.info("Legal Mind Teams Bot initialized with agent registry")
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """
        Handle incoming Teams messages with enhanced patterns
        
        Implements proper Teams integration:
        1. Send typing indicator for responsiveness
        2. Process query through specialized agents
        3. Return formatted response with suggested actions
        """
        try:
            # Send typing indicator to show bot is processing
            await self._send_typing_indicator(turn_context)
            
            # Get user message
            user_message = turn_context.activity.text
            logger.info(f"Processing Teams message: {user_message[:100]}...")
            
            # Process through agent coordination
            response_text, suggested_actions = await self.process_legal_query(user_message)
            
            # Create response with suggested actions
            response_activity = MessageFactory.text(response_text)
            if suggested_actions:
                response_activity.suggested_actions = SuggestedActions(actions=suggested_actions)
            
            # Send response
            await turn_context.send_activity(response_activity)
            
        except Exception as e:
            logger.error(f"Error processing Teams message: {e}")
            error_message = (
                "⚠️ I apologize, but I encountered an error while processing your request. "
                "Please try again or contact support if the issue persists.\\n\\n"
                "📖 **Research Disclaimer:** This system is for research and educational purposes only. "
                "For production legal matters, please consult qualified legal professionals."
            )
            await turn_context.send_activity(MessageFactory.text(error_message))
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ) -> None:
        """
        Send welcome message when new members join Teams conversation
        
        Enhanced welcome with:
        - Clear capability explanation
        - Suggested actions for quick start
        - Research disclaimer
        """
        welcome_text = (
            "🤖⚖️ **Welcome to Legal Mind Agent!**\\n\\n"
            "I'm your AI Policy Expert for Regulatory Compliance, powered by Microsoft's AI platform. "
            "I coordinate specialized agents to provide citation-rich compliance guidance:\\n\\n"
            "🔧 **Specialized AI Policy Agents:**\\n"
            "• **Regulation Analysis** - AI regulation ingestion & framework analysis\\n"
            "• **Risk Scoring** - Compliance risk assessment & scoring\\n"
            "• **Compliance Expert** - Regulatory compliance & audit preparation\\n"
            "• **Policy Translation** - Complex regulation interpretation\\n"
            "• **Comparative Regulatory** - Cross-jurisdictional analysis\\n\\n"
            "⚠️ **Research Purpose Only**: This solution is for research and educational purposes. "
            "Always consult qualified legal professionals for compliance decisions.\\n\\n"
            "*What regulatory compliance matter can I help you with today?*"
        )
        
        # Create suggested actions for quick start
        suggested_actions = [
            CardAction(
                type=ActionTypes.im_back,
                title="🔍 Analyze EU AI Act",
                value="Analyze EU AI Act requirements for our chatbot"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="📊 Risk Assessment",
                value="Score compliance risk for facial recognition deployment"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="✅ GDPR Compliance",
                value="GDPR compliance checklist for AI data processing"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="🌍 Compare Regulations",
                value="Compare US vs EU AI governance requirements"
            )
        ]
        
        welcome_activity = MessageFactory.text(welcome_text)
        welcome_activity.suggested_actions = SuggestedActions(actions=suggested_actions)
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(welcome_activity)
    
    async def _send_typing_indicator(self, turn_context: TurnContext) -> None:
        """Send typing indicator to show bot is processing"""
        try:
            typing_activity = Activity(
                type=ActivityTypes.typing,
                relates_to=turn_context.activity.relates_to
            )
            await turn_context.send_activity(typing_activity)
        except Exception as e:
            logger.warning(f"Could not send typing indicator: {e}")
    
    async def process_legal_query(self, user_message: str) -> Tuple[str, List[CardAction]]:
        """
        Process legal queries through specialized agent coordination
        
        Args:
            user_message: User's query text
            
        Returns:
            Tuple of (response_text, suggested_actions)
        """
        if not user_message:
            return self._get_help_message()
        
        # Analyze query intent and route to appropriate agents
        query_intent = self._analyze_query_intent(user_message)
        
        # Route to specialized AI policy agents
        if query_intent == "regulation":
            return await self._handle_regulation_analysis(user_message)
        elif query_intent == "risk":
            return await self._handle_risk_scoring(user_message)
        elif query_intent == "compliance":
            return await self._handle_compliance_query(user_message)
        elif query_intent == "policy":
            return await self._handle_policy_translation(user_message)
        elif query_intent == "comparative":
            return await self._handle_comparative_analysis(user_message)
        elif query_intent == "greeting":
            return self._get_greeting_response()
        else:
            return await self._handle_general_legal_query(user_message)
    
    def _analyze_query_intent(self, message: str) -> str:
        """Analyze user query to determine appropriate specialized AI policy agent"""
        message_lower = message.lower()
        
        # Regulation analysis keywords
        if any(keyword in message_lower for keyword in [
            'regulation', 'ai act', 'gdpr', 'ccpa', 'nist', 'framework', 'law', 'statute'
        ]):
            return "regulation"
        
        # Risk scoring keywords
        elif any(keyword in message_lower for keyword in [
            'risk', 'score', 'assessment', 'evaluate', 'facial recognition', 'biometric'
        ]):
            return "risk"
        
        # Compliance keywords
        elif any(keyword in message_lower for keyword in [
            'compliance', 'checklist', 'audit', 'requirement', 'data processing', 'privacy'
        ]):
            return "compliance"
        
        # Policy translation keywords
        elif any(keyword in message_lower for keyword in [
            'translate', 'explain', 'implementation', 'steps', 'guidance', 'interpret'
        ]):
            return "policy"
        
        # Comparative analysis keywords
        elif any(keyword in message_lower for keyword in [
            'compare', 'difference', 'versus', 'vs', 'between', 'jurisdiction', 'us vs eu'
        ]):
            return "comparative"
        
        # Greeting keywords
        elif any(keyword in message_lower for keyword in [
            'hello', 'hi', 'hey', 'help', 'what can you do'
        ]):
            return "greeting"
        
        return "general"
    
    async def _handle_regulation_analysis(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle regulation analysis queries"""
        response = (
            f"📋 **Regulation Analysis Agent**\\n\\n"
            f"**Query:** {message}\\n\\n"
            f"**Analysis Framework:** I specialize in AI regulation ingestion and framework analysis:\\n\\n"
            f"• **EU AI Act** - High-risk AI system classifications and requirements\\n"
            f"• **GDPR/CCPA** - Data protection and privacy regulations for AI\\n"
            f"• **NIST AI Framework** - Risk management and governance standards\\n"
            f"• **Sectoral Regulations** - Industry-specific AI compliance requirements\\n\\n"
            f"📖 **Research Disclaimer:** This analysis is for research and educational purposes only. "
            f"Always consult qualified legal professionals for compliance decisions.\\n\\n"
            f"*Please specify the regulation and your AI system for detailed analysis.*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🇪🇺 EU AI Act Details", value="Explain EU AI Act high-risk categories"),
            CardAction(type=ActionTypes.im_back, title="🛡️ GDPR for AI", value="GDPR requirements for AI data processing"),
            CardAction(type=ActionTypes.im_back, title="📊 NIST Framework", value="NIST AI Risk Management Framework overview")
        ]
        
        return response, suggested_actions
    
    async def _handle_risk_scoring(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle risk scoring queries"""
        response = (
            f"🔍 **Risk Scoring Agent**\\n\\n"
            f"**Query:** {message}\\n\\n"
            f"**Risk Assessment Framework:** I provide compliance risk assessment and scoring:\\n\\n"
            f"• **High-Risk AI Classification** - EU AI Act risk category assessment\\n"
            f"• **Data Protection Risk** - GDPR/CCPA privacy impact scoring\\n"
            f"• **Algorithmic Bias Risk** - Fairness and discrimination assessment\\n"
            f"• **Transparency Requirements** - Explainability and disclosure obligations\\n\\n"
            f"📖 **Research Disclaimer:** Risk scores are for research purposes only. "
            f"Professional legal review required for production deployments.\\n\\n"
            f"*Describe your AI system for comprehensive risk scoring.*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🎯 High-Risk Assessment", value="Is my AI system high-risk under EU AI Act?"),
            CardAction(type=ActionTypes.im_back, title="⚖️ Bias Risk Check", value="Assess algorithmic bias risk for hiring AI"),
            CardAction(type=ActionTypes.im_back, title="🔒 Privacy Impact", value="GDPR privacy impact assessment for AI")
        ]
        
        return response, suggested_actions
    
    async def _handle_compliance_query(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle compliance-related queries"""
        response = (
            f"✅ **Compliance Expert Agent**\\n\\n"
            f"**Query:** {message}\\n\\n"
            f"**Compliance Framework:** I provide regulatory compliance and audit preparation:\\n\\n"
            f"• **Compliance Checklists** - Step-by-step regulatory requirements\\n"
            f"• **Audit Preparation** - Documentation and evidence requirements\\n"
            f"• **Implementation Roadmaps** - Practical compliance deployment guides\\n"
            f"• **Monitoring & Reporting** - Ongoing compliance maintenance\\n\\n"
            f"📖 **Research Disclaimer:** Compliance guidance is for educational purposes. "
            f"Engage qualified legal counsel for production compliance programs.\\n\\n"
            f"*What specific compliance requirements do you need guidance on?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="📋 GDPR Checklist", value="GDPR compliance checklist for AI systems"),
            CardAction(type=ActionTypes.im_back, title="📄 Documentation Guide", value="Required documentation for AI Act compliance"),
            CardAction(type=ActionTypes.im_back, title="🔍 Audit Preparation", value="Prepare for AI compliance audit")
        ]
        
        return response, suggested_actions
    
    async def _handle_policy_translation(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle policy translation queries"""
        response = (
            f"📖 **Policy Translation Agent**\\n\\n"
            f"**Query:** {message}\\n\\n"
            f"**Translation Framework:** I translate complex regulations into actionable guidance:\\n\\n"
            f"• **Plain Language Translation** - Converting legal text to clear requirements\\n"
            f"• **Implementation Steps** - Practical action items from regulatory text\\n"
            f"• **Technical Mapping** - Linking regulations to technical implementations\\n"
            f"• **Best Practices** - Industry-standard approaches to compliance\\n\\n"
            f"📖 **Research Disclaimer:** Translations are for research and educational purposes. "
            f"Original regulatory text and legal counsel remain authoritative.\\n\\n"
            f"*Which regulation would you like me to translate into actionable steps?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔧 NIST Implementation", value="Translate NIST AI framework into implementation steps"),
            CardAction(type=ActionTypes.im_back, title="📐 EU AI Act Guide", value="Convert EU AI Act requirements to technical specs"),
            CardAction(type=ActionTypes.im_back, title="🛡️ Privacy by Design", value="Implement GDPR privacy by design principles")
        ]
        
        return response, suggested_actions
    
    async def _handle_comparative_analysis(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle comparative regulatory analysis"""
        response = (
            f"⚖️ **Comparative Regulatory Agent**\\n\\n"
            f"**Query:** {message}\\n\\n"
            f"**Comparative Framework:** I analyze regulatory differences across jurisdictions:\\n\\n"
            f"• **Cross-Jurisdictional Mapping** - US vs EU vs Asia-Pacific AI regulations\\n"
            f"• **Harmonization Analysis** - Common principles and divergent approaches\\n"
            f"• **Global Compliance Strategy** - Multi-jurisdiction deployment guidance\\n"
            f"• **Regulatory Trends** - Emerging patterns in AI governance\\n\\n"
            f"📖 **Research Disclaimer:** Comparative analysis is for research purposes. "
            f"Jurisdiction-specific legal advice required for global deployments.\\n\\n"
            f"*Which jurisdictions would you like me to compare for your AI system?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🌍 US vs EU AI Laws", value="Compare US and EU AI governance requirements"),
            CardAction(type=ActionTypes.im_back, title="🔄 Global Harmonization", value="Common AI principles across jurisdictions"),
            CardAction(type=ActionTypes.im_back, title="📈 Regulatory Trends", value="Emerging AI regulation trends globally")
        ]
        
        return response, suggested_actions
    
    async def _handle_general_legal_query(self, message: str) -> Tuple[str, List[CardAction]]:
        """Handle general legal queries"""
        response = (
            f"🤖⚖️ **Legal Mind Agent**\\n\\n"
            f"**Your Question:** {message}\\n\\n"
            f"**AI Policy Expertise:** I specialize in regulatory compliance for AI systems. "
            f"For the most accurate analysis, please specify:\\n\\n"
            f"• **AI System Type** - Chatbot, facial recognition, hiring algorithm, etc.\\n"
            f"• **Jurisdiction** - EU, US, California, UK, etc.\\n"
            f"• **Regulatory Focus** - EU AI Act, GDPR, CCPA, NIST framework\\n"
            f"• **Use Case** - Risk assessment, compliance checklist, implementation guide\\n\\n"
            f"📖 **Research Disclaimer:** This system provides research and educational guidance only. "
            f"Professional legal counsel required for production compliance decisions.\\n\\n"
            f"*How can I assist with your AI regulatory compliance needs?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔍 Regulation Analysis", value="Analyze EU AI Act requirements"),
            CardAction(type=ActionTypes.im_back, title="📊 Risk Assessment", value="Score compliance risk for my AI system"),
            CardAction(type=ActionTypes.im_back, title="✅ Compliance Guide", value="Create compliance checklist"),
            CardAction(type=ActionTypes.im_back, title="🌍 Compare Laws", value="Compare AI regulations across jurisdictions")
        ]
        
        return response, suggested_actions
    
    def _get_greeting_response(self) -> Tuple[str, List[CardAction]]:
        """Return greeting response with suggested actions"""
        response = (
            "👋 **Hello! I'm Legal Mind Agent**\\n\\n"
            "I'm your AI Policy Expert for Regulatory Compliance, specializing in:\\n\\n"
            "🔧 **Specialized AI Policy Agents:**\\n"
            "• **Regulation Analysis** - AI regulation framework analysis\\n"
            "• **Risk Scoring** - Compliance risk assessment & scoring\\n"
            "• **Compliance Expert** - Regulatory compliance & audit prep\\n"
            "• **Policy Translation** - Converting regulations to action items\\n"
            "• **Comparative Regulatory** - Cross-jurisdictional analysis\\n\\n"
            "📖 **Research Purpose Only** - Educational guidance, not legal advice.\\n\\n"
            "*What AI regulatory compliance matter can I help you with?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🇪🇺 EU AI Act", value="Analyze EU AI Act requirements for chatbot"),
            CardAction(type=ActionTypes.im_back, title="🔍 Risk Score", value="Score compliance risk for facial recognition"),
            CardAction(type=ActionTypes.im_back, title="✅ GDPR Compliance", value="GDPR compliance checklist for AI"),
            CardAction(type=ActionTypes.im_back, title="🌍 Compare Regs", value="Compare US vs EU AI governance")
        ]
        
        return response, suggested_actions
    
    def _get_help_message(self) -> Tuple[str, List[CardAction]]:
        """Return help message for empty queries"""
        response = (
            "🤖⚖️ **Welcome to Legal Mind Agent!**\\n\\n"
            "I'm your AI Policy Expert ready to help with regulatory compliance. "
            "I coordinate specialized agents for:\\n\\n"
            "• Regulation analysis and framework interpretation\\n"
            "• Risk assessment and compliance scoring\\n"
            "• Compliance checklists and audit preparation\\n"
            "• Policy translation and implementation guidance\\n"
            "• Comparative regulatory analysis\\n\\n"
            "📖 **Research Purpose Only** - This is educational guidance, not legal advice.\\n\\n"
            "*How can I assist with your AI regulatory compliance needs today?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔍 Start Analysis", value="Analyze regulations for my AI system"),
            CardAction(type=ActionTypes.im_back, title="📊 Risk Assessment", value="Assess compliance risks"),
            CardAction(type=ActionTypes.im_back, title="✅ Get Checklist", value="Create compliance checklist"),
            CardAction(type=ActionTypes.im_back, title="❓ Learn More", value="What can Legal Mind Agent do?")
        ]
        
        return response, suggested_actions
