"""
Legal-Mind-AI Agent Orchestrator
Manages multiple AI agents for legal policy expertise
"""

import os
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import structlog

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder, RunStatus

# Import services for real-time capabilities
from services.news_service import NewsMonitorService
from services.search_service import SearchService, SearchType

logger = structlog.get_logger(__name__)

class AgentType(Enum):
    POLICY_EXPERT = "policy_expert"
    NEWS_MONITOR = "news_monitor"
    DOCUMENT_ANALYZER = "document_analyzer"
    REPORT_GENERATOR = "report_generator"
    ORCHESTRATOR = "orchestrator"

@dataclass
class QueryContext:
    """Context for a user query including routing and collaboration info"""
    user_id: str
    query: str
    thread_id: Optional[str] = None
    required_agents: List[AgentType] = None
    priority: str = "normal"  # low, normal, high, urgent
    output_format: str = "text"  # text, pdf, email
    email_address: Optional[str] = None
    max_response_length: int = 4000  # Maximum response length for Teams
    enable_chunking: bool = True  # Enable response chunking for long responses

@dataclass
class AgentResponse:
    """Response from an individual agent"""
    agent_type: AgentType
    content: str
    confidence: float
    sources: List[str]
    metadata: Dict[str, Any]

class QueryComplexityAnalyzer:
    """Analyzes query complexity and suggests processing strategies"""
    
    @staticmethod
    def analyze_complexity(query: str) -> Dict[str, Any]:
        """Analyze query complexity and return processing recommendations"""
        word_count = len(query.split())
        question_count = query.count('?')
        numbered_points = len([line for line in query.split('\n') if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))])
        
        # Check for multi-part questions (like "A and B?" or "A, and B?")
        has_compound_question = ' and ' in query.lower() and '?' in query
        has_multiple_topics = query.count(',') > 2  # Multiple comma-separated topics
        
        complexity_score = 0
        if word_count > 50:  # Reduced threshold
            complexity_score += 2
        if word_count > 100:
            complexity_score += 2
        if question_count > 1:  # Multiple questions
            complexity_score += 3
        if numbered_points > 2:
            complexity_score += 2
        if has_compound_question:  # Multi-part questions like yours
            complexity_score += 4
        if has_multiple_topics:
            complexity_score += 2
        
        complexity_level = "simple"
        if complexity_score >= 3:
            complexity_level = "moderate"
        if complexity_score >= 6:
            complexity_level = "complex"
        if complexity_score >= 8:
            complexity_level = "very_complex"
        
        return {
            "complexity_level": complexity_level,
            "complexity_score": complexity_score,
            "word_count": word_count,
            "question_count": question_count,
            "numbered_points": numbered_points,
            "has_compound_question": has_compound_question,
            "has_multiple_topics": has_multiple_topics,
            "requires_chunking": complexity_score >= 6,
            "requires_specialized_processing": complexity_score >= 4,
            "estimated_processing_time": min(30 + (complexity_score * 5), 60)  # Reduced max time
        }

class LegalMindOrchestrator:
    """
    Main orchestrator for the Legal-Mind-AI multi-agent system
    Enhanced with complex query handling, retry logic, and response chunking
    """
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.project = AIProjectClient(
            endpoint=os.getenv("AZURE_PROJECT_ENDPOINT"),
            credential=self.credential
        )
        
        # Initialize services
        self.search_service = SearchService()
        self.news_service = NewsMonitorService()  # Keep for backward compatibility
        
        # Agent configurations
        self.agents = {
            AgentType.POLICY_EXPERT: os.getenv("POLICY_EXPERT_AGENT_ID"),
            AgentType.NEWS_MONITOR: os.getenv("NEWS_MONITOR_AGENT_ID"),
            AgentType.DOCUMENT_ANALYZER: os.getenv("DOCUMENT_ANALYZER_AGENT_ID"),
            AgentType.REPORT_GENERATOR: os.getenv("REPORT_GENERATOR_AGENT_ID"),
        }
        
        # Fallback to main agent if specialized agents not configured
        self.main_agent_id = os.getenv("AZURE_AGENT_ID")
        
        # Rate limiting and retry configuration
        self.max_retries = 3
        self.base_retry_delay = 5  # seconds
        self.max_retry_delay = 60  # seconds
        
        # Response chunking configuration
        self.max_chunk_size = 3800  # Leave room for Teams formatting
        
    async def process_query(self, context: QueryContext) -> str:
        """
        Process a user query through the multi-agent system with enhanced handling for complex queries
        """
        logger.info("Processing query", user_id=context.user_id, query=context.query[:100])
        
        try:
            # Check for basic greetings and help requests first
            basic_response = await self._handle_basic_queries(context.query)
            if basic_response:
                return basic_response
            
            # Analyze query complexity
            complexity_analysis = QueryComplexityAnalyzer.analyze_complexity(context.query)
            logger.info("Query complexity analysis", **complexity_analysis, user_id=context.user_id)
            
            # Handle complex queries with special processing
            if complexity_analysis["requires_specialized_processing"]:
                return await self._process_complex_query(context, complexity_analysis)
            
            # 1. Analyze query and determine required agents
            required_agents = await self._analyze_query_requirements(context)
            
            # 2. Execute agents with retry logic
            agent_responses = await self._execute_agents_with_retry(context, required_agents)
            
            # 3. Synthesize responses
            final_response = await self._synthesize_responses(context, agent_responses)
            
            # 4. Handle output format and chunking
            formatted_response = await self._format_and_chunk_output(context, final_response, complexity_analysis)
            
            return formatted_response
            
        except Exception as e:
            logger.error("Error processing query", error=str(e), user_id=context.user_id)
            return await self._generate_error_response(str(e), context)
    
    async def _process_complex_query(self, context: QueryContext, complexity_analysis: Dict[str, Any]) -> str:
        """Process complex multi-part queries with special handling"""
        logger.info("Processing complex query", complexity_level=complexity_analysis["complexity_level"], user_id=context.user_id)
        
        try:
            # Break down complex query into manageable parts
            query_parts = self._break_down_complex_query(context.query)
            
            if len(query_parts) > 1:
                return await self._process_multi_part_query(context, query_parts, complexity_analysis)
            else:
                # Single complex query - use enhanced prompt
                enhanced_query = self._create_enhanced_complex_prompt(context.query)
                response = await self._execute_single_agent_with_retry(self.main_agent_id, enhanced_query)
                return await self._format_and_chunk_output(context, response, complexity_analysis)
                
        except Exception as e:
            logger.error("Error processing complex query", error=str(e), user_id=context.user_id)
            return await self._generate_error_response(str(e), context)
    
    def _break_down_complex_query(self, query: str) -> List[str]:
        """Break down a complex query into manageable parts"""
        # Handle compound questions with "and" (like your example)
        if ' and ' in query.lower() and query.count('?') == 1:
            # Split on "and" but keep the context
            parts = query.split(' and ')
            if len(parts) == 2:
                # Add question mark to first part if missing
                first_part = parts[0].strip()
                if not first_part.endswith('?'):
                    first_part += '?'
                
                second_part = parts[1].strip()
                if not second_part.endswith('?'):
                    second_part += '?'
                
                return [first_part, second_part]
        
        # Look for numbered points, bullet points, or multiple questions
        lines = query.split('\n')
        parts = []
        current_part = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new numbered point or question
            is_new_section = (
                (line[0].isdigit() and '. ' in line) or
                line.startswith('-') or
                line.startswith('•') or
                (line.endswith('?') and len(current_part) > 0)
            )
            
            if is_new_section and current_part:
                parts.append('\n'.join(current_part))
                current_part = [line]
            else:
                current_part.append(line)
        
        if current_part:
            parts.append('\n'.join(current_part))
        
        # If we couldn't break it down effectively, return as single part
        if len(parts) <= 1:
            return [query]
        
        return parts
    
    async def _process_multi_part_query(self, context: QueryContext, query_parts: List[str], complexity_analysis: Dict[str, Any]) -> str:
        """Process a multi-part query with structured responses"""
        logger.info("Processing multi-part query", parts_count=len(query_parts), user_id=context.user_id)
        
        responses = []
        
        for i, part in enumerate(query_parts, 1):
            try:
                logger.info(f"Processing part {i}/{len(query_parts)}", user_id=context.user_id)
                
                # Create context for this part
                part_context = QueryContext(
                    user_id=context.user_id,
                    query=part,
                    priority=context.priority,
                    output_format=context.output_format,
                    enable_chunking=False  # Handle chunking at the end
                )
                
                # Process the part
                part_response = await self._execute_single_agent_with_retry(
                    self.main_agent_id, 
                    self._create_focused_prompt(part, i, len(query_parts))
                )
                
                responses.append(f"**{i}. Response to: {part[:60]}{'...' if len(part) > 60 else ''}**\n\n{part_response}")
                
                # Add delay to avoid rate limiting
                if i < len(query_parts):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing part {i}", error=str(e), user_id=context.user_id)
                responses.append(f"**{i}. Error processing part:** {str(e)}")
        
        # Combine all responses
        combined_response = "🤖 **Comprehensive Multi-Part Analysis**\n\n" + "\n\n---\n\n".join(responses)
        
        # Add summary if there are multiple parts
        if len(responses) > 1:
            combined_response += "\n\n---\n\n**📋 Summary**\n\nI've provided detailed responses to each part of your comprehensive query. Each section addresses specific aspects of AI governance and compliance as requested."
        
        return await self._format_and_chunk_output(context, combined_response, complexity_analysis)
    
    def _create_enhanced_complex_prompt(self, query: str) -> str:
        """Create an enhanced prompt for complex queries with response length limits"""
        return f"""
As a Legal AI Policy Expert, please provide a concise but comprehensive response to this query. 

IMPORTANT: Please limit your response to approximately 3000 characters to ensure readability.

Structure your response with:
1. Key points summary (bullet format)
2. Specific regulatory references (where applicable)
3. Brief implementation guidance
4. Main takeaways

Query: {query}

Please focus on the most critical information and provide actionable insights within the length constraints.
        """
    
    def _create_focused_prompt(self, query_part: str, part_number: int, total_parts: int) -> str:
        """Create a focused prompt for a specific part of a multi-part query"""
        return f"""
As a Legal AI Policy Expert, this is part {part_number} of {total_parts} of a comprehensive analysis. 

IMPORTANT: Please limit your response to approximately 2500 characters for this part.

Please provide a focused response to:
{query_part}

Include:
- Key points in bullet format
- Specific regulatory references
- Brief actionable guidance

Focus on the most essential information for this specific aspect.
        """
    
    async def _execute_agents_with_retry(self, context: QueryContext, required_agents: List[AgentType]) -> List[AgentResponse]:
        """Execute agents with retry logic and search-enhanced context"""
        responses = []
        
        # Pre-fetch relevant search context for all agents
        search_context = await self._gather_search_context(context.query, required_agents)
        
        for agent_type in required_agents:
            try:
                # Special handling for news queries - use real-time search
                if agent_type == AgentType.NEWS_MONITOR:
                    response = await self._handle_news_query(context.query)
                    responses.append(AgentResponse(
                        agent_type=agent_type,
                        content=response,
                        confidence=0.9,
                        sources=["Bing News Search", "Live Web Search"],
                        metadata={"search_type": "real_time_news"}
                    ))
                else:
                    # Regular agent execution with enriched context
                    agent_id = self.agents.get(agent_type) or self.main_agent_id
                    specialized_query = await self._create_search_enhanced_prompt(
                        context.query, agent_type, search_context
                    )
                    
                    response = await self._execute_single_agent_with_retry(agent_id, specialized_query)
                    
                    responses.append(AgentResponse(
                        agent_type=agent_type,
                        content=response,
                        confidence=0.8,
                        sources=search_context.get("sources", []),
                        metadata={
                            "agent_id": agent_id,
                            "search_enhanced": True,
                            "search_results_count": len(search_context.get("results", []))
                        }
                    ))
                
            except Exception as e:
                logger.error("Error executing agent", agent_type=agent_type.value, error=str(e))
                # Continue with other agents even if one fails
                
        return responses

    async def _gather_search_context(self, query: str, required_agents: List[AgentType]) -> Dict[str, Any]:
        """Gather relevant search context based on required agents"""
        search_context = {"results": [], "sources": []}
        
        try:
            # Determine what type of search is needed based on agents
            needs_legal_search = AgentType.POLICY_EXPERT in required_agents or AgentType.DOCUMENT_ANALYZER in required_agents
            needs_news_search = AgentType.NEWS_MONITOR in required_agents
            
            search_tasks = []
            
            # Legal corpus search for policy and document analysis
            if needs_legal_search:
                search_tasks.append(
                    self.search_service.search(query, SearchType.LEGAL_CORPUS, max_results=3)
                )
            
            # Web search for broader context
            if not needs_news_search:  # Avoid duplicate news searches
                search_tasks.append(
                    self.search_service.search(query, SearchType.WEB_SEARCH, max_results=2)
                )
            
            # Execute searches in parallel
            if search_tasks:
                search_responses = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for response in search_responses:
                    if isinstance(response, Exception):
                        logger.warning("Search task failed", error=str(response))
                        continue
                    
                    search_context["results"].extend(response.results)
                    search_context["sources"].extend(response.sources_used)
            
            # Remove duplicate sources
            search_context["sources"] = list(set(search_context["sources"]))
            
            return search_context
            
        except Exception as e:
            logger.error("Error gathering search context", error=str(e))
            return {"results": [], "sources": []}

    async def _create_search_enhanced_prompt(
        self, 
        original_query: str, 
        agent_type: AgentType, 
        search_context: Dict[str, Any]
    ) -> str:
        """Create prompts enhanced with search results"""
        
        # Get base prompt
        base_prompt = await self._create_specialized_prompt(original_query, agent_type)
        
        # Add search context if available
        if search_context.get("results"):
            context_section = "\n\n**RELEVANT CONTEXT FROM SEARCH:**\n"
            
            for i, result in enumerate(search_context["results"][:3], 1):  # Limit to top 3
                context_section += f"\n{i}. **{result.title}** (Source: {result.source})\n"
                context_section += f"   {result.content[:200]}...\n"
                if result.url:
                    context_section += f"   URL: {result.url}\n"
            
            context_section += f"\n**Sources:** {', '.join(search_context['sources'])}\n"
            context_section += "\nPlease incorporate relevant information from the above context into your response, citing sources where appropriate.\n"
            
            # Insert context before the query
            enhanced_prompt = base_prompt.replace(
                f"Query: {original_query}",
                f"{context_section}\nQuery: {original_query}"
            )
            
            return enhanced_prompt
        
        return base_prompt
    
    async def _handle_news_query(self, query: str) -> str:
        """Handle news queries with real-time search and specialized formatting"""
        try:
            # Perform news search using the search service
            news_response = await self.search_service.search(
                query, 
                SearchType.NEWS_SEARCH, 
                max_results=5
            )
            
            if not news_response.results:
                return (
                    "📰 **No recent news found** for your query.\n\n"
                    "This might be because:\n"
                    "• The topic is very new or specific\n"
                    "• There are no recent developments\n"
                    "• Try rephrasing with broader terms\n\n"
                    "You can also ask me about established AI policy topics!"
                )
            
            # Format the news response
            response = f"📰 **Latest News on: {query}**\n\n"
            
            for i, result in enumerate(news_response.results, 1):
                response += f"**{i}. {result.title}**\n"
                
                # Add publication date if available
                if hasattr(result, 'published_date') and result.published_date:
                    response += f"*Published: {result.published_date}*\n"
                
                # Add source
                response += f"*Source: {result.source}*\n\n"
                
                # Add content summary
                content_preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
                response += f"{content_preview}\n"
                
                # Add URL if available
                if result.url:
                    response += f"🔗 [Read more]({result.url})\n"
                
                response += "\n---\n\n"
            
            # Add footer with search metadata
            response += f"*Search performed in real-time using {', '.join(news_response.sources_used)}*\n"
            response += f"*Found {len(news_response.results)} relevant articles*"
            
            return response
            
        except Exception as e:
            logger.error("Error handling news query", error=str(e))
            return (
                "⚠️ **News Search Temporarily Unavailable**\n\n"
                "I'm having trouble accessing real-time news sources right now. "
                "Please try again in a moment, or ask me about established AI policy topics "
                "that I can help with from my knowledge base."
            )

    async def _execute_single_agent_with_retry(self, agent_id: str, query: str) -> str:
        """Execute a single agent with retry logic for rate limiting and timeouts"""
        for attempt in range(self.max_retries + 1):
            try:
                return await self._execute_single_agent(agent_id, query)
                
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limiting
                if "rate_limit_exceeded" in error_str.lower():
                    if attempt < self.max_retries:
                        # Extract wait time if available
                        wait_time = self._extract_wait_time(error_str)
                        if not wait_time:
                            wait_time = min(self.base_retry_delay * (2 ** attempt), self.max_retry_delay)
                        
                        logger.warning(f"Rate limit exceeded, retrying in {wait_time}s", 
                                     attempt=attempt + 1, wait_time=wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                
                # Handle timeouts
                if "timeout" in error_str.lower() or "time" in error_str.lower():
                    if attempt < self.max_retries:
                        wait_time = 5
                        logger.warning(f"Timeout occurred, retrying in {wait_time}s", 
                                     attempt=attempt + 1)
                        await asyncio.sleep(wait_time)
                        continue
                
                # If it's the last attempt or an unhandleable error, raise it
                if attempt == self.max_retries:
                    raise e
                    
                # For other errors, wait a bit and retry
                await asyncio.sleep(2)
        
        raise Exception("Max retries exceeded")
    
    def _extract_wait_time(self, error_message: str) -> Optional[int]:
        """Extract wait time from rate limit error message"""
        import re
        
        # Look for patterns like "Try again in X seconds"
        match = re.search(r'try again in (\d+) seconds?', error_message.lower())
        if match:
            return int(match.group(1)) + 1  # Add 1 second buffer
        
        return None
    
    async def _format_and_chunk_output(self, context: QueryContext, response: str, complexity_analysis: Dict[str, Any]) -> str:
        """Format output and chunk if necessary for Teams limitations"""
        # Apply basic formatting
        formatted_response = await self._format_output(context, response)
        
        # Check if chunking is needed
        if (context.enable_chunking and 
            len(formatted_response) > context.max_response_length and 
            complexity_analysis.get("requires_chunking", False)):
            
            return await self._chunk_response(formatted_response, context.max_response_length)
        
        return formatted_response
    
    async def _chunk_response(self, response: str, max_length: int) -> str:
        """Chunk long responses for Teams message limits"""
        if len(response) <= max_length:
            return response
        
        # Try to split at natural breakpoints
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = response.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
                else:
                    # Paragraph itself is too long, split by sentences
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence + '. '
                            else:
                                # Sentence is too long, just cut it
                                chunks.append(sentence[:max_length-20] + "...")
                                current_chunk = ""
                        else:
                            current_chunk += sentence + '. '
            else:
                current_chunk += paragraph + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Return the first chunk with a note about continuation
        if len(chunks) > 1:
            first_chunk = chunks[0]
            first_chunk += f"\n\n📄 **This is part 1 of {len(chunks)}.** Due to length limits, please ask for the next part to continue."
            return first_chunk
        
        return response
    
    async def _generate_error_response(self, error: str, context: QueryContext) -> str:
        """Generate a helpful error response for users"""
        if "rate_limit_exceeded" in error.lower():
            return """
🚧 **System Temporarily Busy**

I'm currently experiencing high demand. This is a temporary issue that typically resolves within a few moments.

**Please try:**
1. Waiting 30 seconds and resending your query
2. Breaking complex questions into smaller parts
3. Asking one question at a time

I apologize for the inconvenience and appreciate your patience! 🙏
            """
        
        elif "timeout" in error.lower():
            return """
⏱️ **Query Processing Timeout**

Your query was quite complex and took longer than expected to process.

**Please try:**
1. Breaking your question into smaller, more specific parts
2. Asking about one topic at a time
3. Using more specific keywords in your query

I'm ready to help with more focused questions! 🚀
            """
        
        else:
            return f"""
❌ **Processing Error**

I encountered an unexpected error while processing your request.

**What you can do:**
1. Try rephrasing your question
2. Break complex queries into simpler parts
3. Contact support if the issue persists

Error details: {error[:100]}{'...' if len(error) > 100 else ''}
            """

    async def _analyze_query_requirements(self, context: QueryContext) -> List[AgentType]:
        """
        Analyze the user query to determine which agents are needed
        """
        query_lower = context.query.lower()
        required_agents = []
        
        # Policy-related keywords
        policy_keywords = [
            "eu ai act", "nist", "iso", "aida", "policy", "regulation", "compliance",
            "governance", "framework", "standard", "guideline", "requirement"
        ]
        
        # News-related keywords
        news_keywords = [
            "latest", "recent", "news", "update", "announcement", "current",
            "today", "this week", "this month", "development"
        ]
        
        # Document analysis keywords
        doc_keywords = [
            "analyze", "document", "file", "pdf", "review", "examine",
            "compare", "contrast", "summarize"
        ]
        
        # Report generation keywords
        report_keywords = [
            "report", "summary", "overview", "comprehensive", "detailed",
            "analysis", "pdf", "email", "send"
        ]
        
        # Determine required agents based on keywords
        if any(keyword in query_lower for keyword in policy_keywords):
            required_agents.append(AgentType.POLICY_EXPERT)
            
        if any(keyword in query_lower for keyword in news_keywords):
            required_agents.append(AgentType.NEWS_MONITOR)
            
        if any(keyword in query_lower for keyword in doc_keywords):
            required_agents.append(AgentType.DOCUMENT_ANALYZER)
            
        if any(keyword in query_lower for keyword in report_keywords):
            required_agents.append(AgentType.REPORT_GENERATOR)
            context.output_format = "pdf"  # Assume PDF for reports
        
        # Default to policy expert if no specific agent identified
        if not required_agents:
            required_agents.append(AgentType.POLICY_EXPERT)
            
        return required_agents

    async def _execute_single_agent(self, agent_id: str, query: str) -> str:
        """
        Execute a single agent and return its response with timeout protection
        """
        # Create thread
        thread = self.project.agents.threads.create()
        
        # Send message
        self.project.agents.messages.create(
            thread.id, 
            role="user", 
            content=query
        )
        
        # Run agent
        run = self.project.agents.runs.create_and_process(
            thread.id, 
            agent_id=agent_id
        )
        
        # Poll for completion with timeout protection
        max_wait_time = 90  # Maximum 90 seconds wait time
        poll_interval = 2   # Poll every 2 seconds instead of 1
        elapsed_time = 0
        
        while run.status not in (RunStatus.COMPLETED, RunStatus.FAILED) and elapsed_time < max_wait_time:
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval
            
            try:
                run = self.project.agents.runs.get(thread_id=thread.id, run_id=run.id)
            except Exception as e:
                logger.warning(f"Error polling agent status: {e}")
                # Continue polling unless we've exceeded time limit
                if elapsed_time >= max_wait_time:
                    raise Exception(f"Agent execution timed out after {max_wait_time} seconds")
        
        if elapsed_time >= max_wait_time:
            raise Exception(f"Agent execution timed out after {max_wait_time} seconds")
        
        if run.status == RunStatus.FAILED:
            raise Exception(f"Agent run failed: {run.last_error}")
        
        # Get response
        try:
            messages = self.project.agents.messages.list(
                thread_id=thread.id,
                order=ListSortOrder.ASCENDING
            )
            
            for message in messages:
                if message.role == "assistant" and message.text_messages:
                    return message.text_messages[-1].text.value
        except Exception as e:
            logger.error(f"Error retrieving agent response: {e}")
            raise Exception(f"Failed to retrieve agent response: {e}")
                
        return "No response generated"

    async def _create_specialized_prompt(self, original_query: str, agent_type: AgentType) -> str:
        """
        Create specialized prompts for different agent types
        """
        base_query = original_query
        
        if agent_type == AgentType.POLICY_EXPERT:
            return f"""
            As a Legal AI Policy Expert, please analyze the following query with focus on:
            - Relevant AI policies, regulations, and frameworks
            - Compliance requirements and implications
            - Best practices and recommendations
            - Cite specific sections and sources where applicable
            
            Query: {base_query}
            """
            
        elif agent_type == AgentType.NEWS_MONITOR:
            return f"""
            As an AI Policy News Monitor, please provide:
            - Latest developments and news related to the query
            - Recent policy changes or announcements
            - Upcoming deadlines or important dates
            - Trending topics in AI governance
            
            Query: {base_query}
            """
            
        elif agent_type == AgentType.DOCUMENT_ANALYZER:
            return f"""
            As a Document Analysis Expert, please:
            - Analyze and summarize relevant documents
            - Compare different policy frameworks
            - Extract key requirements and obligations
            - Identify potential conflicts or gaps
            
            Query: {base_query}
            """
            
        elif agent_type == AgentType.REPORT_GENERATOR:
            return f"""
            As a Report Generation Specialist, please create:
            - A comprehensive, well-structured analysis
            - Executive summary and key findings
            - Actionable recommendations
            - Professional formatting suitable for stakeholders
            
            Query: {base_query}
            """
            
        return base_query

    async def _synthesize_responses(self, context: QueryContext, responses: List[AgentResponse]) -> str:
        """
        Synthesize multiple agent responses into a coherent final response
        """
        if len(responses) == 1:
            return responses[0].content
            
        # Combine responses intelligently
        synthesis_prompt = f"""
        Please synthesize the following expert responses into a comprehensive, coherent answer to the user's query: "{context.query}"
        
        Expert Responses:
        """
        
        for i, response in enumerate(responses, 1):
            synthesis_prompt += f"\n\n{i}. {response.agent_type.value.replace('_', ' ').title()} Analysis:\n{response.content}"
        
        synthesis_prompt += """
        
        Please provide a unified response that:
        - Integrates all relevant insights
        - Maintains clarity and readability
        - Highlights key actionable items
        - Cites sources where appropriate
        - Avoids redundancy while preserving important details
        """
        
        # Use main agent for synthesis
        return await self._execute_single_agent_with_retry(self.main_agent_id, synthesis_prompt)

    async def _format_output(self, context: QueryContext, response: str) -> str:
        """
        Format the output based on the requested format (text, PDF, email)
        """
        if context.output_format == "pdf":
            # TODO: Implement PDF generation
            return response + "\n\n📄 *PDF report generation will be implemented in the next phase.*"
            
        elif context.output_format == "email":
            # TODO: Implement email sending
            return response + "\n\n📧 *Email delivery will be implemented in the next phase.*"
            
        return response

    async def _handle_basic_queries(self, query: str) -> Optional[str]:
        """
        Handle basic greetings, help requests, and common conversational queries
        Returns a response if it's a basic query, None if it should go to specialized agents
        """
        query_lower = query.lower().strip()
        
        # Remove common prefixes that Teams might add
        query_clean = query_lower.replace("<at>legal-mind-ai</at>", "").strip()
        
        # Greeting patterns
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", 
            "good evening", "greetings", "howdy", "what's up"
        ]
        
        # Help patterns
        help_patterns = [
            "help", "what can you do", "what do you do", "how can you help", 
            "what are your capabilities", "what can i ask you", "commands",
            "how do you work", "what's your purpose", "what are you"
        ]
        
        # Check for greetings
        for greeting in greetings:
            if query_clean == greeting or query_clean.startswith(greeting + " ") or query_clean.endswith(" " + greeting):
                return (
                    "Hello! 👋 I'm Legal-Mind-AI, a specialized AI assistant focused on providing "
                    "insights related to AI Law, Policy, and Regulation. I can help you with:\n\n"
                    "🔍 **AI Policy & Regulations** - EU AI Act, NIST frameworks, GDPR compliance\n"
                    "📰 **Latest News** - Recent developments in AI governance\n"
                    "📊 **Compliance Analysis** - Requirements and best practices\n"
                    "📄 **Report Generation** - Detailed policy analysis reports\n\n"
                    "How may I assist you today? Feel free to ask about any AI governance topic!"
                )
        
        # Check for help requests
        for pattern in help_patterns:
            if pattern in query_clean:
                return (
                    "🤖 **Legal-Mind-AI Help Center**\n\n"
                    "I'm your AI policy expert! Here's what I can help you with:\n\n"
                    "**📋 Policy Guidance:**\n"
                    "• EU AI Act requirements and compliance\n"
                    "• NIST AI Risk Management Framework\n"
                    "• GDPR implications for AI systems\n"
                    "• International AI governance standards\n\n"
                    "**📰 News & Updates:**\n"
                    "• Latest AI policy developments\n"
                    "• Regulatory announcements\n"
                    "• Compliance deadlines\n\n"
                    "**📊 Analysis & Reports:**\n"
                    "• Risk assessments\n"
                    "• Compliance gap analysis\n"
                    "• Policy comparison reports\n\n"
                    "**Example questions:**\n"
                    "• 'What are the key requirements of the EU AI Act?'\n"
                    "• 'How do I ensure GDPR compliance for my AI system?'\n"
                    "• 'What's the latest news in AI regulation?'\n"
                    "• 'Generate a compliance report for my AI project'\n\n"
                    "What would you like to know about AI governance today?"
                )
        
        # Check for very short, conversational queries that should get a friendly redirect
        simple_queries = ["ok", "okay", "thanks", "thank you", "yes", "no", "sure"]
        if query_clean in simple_queries:
            return (
                "You're welcome! I'm here to help with any AI policy, regulation, or "
                "governance questions you might have. What would you like to explore?"
            )
        
        # Return None if it's not a basic query - let specialized agents handle it
        return None

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including search services"""
        search_status = self.search_service.get_service_status()
        
        return {
            "agents": {
                "policy_expert": bool(self.agents.get(AgentType.POLICY_EXPERT)),
                "news_monitor": bool(self.agents.get(AgentType.NEWS_MONITOR)),
                "document_analyzer": bool(self.agents.get(AgentType.DOCUMENT_ANALYZER)),
                "report_generator": bool(self.agents.get(AgentType.REPORT_GENERATOR)),
                "main_agent": bool(self.main_agent_id)
            },
            "search_services": search_status,
            "features": {
                "real_time_news": search_status["news_service"],
                "legal_corpus_search": search_status["azure_search"],
                "web_search": search_status["bing_search"],
                "mixed_search": any(search_status.values())
            }
        }

# Global orchestrator instance
orchestrator = LegalMindOrchestrator()
