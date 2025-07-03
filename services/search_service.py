"""
Centralized Search Service for Legal-Mind-AI
Manages all search operations including Azure AI Search, Bing Search, and News APIs
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from services.news_service import NewsMonitorService, NewsItem

logger = structlog.get_logger(__name__)

class SearchType(Enum):
    """Types of search operations"""
    LEGAL_CORPUS = "legal_corpus"
    CURRENT_NEWS = "current_news" 
    WEB_SEARCH = "web_search"
    MIXED = "mixed"

@dataclass
class SearchResult:
    """Unified search result structure"""
    title: str
    content: str
    source: str
    url: Optional[str] = None
    relevance_score: float = 0.0
    published_date: Optional[datetime] = None
    search_type: SearchType = SearchType.WEB_SEARCH
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SearchResponse:
    """Complete search response with metadata"""
    results: List[SearchResult]
    search_type: SearchType
    query: str
    total_results: int
    search_duration: float
    sources_used: List[str]
    cached: bool = False

class AzureSearchService:
    """Azure AI Search integration for legal corpus"""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.api_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "legal-mind-corpus")
        self.enabled = bool(self.endpoint and self.api_key)
        
    async def search(self, query: str, top: int = 5) -> List[SearchResult]:
        """Search the legal corpus"""
        if not self.enabled:
            logger.warning("Azure AI Search not configured")
            return []
            
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            search_body = {
                "search": query,
                "top": top,
                "highlight": "content",
                "highlightPreTag": "**",
                "highlightPostTag": "**"
            }
            
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version=2023-11-01"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=search_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_azure_results(data, query)
                    else:
                        logger.error("Azure Search API error", status=response.status, response=await response.text())
                        return []
                        
        except Exception as e:
            logger.error("Error in Azure Search", error=str(e))
            return []
    
    def _parse_azure_results(self, data: Dict, query: str) -> List[SearchResult]:
        """Parse Azure Search API response"""
        results = []
        
        for item in data.get("value", []):
            try:
                # Extract highlighted content or fall back to regular content
                content = ""
                if "@search.highlights" in item and "content" in item["@search.highlights"]:
                    content = " ".join(item["@search.highlights"]["content"])
                else:
                    content = item.get("content", "")[:500] + "..."
                
                result = SearchResult(
                    title=item.get("title", "Legal Document"),
                    content=content,
                    source="Legal Corpus",
                    url=item.get("url"),
                    relevance_score=item.get("@search.score", 0.0),
                    search_type=SearchType.LEGAL_CORPUS,
                    metadata={
                        "document_type": item.get("document_type"),
                        "jurisdiction": item.get("jurisdiction"),
                        "effective_date": item.get("effective_date")
                    }
                )
                results.append(result)
                
            except Exception as e:
                logger.warning("Error parsing Azure search result", error=str(e))
                
        return results

class BingSearchService:
    """Bing Search integration for web search"""
    
    def __init__(self):
        self.api_key = os.getenv("BING_SEARCH_KEY")
        self.enabled = bool(self.api_key)
        
    async def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """Perform web search using Bing"""
        if not self.enabled:
            logger.warning("Bing Search not configured")
            return []
            
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "count": count,
                "textDecorations": True,
                "textFormat": "HTML"
            }
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_bing_results(data)
                    else:
                        logger.error("Bing Search API error", status=response.status)
                        return []
                        
        except Exception as e:
            logger.error("Error in Bing Search", error=str(e))
            return []
    
    def _parse_bing_results(self, data: Dict) -> List[SearchResult]:
        """Parse Bing Search API response"""
        results = []
        
        for item in data.get("webPages", {}).get("value", []):
            try:
                result = SearchResult(
                    title=item.get("name", ""),
                    content=item.get("snippet", ""),
                    source="Web Search",
                    url=item.get("url"),
                    search_type=SearchType.WEB_SEARCH,
                    metadata={
                        "display_url": item.get("displayUrl"),
                        "language": item.get("language")
                    }
                )
                results.append(result)
                
            except Exception as e:
                logger.warning("Error parsing Bing search result", error=str(e))
                
        return results

class SearchService:
    """
    Centralized search service that manages all search operations
    """
    
    def __init__(self):
        # Initialize search services
        self.azure_search = AzureSearchService()
        self.bing_search = BingSearchService()
        self.news_service = NewsMonitorService()
        
        # Search cache (simple in-memory cache)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Rate limiting
        self._last_requests = {
            "azure": [],
            "bing": [],
            "news": []
        }
        self._rate_limits = {
            "azure": {"requests": 10, "window": 60},  # 10 requests per minute
            "bing": {"requests": 3, "window": 60},    # 3 requests per minute  
            "news": {"requests": 5, "window": 60}     # 5 requests per minute
        }
    
    async def search(
        self, 
        query: str, 
        search_type: SearchType = SearchType.MIXED,
        max_results: int = 5
    ) -> SearchResponse:
        """
        Unified search interface
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"{search_type.value}:{query}:{max_results}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        results = []
        sources_used = []
        
        try:
            if search_type == SearchType.LEGAL_CORPUS:
                results = await self._search_legal_corpus(query, max_results)
                sources_used = ["Azure AI Search"]
                
            elif search_type == SearchType.CURRENT_NEWS:
                results = await self._search_current_news(query, max_results)
                sources_used = ["Bing News", "News APIs"]
                
            elif search_type == SearchType.WEB_SEARCH:
                results = await self._search_web(query, max_results)
                sources_used = ["Bing Web Search"]
                
            elif search_type == SearchType.MIXED:
                # Intelligent mixed search
                results = await self._mixed_search(query, max_results)
                sources_used = ["Azure AI Search", "Bing Search", "News APIs"]
            
            # Calculate search duration
            duration = (datetime.now() - start_time).total_seconds()
            
            response = SearchResponse(
                results=results,
                search_type=search_type,
                query=query,
                total_results=len(results),
                search_duration=duration,
                sources_used=sources_used,
                cached=False
            )
            
            # Cache the result
            self._cache_result(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error("Error in unified search", error=str(e))
            return SearchResponse(
                results=[],
                search_type=search_type,
                query=query,
                total_results=0,
                search_duration=(datetime.now() - start_time).total_seconds(),
                sources_used=[],
                cached=False
            )
    
    async def _search_legal_corpus(self, query: str, max_results: int) -> List[SearchResult]:
        """Search legal corpus with rate limiting"""
        if not await self._check_rate_limit("azure"):
            logger.warning("Azure Search rate limit exceeded")
            return []
        
        return await self.azure_search.search(query, max_results)
    
    async def _search_current_news(self, query: str, max_results: int) -> List[SearchResult]:
        """Search current news with rate limiting"""
        if not await self._check_rate_limit("news"):
            logger.warning("News search rate limit exceeded")
            return []
        
        try:
            # Use the existing news service
            news_items = await self.news_service.get_latest_news(
                query=query,
                hours_back=168,  # 7 days
                max_items=max_results
            )
            
            # Convert NewsItem to SearchResult
            results = []
            for item in news_items:
                result = SearchResult(
                    title=item.title,
                    content=item.summary,
                    source=item.source,
                    url=item.url,
                    published_date=item.published_date,
                    relevance_score=item.relevance_score,
                    search_type=SearchType.CURRENT_NEWS,
                    metadata={"keywords": item.keywords}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Error in news search", error=str(e))
            return []
    
    async def _search_web(self, query: str, max_results: int) -> List[SearchResult]:
        """Search web with rate limiting"""
        if not await self._check_rate_limit("bing"):
            logger.warning("Bing search rate limit exceeded")
            return []
        
        return await self.bing_search.search(query, max_results)
    
    async def _mixed_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Intelligent mixed search across all sources"""
        all_results = []
        
        # Determine query intent for smart source selection
        query_lower = query.lower()
        
        # Legal/regulatory keywords - prioritize legal corpus
        if any(keyword in query_lower for keyword in [
            "regulation", "compliance", "law", "legal", "policy", "act", 
            "gdpr", "eu ai act", "nist", "framework", "requirement"
        ]):
            legal_results = await self._search_legal_corpus(query, max_results // 2 + 1)
            all_results.extend(legal_results)
        
        # News/current keywords - prioritize news search
        if any(keyword in query_lower for keyword in [
            "latest", "recent", "news", "update", "current", "development",
            "announcement", "today", "this week"
        ]):
            news_results = await self._search_current_news(query, max_results // 2 + 1)
            all_results.extend(news_results)
        
        # If we don't have enough results, supplement with web search
        if len(all_results) < max_results:
            remaining = max_results - len(all_results)
            web_results = await self._search_web(query, remaining)
            all_results.extend(web_results)
        
        # Sort by relevance and return top results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_results[:max_results]
    
    async def _check_rate_limit(self, service: str) -> bool:
        """Check if service is within rate limits"""
        now = datetime.now()
        service_requests = self._last_requests[service]
        rate_limit = self._rate_limits[service]
        
        # Remove old requests outside the window
        cutoff = now - timedelta(seconds=rate_limit["window"])
        self._last_requests[service] = [req for req in service_requests if req > cutoff]
        
        # Check if we can make another request
        if len(self._last_requests[service]) < rate_limit["requests"]:
            self._last_requests[service].append(now)
            return True
        
        return False
    
    def _get_cached_result(self, cache_key: str) -> Optional[SearchResponse]:
        """Get cached search result if still valid"""
        if cache_key in self._cache:
            cached_time, result = self._cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self._cache_ttl:
                result.cached = True
                return result
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: SearchResponse):
        """Cache search result"""
        self._cache[cache_key] = (datetime.now(), result)
        
        # Simple cache cleanup - remove old entries if cache gets too large
        if len(self._cache) > 100:
            # Remove oldest 20 entries
            sorted_cache = sorted(self._cache.items(), key=lambda x: x[1][0])
            for key, _ in sorted_cache[:20]:
                del self._cache[key]
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all search services"""
        return {
            "azure_search": self.azure_search.enabled,
            "bing_search": self.bing_search.enabled,
            "news_service": bool(self.news_service.bing_search_key or self.news_service.news_api_key)
        }
