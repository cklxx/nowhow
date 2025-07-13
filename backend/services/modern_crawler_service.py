"""
Modern crawler service using latest open source tools (2024).
Integrates Firecrawl, Crawl4AI, Playwright, and other cutting-edge solutions.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import time
import random

# Core HTTP and parsing
import aiohttp
import feedparser
from bs4 import BeautifulSoup

# Modern scraping tools
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

from core.interfaces import ICrawlerService
from core.exceptions import CrawlingError
from config import Settings

logger = logging.getLogger(__name__)


class ModernCrawlerService(ICrawlerService):
    """
    Modern web crawler service using 2024's best open source tools.
    
    Features:
    - Firecrawl for AI-ready content extraction
    - Crawl4AI for LLM-friendly output 
    - Playwright for dynamic content
    - Intelligent fallback mechanisms
    - Enhanced error handling and retry logic
    """
    
    # Premium AI sources verified for 2024
    PREMIUM_SOURCES = {
        "rss_feeds": [
            {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default", "priority": "high"},
            {"name": "Berkeley BAIR", "url": "https://bair.berkeley.edu/blog/feed.xml", "priority": "high"},
            {"name": "MIT AI News", "url": "https://news.mit.edu/rss/topic/artificial-intelligence", "priority": "high"},
            {"name": "OpenAI Research", "url": "https://openai.com/blog/rss/", "priority": "high"},
            {"name": "DeepMind Blog", "url": "https://deepmind.google/discover/blog/rss.xml", "priority": "high"},
            {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss", "priority": "high"},
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/ai/feed/", "priority": "medium"},
            {"name": "The Gradient", "url": "https://thegradient.pub/rss/", "priority": "medium"},
            {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/feed/", "priority": "medium"},
            {"name": "AWS ML Blog", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "priority": "medium"}
        ],
        "websites": [
            {"name": "ArXiv AI Latest", "url": "https://arxiv.org/list/cs.AI/recent", "type": "dynamic", "priority": "high"},
            {"name": "Papers With Code", "url": "https://paperswithcode.com/latest", "type": "dynamic", "priority": "high"},
            {"name": "Hugging Face Papers", "url": "https://huggingface.co/papers", "type": "dynamic", "priority": "medium"}
        ]
    }
    
    # Modern user agents for 2024
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    ]
    
    def __init__(self, settings: Settings, firecrawl_api_key: Optional[str] = None):
        self.settings = settings
        self.firecrawl_api_key = firecrawl_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {"firecrawl": 0, "crawl4ai": 0, "playwright": 0, "fallback": 0}
        
        # Initialize available tools
        self.firecrawl = None
        self.crawl4ai = None
        
        if FIRECRAWL_AVAILABLE and firecrawl_api_key:
            try:
                self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
                logger.info("✅ Firecrawl initialized")
            except Exception as e:
                logger.warning(f"⚠️  Firecrawl initialization failed: {e}")
        
        logger.info(f"🔧 Tool availability: Firecrawl={FIRECRAWL_AVAILABLE}, Crawl4AI={CRAWL4AI_AVAILABLE}, Playwright={PLAYWRIGHT_AVAILABLE}")
    
    async def __aenter__(self):
        """Initialize async context with connection pooling"""
        connector = aiohttp.TCPConnector(
            limit=30,  # Increased connection limit
            limit_per_host=8,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=20, sock_read=45)
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    async def crawl_premium_sources(self) -> Dict[str, Any]:
        """Crawl premium AI sources using modern tools with intelligent fallbacks"""
        if not self.session:
            raise CrawlingError("Crawler not initialized. Use async context manager.")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "crawler_version": "modern_v1.0",
            "tools_used": [],
            "rss_articles": [],
            "web_pages": [],
            "stats": {"total_sources": 0, "successful": 0, "failed": 0, "by_tool": {}},
            "source_details": []
        }
        
        # Process RSS feeds
        rss_sources = self.PREMIUM_SOURCES["rss_feeds"]
        logger.info(f"🚀 Processing {len(rss_sources)} premium RSS sources")
        
        for source in rss_sources:
            try:
                articles = await self._crawl_rss_modern(source)
                if articles:
                    results["rss_articles"].extend(articles)
                    results["stats"]["successful"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "success",
                        "method": "rss_native",
                        "articles_count": len(articles)
                    })
                    logger.info(f"✅ {source['name']}: {len(articles)} articles")
                else:
                    results["stats"]["failed"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "no_content",
                        "method": "rss_native"
                    })
                    logger.warning(f"⚠️  {source['name']}: No content")
            except Exception as e:
                results["stats"]["failed"] += 1
                results["source_details"].append({
                    "name": source["name"],
                    "url": source["url"],
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ {source['name']}: {e}")
            
            # Rate limiting
            await asyncio.sleep(random.uniform(1, 3))
        
        # Process dynamic websites with modern tools
        web_sources = self.PREMIUM_SOURCES["websites"]
        logger.info(f"🌐 Processing {len(web_sources)} premium websites with modern tools")
        
        for source in web_sources:
            try:
                pages = await self._crawl_website_modern(source)
                if pages:
                    results["web_pages"].extend(pages)
                    results["stats"]["successful"] += 1
                    method = pages[0].get("extraction_method", "unknown")
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "success",
                        "method": method,
                        "pages_count": len(pages)
                    })
                    logger.info(f"✅ {source['name']}: {len(pages)} pages via {method}")
                else:
                    results["stats"]["failed"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "no_content"
                    })
                    logger.warning(f"⚠️  {source['name']}: No content")
            except Exception as e:
                results["stats"]["failed"] += 1
                results["source_details"].append({
                    "name": source["name"],
                    "url": source["url"],
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ {source['name']}: {e}")
            
            # Rate limiting between tools
            await asyncio.sleep(random.uniform(2, 5))
        
        # Final statistics
        results["stats"]["total_sources"] = len(rss_sources) + len(web_sources)
        results["stats"]["by_tool"] = self.stats.copy()
        results["stats"]["total_items"] = len(results["rss_articles"]) + len(results["web_pages"])
        results["tools_used"] = [tool for tool, count in self.stats.items() if count > 0]
        
        success_rate = results["stats"]["successful"] / max(results["stats"]["total_sources"], 1)
        
        logger.info("=" * 60)
        logger.info(f"🎉 Modern crawling completed!")
        logger.info(f"📊 Success rate: {success_rate:.1%}")
        logger.info(f"📈 Total items: {results['stats']['total_items']}")
        logger.info(f"🔧 Tools used: {', '.join(results['tools_used'])}")
        logger.info("=" * 60)
        
        return results
    
    async def _crawl_rss_modern(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Modern RSS crawling with enhanced parsing"""
        url = source["url"]
        headers = {'User-Agent': random.choice(self.USER_AGENTS)}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_rss_enhanced(content, source)
                else:
                    logger.warning(f"RSS HTTP {response.status}: {url}")
                    return []
        except Exception as e:
            logger.error(f"RSS crawl failed {url}: {e}")
            return []
    
    async def _crawl_website_modern(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Modern website crawling using multiple tools with intelligent fallback"""
        url = source["url"]
        
        # Strategy 1: Try Firecrawl (best for AI-ready content)
        if self.firecrawl:
            try:
                logger.info(f"🔥 Trying Firecrawl for {source['name']}")
                result = self.firecrawl.scrape_url(url, formats=['markdown', 'html'])
                if result and result.get('content'):
                    self.stats["firecrawl"] += 1
                    return self._process_firecrawl_result(result, source)
            except Exception as e:
                logger.warning(f"Firecrawl failed for {url}: {e}")
        
        # Strategy 2: Try Crawl4AI (excellent for LLM content)
        if CRAWL4AI_AVAILABLE:
            try:
                logger.info(f"🤖 Trying Crawl4AI for {source['name']}")
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(url)
                    if result and result.success:
                        self.stats["crawl4ai"] += 1
                        return self._process_crawl4ai_result(result, source)
            except Exception as e:
                logger.warning(f"Crawl4AI failed for {url}: {e}")
        
        # Strategy 3: Try Playwright (for dynamic content)
        if PLAYWRIGHT_AVAILABLE and source.get("type") == "dynamic":
            try:
                logger.info(f"🎭 Trying Playwright for {source['name']}")
                result = await self._crawl_with_playwright(url)
                if result:
                    self.stats["playwright"] += 1
                    return self._process_playwright_result(result, source)
            except Exception as e:
                logger.warning(f"Playwright failed for {url}: {e}")
        
        # Strategy 4: Fallback to traditional HTTP + BeautifulSoup
        try:
            logger.info(f"🔙 Using fallback method for {source['name']}")
            result = await self._crawl_with_fallback(url)
            if result:
                self.stats["fallback"] += 1
                return self._process_fallback_result(result, source)
        except Exception as e:
            logger.error(f"All methods failed for {url}: {e}")
        
        return []
    
    async def _crawl_with_playwright(self, url: str) -> Optional[Dict[str, Any]]:
        """Crawl using Playwright for dynamic content"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.set_extra_http_headers({
                    'User-Agent': random.choice(self.USER_AGENTS)
                })
                
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for dynamic content
                await page.wait_for_timeout(3000)
                
                title = await page.title()
                content = await page.content()
                
                return {"title": title, "content": content, "method": "playwright"}
                
            finally:
                await browser.close()
    
    async def _crawl_with_fallback(self, url: str) -> Optional[Dict[str, Any]]:
        """Traditional fallback crawling method"""
        headers = {'User-Agent': random.choice(self.USER_AGENTS)}
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ''
                
                return {
                    "title": title_text,
                    "content": content,
                    "method": "fallback"
                }
            else:
                return None
    
    def _process_firecrawl_result(self, result: Dict[str, Any], source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Firecrawl result into standard format"""
        return [{
            "title": result.get('title', ''),
            "content": result.get('content', ''),
            "markdown": result.get('markdown', ''),
            "url": source['url'],
            "source": source['name'],
            "extraction_method": "firecrawl",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.9  # Firecrawl provides high-quality extraction
        }]
    
    def _process_crawl4ai_result(self, result: Any, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Crawl4AI result into standard format"""
        return [{
            "title": getattr(result, 'title', ''),
            "content": getattr(result, 'cleaned_html', '') or getattr(result, 'markdown', ''),
            "markdown": getattr(result, 'markdown', ''),
            "url": source['url'],
            "source": source['name'],
            "extraction_method": "crawl4ai",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.85  # Crawl4AI provides good LLM-ready content
        }]
    
    def _process_playwright_result(self, result: Dict[str, Any], source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Playwright result into standard format"""
        soup = BeautifulSoup(result['content'], 'html.parser')
        
        # Extract main content
        main_content = self._extract_main_content(soup)
        
        return [{
            "title": result['title'],
            "content": main_content,
            "url": source['url'],
            "source": source['name'],
            "extraction_method": "playwright",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.8  # Good for dynamic content
        }]
    
    def _process_fallback_result(self, result: Dict[str, Any], source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process fallback result into standard format"""
        soup = BeautifulSoup(result['content'], 'html.parser')
        main_content = self._extract_main_content(soup)
        
        return [{
            "title": result['title'],
            "content": main_content,
            "url": source['url'],
            "source": source['name'],
            "extraction_method": "fallback",
            "timestamp": datetime.now().isoformat(),
            "quality_score": 0.6  # Basic extraction quality
        }]
    
    def _parse_rss_enhanced(self, content: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced RSS parsing with better content extraction"""
        try:
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries[:12]:  # Limit to 12 articles
                # Enhanced content extraction
                content_text = ""
                if hasattr(entry, 'content') and entry.content:
                    content_text = entry.content[0].value if entry.content else ""
                elif hasattr(entry, 'summary'):
                    content_text = entry.summary
                elif hasattr(entry, 'description'):
                    content_text = entry.description
                
                # Clean HTML if present
                if content_text:
                    soup = BeautifulSoup(content_text, 'html.parser')
                    content_text = soup.get_text().strip()
                
                article = {
                    "title": getattr(entry, 'title', '').strip(),
                    "url": getattr(entry, 'link', ''),
                    "summary": getattr(entry, 'summary', '').strip(),
                    "content": content_text,
                    "published": getattr(entry, 'published', ''),
                    "author": getattr(entry, 'author', ''),
                    "source": source['name'],
                    "source_url": source['url'],
                    "extraction_method": "rss_enhanced",
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": self._calculate_rss_quality(entry)
                }
                
                if article["title"] and (article["content"] or article["summary"]):
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"RSS parsing failed: {e}")
            return []
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from BeautifulSoup object"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Try to find main content
        main_selectors = ['main', 'article', '.content', '#content', '.post', '.entry']
        
        for selector in main_selectors:
            main_elem = soup.select_one(selector)
            if main_elem:
                text = main_elem.get_text().strip()
                if len(text) > 200:  # Ensure substantial content
                    return text[:3000]  # Limit length
        
        # Fallback to body
        body = soup.find('body')
        if body:
            text = body.get_text().strip()
            return text[:3000] if text else ""
        
        return ""
    
    def _calculate_rss_quality(self, entry) -> float:
        """Calculate quality score for RSS entry"""
        score = 0.5
        
        title = getattr(entry, 'title', '')
        if title and 20 <= len(title) <= 150:
            score += 0.2
        
        if hasattr(entry, 'content') and entry.content:
            score += 0.2
        elif hasattr(entry, 'summary') and len(getattr(entry, 'summary', '')) > 100:
            score += 0.1
        
        if getattr(entry, 'author', ''):
            score += 0.1
        
        if getattr(entry, 'published', ''):
            score += 0.1
        
        return min(1.0, score)
    
    # Legacy compatibility methods
    async def crawl_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy compatibility method"""
        result = await self.crawl_premium_sources()
        return result
    
    async def crawl_multiple(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy compatibility method"""
        result = await self.crawl_premium_sources()
        return [result]
    
    async def validate_source(self, source_config: Dict[str, Any]) -> bool:
        """Validate if a source is accessible"""
        try:
            if not self.session:
                return False
            
            url = source_config.get('url', '')
            if not url:
                return False
            
            headers = {'User-Agent': random.choice(self.USER_AGENTS)}
            async with self.session.head(url, headers=headers) as response:
                return response.status < 400
                
        except Exception:
            return False