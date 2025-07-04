"""
Legal-Mind-AI Semantic Kernel Orchestrator
Enhanced agent orchestration using Microsoft Semantic Kernel
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog

# Simplified Semantic Kernel imports for compatibility
import semantic_kernel as sk
from semantic_kernel.functions import KernelArguments, kernel_function

# Import existing services
from services.news_service import NewsMonitorService
from services.search_service import SearchService, SearchType
from services.email_service import EmailService
from services.pdf_generator import LegalMindReportGenerator

# Import legacy orchestrator components
from agents.orchestrator import AgentType, QueryContext, AgentResponse

logger = structlog.get_logger(__name__)

class LegalMindSemanticKernel:
    """
    Enhanced Legal-Mind-AI orchestrator using Microsoft Semantic Kernel
    """
    
    def __init__(self):
        self.kernel = sk.Kernel()
        self.search_service = SearchService()
        self.news_service = NewsMonitorService()
        self.email_service = EmailService()
        self.pdf_generator = LegalMindReportGenerator()
        
        # Initialize kernel
        self._initialize_kernel()
        self._register_plugins()
        
        logger.info("Semantic Kernel orchestrator initialized")
    
    def _initialize_kernel(self):
        """Initialize the Semantic Kernel"""
        try:
            # For now, we'll use the kernel without external AI services
            # and rely on our existing Azure AI Projects integration
            logger.info("Kernel initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize kernel", error=str(e))
    
    def _register_plugins(self):
        """Register custom Legal-Mind plugins"""
        try:
            # Register custom plugins
            self.kernel.add_plugin(LegalSearchPlugin(self.search_service), plugin_name="LegalSearch")
            self.kernel.add_plugin(NewsMonitorPlugin(self.news_service), plugin_name="NewsMonitor")
            self.kernel.add_plugin(PolicyExpertPlugin(), plugin_name="PolicyExpert")
            self.kernel.add_plugin(ReportGeneratorPlugin(self.pdf_generator, self.email_service), plugin_name="ReportGenerator")
            
            logger.info("Custom plugins registered successfully")
            
        except Exception as e:
            logger.error("Failed to register plugins", error=str(e))
    
    async def process_query(self, context: QueryContext) -> str:
        """
        Process a user query using Semantic Kernel orchestration
        """
        try:
            logger.info("Processing query with Semantic Kernel", 
                       query=context.query, user_id=context.user_id)
            
            # Analyze query to determine required plugins
            plan = await self._create_execution_plan(context.query)
            
            logger.info("Query plan generated", plan=plan[:200] if isinstance(plan, str) else str(plan)[:200])
            
            # Execute the plan
            response = await self._execute_plan(plan, context)
            
            return response
            
        except Exception as e:
            logger.error("Error processing query", error=str(e))
            return f"❌ I encountered an error processing your request: {str(e)}"
    
    async def _create_execution_plan(self, query: str) -> Dict[str, Any]:
        """Create an execution plan for the query"""
        plan = {
            "query": query,
            "plugins_needed": [],
            "query_type": "general",
            "requires_real_time": False
        }
        
        query_lower = query.lower()
        
        # Analyze query to determine required plugins
        if any(keyword in query_lower for keyword in ["news", "latest", "recent", "current", "update"]):
            plan["plugins_needed"].append("NewsMonitor")
            plan["query_type"] = "news"
            plan["requires_real_time"] = True
        
        if any(keyword in query_lower for keyword in ["policy", "regulation", "compliance", "act", "framework", "gdpr", "nist", "eu ai"]):
            plan["plugins_needed"].append("PolicyExpert")
            plan["query_type"] = "policy"
        
        if any(keyword in query_lower for keyword in ["search", "find", "lookup", "document"]):
            plan["plugins_needed"].append("LegalSearch")
        
        if any(keyword in query_lower for keyword in ["report", "pdf", "email", "generate", "create report"]):
            plan["plugins_needed"].append("ReportGenerator")
            plan["query_type"] = "report"
        
        # Default to policy expert if no specific plugins identified
        if not plan["plugins_needed"]:
            plan["plugins_needed"].append("PolicyExpert")
            plan["query_type"] = "policy"
        
        return plan
    
    async def _execute_plan(self, plan: Dict[str, Any], context: QueryContext) -> str:
        """Execute the generated plan using appropriate plugins"""
        try:
            plugins_needed = plan["plugins_needed"]
            results = []
            
            # Execute plugins based on plan
            for plugin_name in plugins_needed:
                try:
                    if plugin_name == "NewsMonitor":
                        result = await self._call_news_monitor(context.query)
                        if result:
                            results.append({"type": "news", "content": result})
                    
                    elif plugin_name == "PolicyExpert":
                        result = await self._call_policy_expert(context.query)
                        if result:
                            results.append({"type": "policy", "content": result})
                    
                    elif plugin_name == "LegalSearch":
                        result = await self._call_legal_search(context.query)
                        if result:
                            results.append({"type": "search", "content": result})
                    
                    elif plugin_name == "ReportGenerator":
                        result = await self._call_report_generator(context, results)
                        return result  # Report generation is usually the final step
                    
                except Exception as e:
                    logger.warning("Plugin execution failed", plugin=plugin_name, error=str(e))
                    continue
            
            # Combine results
            if results:
                return await self._synthesize_results(results, context, plan)
            else:
                return "❌ I wasn't able to process your query. Please try rephrasing or ask about specific AI policy topics."
            
        except Exception as e:
            logger.error("Plan execution failed", error=str(e))
            return f"❌ Error executing query plan: {str(e)}"
    
    async def _call_news_monitor(self, query: str) -> str:
        """Call the news monitoring plugin"""
        try:
            news_response = await self.search_service.search(
                query, 
                SearchType.NEWS_SEARCH, 
                max_results=5
            )
            
            if not news_response.results:
                return None
            
            response = f"📰 **Latest News: {query}**\n\n"
            
            for i, result in enumerate(news_response.results, 1):
                response += f"**{i}. {result.title}**\n"
                response += f"*Source: {result.source}*\n"
                response += f"{result.content[:200]}...\n"
                if result.url:
                    response += f"🔗 [Read more]({result.url})\n"
                response += "\n---\n\n"
            
            return response
            
        except Exception as e:
            logger.error("News monitor plugin failed", error=str(e))
            return None
    
    async def _call_policy_expert(self, query: str) -> str:
        """Call the policy expert plugin using our existing orchestrator"""
        try:
            # Use the existing orchestrator's expertise for policy analysis
            from agents.orchestrator import orchestrator
            
            # Create a context for the legacy orchestrator
            temp_context = QueryContext(
                user_id="semantic_kernel_user",
                query=query,
                priority="normal",
                output_format="text"
            )
            
            # Get basic query response from existing system
            response = await orchestrator.process_query(temp_context)
            return response
            
        except Exception as e:
            logger.error("Policy expert plugin failed", error=str(e))
            # Fallback to basic response
            return f"""
📋 **AI Policy Analysis for: {query}**

I can help you with AI governance and policy questions including:

**Key Regulations:**
• **EU AI Act**: Comprehensive AI regulation framework
• **NIST AI Risk Management Framework**: US guidance for AI systems
• **GDPR**: Privacy implications for AI systems

**Common Compliance Areas:**
• Risk assessment and classification
• Data governance and privacy
• Algorithm transparency and explainability
• Human oversight requirements
• Documentation and record-keeping

For more specific guidance, please ask about particular regulations or use cases.
"""
    
    async def _call_legal_search(self, query: str) -> str:
        """Call the legal search plugin"""
        try:
            search_response = await self.search_service.search(
                query,
                SearchType.WEB_SEARCH,
                max_results=3
            )
            
            if not search_response.results:
                return None
            
            response = f"🔍 **Search Results: {query}**\n\n"
            
            for i, result in enumerate(search_response.results, 1):
                response += f"**{i}. {result.title}**\n"
                response += f"*Source: {result.source}*\n"
                response += f"{result.content[:300]}...\n"
                if result.url:
                    response += f"🔗 [Source]({result.url})\n"
                response += "\n"
            
            return response
            
        except Exception as e:
            logger.error("Legal search plugin failed", error=str(e))
            return None
    
    async def _call_report_generator(self, context: QueryContext, results: List[Dict[str, Any]]) -> str:
        """Call the report generator plugin"""
        try:
            report_content = self._compile_report_content(results, context.query)
            
            if context.output_format == "pdf":
                # Generate PDF report
                pdf_path = await self.pdf_generator.generate_policy_report(
                    title=f"Legal-Mind-AI Analysis: {context.query[:50]}...",
                    content=report_content,
                    user_id=context.user_id
                )
                
                if context.email_address:
                    # Send via email
                    await self.email_service.send_report_email(
                        context.email_address,
                        f"Legal-Mind-AI Report: {context.query[:30]}...",
                        report_content,
                        pdf_path
                    )
                    return f"📧 Report generated and sent to {context.email_address}"
                else:
                    return f"📄 Report generated: {pdf_path}"
            else:
                return report_content
                
        except Exception as e:
            logger.error("Report generator plugin failed", error=str(e))
            return "❌ Unable to generate report at the moment."
    
    def _compile_report_content(self, results: List[Dict[str, Any]], query: str) -> str:
        """Compile results into a formatted report"""
        report = f"# Legal-Mind-AI Analysis Report\n\n"
        report += f"**Query:** {query}\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for result in results:
            if result["type"] == "news":
                report += "## Latest News & Developments\n\n"
                report += result["content"] + "\n\n"
            elif result["type"] == "policy":
                report += "## Policy Analysis\n\n"
                report += result["content"] + "\n\n"
            elif result["type"] == "search":
                report += "## Document Search Results\n\n"
                report += result["content"] + "\n\n"
        
        return report
    
    async def _synthesize_results(self, results: List[Dict[str, Any]], context: QueryContext, plan: Dict[str, Any]) -> str:
        """Synthesize multiple plugin results into a coherent response"""
        try:
            # Create a comprehensive response based on the query type
            if plan["query_type"] == "news":
                return self._synthesize_news_response(results, context.query)
            elif plan["query_type"] == "policy":
                return self._synthesize_policy_response(results, context.query)
            elif plan["query_type"] == "report":
                return self._compile_report_content(results, context.query)
            else:
                return self._synthesize_general_response(results, context.query)
                
        except Exception as e:
            logger.error("Result synthesis failed", error=str(e))
            # Fallback to simple concatenation
            response = f"# Response to: {context.query}\n\n"
            for result in results:
                response += f"## {result['type'].title()} Information\n\n"
                response += result["content"] + "\n\n"
            return response
    
    def _synthesize_news_response(self, results: List[Dict[str, Any]], query: str) -> str:
        """Synthesize news-focused response"""
        response = f"📰 **Latest AI Policy News**\n\n"
        
        for result in results:
            if result["type"] == "news":
                response += result["content"]
            elif result["type"] == "policy":
                response += "\n## 📋 **Policy Context**\n\n"
                response += result["content"]
        
        response += "\n\n---\n*Stay updated with Legal-Mind-AI for the latest in AI governance and policy.*"
        return response
    
    def _synthesize_policy_response(self, results: List[Dict[str, Any]], query: str) -> str:
        """Synthesize policy-focused response"""
        response = f"📋 **AI Policy Analysis: {query}**\n\n"
        
        for result in results:
            if result["type"] == "policy":
                response += result["content"]
            elif result["type"] == "search":
                response += "\n## 📚 **Additional Resources**\n\n"
                response += result["content"]
            elif result["type"] == "news":
                response += "\n## 📰 **Latest Developments**\n\n"
                response += result["content"]
        
        return response
    
    def _synthesize_general_response(self, results: List[Dict[str, Any]], query: str) -> str:
        """Synthesize general response"""
        response = f"🤖 **Legal-Mind-AI Analysis**\n\n"
        
        for result in results:
            response += f"## {result['type'].title()}\n\n"
            response += result["content"] + "\n\n"
        
        return response


# Custom Semantic Kernel Plugins

class LegalSearchPlugin:
    """Plugin for legal document and policy search"""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
    
    @kernel_function(description="Search legal documents and policies")
    async def search_documents(self, query: str, search_type: str = "mixed") -> str:
        """Search for legal documents and policies"""
        return f"Legal search initiated for: {query}"


class NewsMonitorPlugin:
    """Plugin for AI policy news monitoring"""
    
    def __init__(self, news_service: NewsMonitorService):
        self.news_service = news_service
    
    @kernel_function(description="Get latest AI policy news")
    async def get_latest_news(self, query: str, hours_back: int = 24) -> str:
        """Get the latest AI policy news"""
        return f"News search initiated for: {query}"


class PolicyExpertPlugin:
    """Plugin for AI policy expert analysis"""
    
    @kernel_function(description="Provide expert AI policy analysis")
    async def analyze_policy(self, query: str) -> str:
        """Analyze AI policy and provide expert guidance"""
        return f"Policy analysis initiated for: {query}"


class ReportGeneratorPlugin:
    """Plugin for generating reports and documents"""
    
    def __init__(self, pdf_generator: LegalMindReportGenerator, email_service: EmailService):
        self.pdf_generator = pdf_generator
        self.email_service = email_service
    
    @kernel_function(description="Generate and deliver reports")
    async def generate_report(self, content: str, format: str = "text") -> str:
        """Generate reports in various formats"""
        return f"Report generation initiated: {format}"


# Global instance
semantic_orchestrator = LegalMindSemanticKernel()
