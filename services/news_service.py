"""
News Monitoring Service for Legal-Mind-AI
Fetches and analyzes latest AI policy news and updates
"""

import os
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class NewsItem:
    """Represents a news item related to AI policy"""
    
    def __init__(
        self,
        title: str,
        summary: str,
        url: str,
        published_date: datetime,
        source: str,
        relevance_score: float = 0.0,
        keywords: List[str] = None
    ):
        self.title = title
        self.summary = summary
        self.url = url
        self.published_date = published_date
        self.source = source
        self.relevance_score = relevance_score
        self.keywords = keywords or []

class NewsMonitorService:
    """
    Service for monitoring AI policy news from various sources
    """
    
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.bing_search_key = os.getenv("BING_SEARCH_KEY")
        
        # AI Policy related keywords for filtering
        self.ai_policy_keywords = [
            "artificial intelligence", "ai regulation", "ai act", "ai policy",
            "machine learning regulation", "algorithmic accountability",
            "ai governance", "ai ethics", "ai safety", "ai compliance",
            "eu ai act", "nist ai", "iso ai", "aida canada", "gdpr ai",
            "algorithmic bias", "ai transparency", "ai audit", "ai risk",
            "responsible ai", "trustworthy ai", "ai standards"
        ]
        
        # RSS feeds for AI policy news
        self.rss_feeds = [
            "https://feeds.feedburner.com/oreilly/radar",
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            "https://www.wired.com/feed/tag/ai/rss",
            "https://venturebeat.com/ai/feed/",
            "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"
        ]
        
        # Government and regulatory sources
        self.regulatory_sources = [
            "https://ec.europa.eu/commission/presscorner/api/documents.cfm?cl=en&typ=1",
            "https://www.nist.gov/news-events/news/rss.xml",
            "https://www.ftc.gov/news-events/news/rss"
        ]
    
    async def get_latest_news(
        self,
        query: Optional[str] = None,
        hours_back: int = 24,
        max_items: int = 10
    ) -> List[NewsItem]:
        """
        Get latest AI policy news
        
        Args:
            query: Specific query to search for
            hours_back: How many hours back to search
            max_items: Maximum number of items to return
            
        Returns:
            List of NewsItem objects
        """
        news_items = []
        
        try:
            # Get news from multiple sources
            tasks = [
                self._get_news_api_articles(query, hours_back),
                self._get_rss_feed_articles(hours_back),
                self._get_bing_news(query, hours_back)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            for result in results:
                if isinstance(result, list):
                    news_items.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Error fetching news: {result}")
            
            # Filter and rank by relevance
            filtered_items = self._filter_and_rank_news(news_items, query)
            
            # Return top items
            return filtered_items[:max_items]
            
        except Exception as e:
            logger.error(f"Error getting latest news: {str(e)}")
            return []
    
    async def _get_news_api_articles(
        self,
        query: Optional[str],
        hours_back: int
    ) -> List[NewsItem]:
        """Fetch articles from News API"""
        if not self.news_api_key:
            return []
        
        try:
            search_query = query or "artificial intelligence regulation OR AI policy OR AI governance"
            from_date = (datetime.now() - timedelta(hours=hours_back)).isoformat()
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": search_query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.news_api_key,
                "pageSize": 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_news_api_response(data)
            
        except Exception as e:
            logger.error(f"Error fetching from News API: {str(e)}")
        
        return []
    
    async def _get_rss_feed_articles(self, hours_back: int) -> List[NewsItem]:
        """Fetch articles from RSS feeds"""
        news_items = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for feed_url in self.rss_feeds:
            try:
                # Note: feedparser is synchronous, but we're keeping this async
                # for consistency and potential future async implementation
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    pub_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        import time
                        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    
                    # Skip old articles
                    if pub_date < cutoff_time:
                        continue
                    
                    # Check if article is AI policy related
                    title = getattr(entry, 'title', '')
                    summary = getattr(entry, 'summary', '')
                    
                    if self._is_ai_policy_related(title + " " + summary):
                        news_items.append(NewsItem(
                            title=title,
                            summary=summary,
                            url=getattr(entry, 'link', ''),
                            published_date=pub_date,
                            source=feed.feed.get('title', 'RSS Feed'),
                            relevance_score=self._calculate_relevance_score(title, summary)
                        ))
                        
            except Exception as e:
                logger.warning(f"Error parsing RSS feed {feed_url}: {str(e)}")
        
        return news_items
    
    async def _get_bing_news(
        self,
        query: Optional[str],
        hours_back: int
    ) -> List[NewsItem]:
        """Fetch news from Bing News Search API"""
        if not self.bing_search_key:
            return []
        
        try:
            search_query = query or "AI regulation artificial intelligence policy"
            
            url = "https://api.bing.microsoft.com/v7.0/news/search"
            headers = {"Ocp-Apim-Subscription-Key": self.bing_search_key}
            params = {
                "q": search_query,
                "count": 20,
                "mkt": "en-US",
                "freshness": "Day" if hours_back <= 24 else "Week"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_bing_news_response(data)
            
        except Exception as e:
            logger.error(f"Error fetching from Bing News: {str(e)}")
        
        return []
    
    def _parse_news_api_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """Parse News API response"""
        news_items = []
        
        for article in data.get('articles', []):
            try:
                # Parse date
                pub_date = datetime.now()
                if article.get('publishedAt'):
                    pub_date = datetime.fromisoformat(
                        article['publishedAt'].replace('Z', '+00:00')
                    )
                
                title = article.get('title', '')
                description = article.get('description', '')
                
                news_items.append(NewsItem(
                    title=title,
                    summary=description,
                    url=article.get('url', ''),
                    published_date=pub_date,
                    source=article.get('source', {}).get('name', 'News API'),
                    relevance_score=self._calculate_relevance_score(title, description)
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing news article: {str(e)}")
        
        return news_items
    
    def _parse_bing_news_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """Parse Bing News API response"""
        news_items = []
        
        for article in data.get('value', []):
            try:
                # Parse date
                pub_date = datetime.now()
                if article.get('datePublished'):
                    pub_date = datetime.fromisoformat(
                        article['datePublished'].replace('Z', '+00:00')
                    )
                
                title = article.get('name', '')
                description = article.get('description', '')
                
                news_items.append(NewsItem(
                    title=title,
                    summary=description,
                    url=article.get('url', ''),
                    published_date=pub_date,
                    source=article.get('provider', [{}])[0].get('name', 'Bing News'),
                    relevance_score=self._calculate_relevance_score(title, description)
                ))
                
            except Exception as e:
                logger.warning(f"Error parsing Bing news article: {str(e)}")
        
        return news_items
    
    def _is_ai_policy_related(self, text: str) -> bool:
        """Check if text is related to AI policy"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.ai_policy_keywords)
    
    def _calculate_relevance_score(self, title: str, summary: str) -> float:
        """Calculate relevance score for a news item"""
        text = (title + " " + summary).lower()
        score = 0.0
        
        # Weight different keywords
        high_value_keywords = ["ai act", "ai regulation", "eu ai act", "nist ai", "ai compliance"]
        medium_value_keywords = ["artificial intelligence", "ai policy", "ai governance", "machine learning"]
        low_value_keywords = ["ai", "algorithm", "automation"]
        
        # Calculate score based on keyword presence
        for keyword in high_value_keywords:
            if keyword in text:
                score += 3.0
        
        for keyword in medium_value_keywords:
            if keyword in text:
                score += 2.0
        
        for keyword in low_value_keywords:
            if keyword in text:
                score += 1.0
        
        # Boost score for regulatory sources
        regulatory_terms = ["regulation", "compliance", "standard", "framework", "policy"]
        for term in regulatory_terms:
            if term in text:
                score += 1.5
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _filter_and_rank_news(
        self,
        news_items: List[NewsItem],
        query: Optional[str] = None
    ) -> List[NewsItem]:
        """Filter and rank news items by relevance"""
        # Remove duplicates based on title similarity
        unique_items = []
        seen_titles = set()
        
        for item in news_items:
            title_key = item.title.lower().strip()[:50]  # First 50 chars for deduplication
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
        
        # Additional filtering based on query
        if query:
            query_lower = query.lower()
            for item in unique_items:
                if query_lower in item.title.lower() or query_lower in item.summary.lower():
                    item.relevance_score += 2.0
        
        # Sort by relevance score and date
        unique_items.sort(key=lambda x: (x.relevance_score, x.published_date), reverse=True)
        
        return unique_items
    
    async def get_policy_updates(self, hours_back: int = 168) -> List[NewsItem]:  # 1 week default
        """Get specific policy updates from regulatory sources"""
        policy_updates = []
        
        # Focus on regulatory and government sources
        policy_queries = [
            "EU AI Act implementation",
            "NIST AI Risk Management Framework update",
            "FTC AI guidance",
            "AI regulation compliance deadline"
        ]
        
        for query in policy_queries:
            updates = await self.get_latest_news(query, hours_back, max_items=5)
            policy_updates.extend(updates)
        
        # Remove duplicates and return top updates
        unique_updates = self._filter_and_rank_news(policy_updates)
        return unique_updates[:10]

# Global news service instance
news_service = NewsMonitorService()
