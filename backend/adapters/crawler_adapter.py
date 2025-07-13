"""
Crawler service adapter implementing clean architecture.
Adapts modern crawler tools to the clean architecture interfaces.
"""

import asyncio
import aiohttp
import feedparser
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from core.clean_architecture import Source, SourceType, CrawlerService

logger = logging.getLogger(__name__)


class ModernCrawlerAdapter:
    """Modern crawler adapter following clean architecture"""
    
    def __init__(self, firecrawl_api_key: Optional[str] = None):
        self.firecrawl_api_key = firecrawl_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self._tools_available = self._check_tools()
    
    def _check_tools(self) -> Dict[str, bool]:
        """Check availability of modern tools"""
        tools = {}
        
        # Check Firecrawl
        try:
            from firecrawl import FirecrawlApp
            tools['firecrawl'] = bool(self.firecrawl_api_key)
        except ImportError:
            tools['firecrawl'] = False
        
        # Check Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            tools['crawl4ai'] = True
        except ImportError:
            tools['crawl4ai'] = False
        
        # Check Playwright
        try:
            from playwright.async_api import async_playwright
            tools['playwright'] = True
        except ImportError:
            tools['playwright'] = False
        
        # Fallback always available
        tools['fallback'] = True
        
        return tools
    
    async def __aenter__(self):
        """Initialize async context"""
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=5,
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; AI-Content-Aggregator/2.0)'
            }
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup async context"""
        if self.session:
            await self.session.close()
    
    async def crawl_source(self, source: Source) -> Dict[str, Any]:
        """Crawl a single source using best available tool"""
        logger.info(f"Crawling source: {source.name} ({source.type.value})")
        
        try:
            if source.type == SourceType.RSS:
                return await self._crawl_rss(source)
            else:
                return await self._crawl_website(source)
        
        except Exception as e:
            logger.error(f"Failed to crawl {source.name}: {e}")
            return {
                'source_id': source.id,
                'source_name': source.name,
                'url': source.url,
                'success': False,
                'error': str(e),
                'items': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def validate_source_url(self, url: str) -> bool:
        """Validate if a source URL is accessible"""
        try:
            if not self.session:
                return False
            
            async with self.session.head(url) as response:
                return response.status < 400
        except Exception:
            return False
    
    async def _crawl_rss(self, source: Source) -> Dict[str, Any]:
        """Crawl RSS source"""
        try:
            async with self.session.get(source.url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                items = []
                for entry in feed.entries[:10]:  # Limit to 10 items
                    item = {
                        'title': entry.get('title', ''),
                        'content': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'author': entry.get('author', ''),
                        'published': entry.get('published', ''),
                        'category': source.category,
                        'source_id': source.id,
                        'extraction_method': 'rss'
                    }
                    
                    # Clean content
                    if item['content']:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(item['content'], 'html.parser')
                        item['content'] = soup.get_text().strip()
                    
                    if item['title']:  # Only include if has title
                        items.append(item)
                
                return {
                    'source_id': source.id,
                    'source_name': source.name,
                    'url': source.url,
                    'success': True,
                    'items': items,
                    'extraction_method': 'rss',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            raise Exception(f"RSS crawling failed: {e}")
    
    async def _crawl_website(self, source: Source) -> Dict[str, Any]:
        """Crawl website using best available tool"""
        # Try tools in order of preference
        if self._tools_available.get('firecrawl') and self.firecrawl_api_key:
            try:
                return await self._crawl_with_firecrawl(source)
            except Exception as e:
                logger.warning(f"Firecrawl failed for {source.name}: {e}")
        
        if self._tools_available.get('crawl4ai'):
            try:
                return await self._crawl_with_crawl4ai(source)
            except Exception as e:
                logger.warning(f"Crawl4AI failed for {source.name}: {e}")
        
        if self._tools_available.get('playwright'):
            try:
                return await self._crawl_with_playwright(source)
            except Exception as e:
                logger.warning(f"Playwright failed for {source.name}: {e}")
        
        # Fallback to basic HTTP
        return await self._crawl_with_fallback(source)
    
    async def _crawl_with_firecrawl(self, source: Source) -> Dict[str, Any]:
        """Crawl using Firecrawl"""
        from firecrawl import FirecrawlApp
        
        app = FirecrawlApp(api_key=self.firecrawl_api_key)
        result = app.scrape_url(source.url, formats=['markdown'])
        
        if not result or not result.get('content'):
            raise Exception("No content returned from Firecrawl")
        
        item = {
            'title': result.get('title', ''),
            'content': result.get('content', ''),
            'url': source.url,
            'category': source.category,
            'source_id': source.id,
            'extraction_method': 'firecrawl'
        }
        
        return {
            'source_id': source.id,
            'source_name': source.name,
            'url': source.url,
            'success': True,
            'items': [item] if item['content'] else [],
            'extraction_method': 'firecrawl',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _crawl_with_crawl4ai(self, source: Source) -> Dict[str, Any]:
        """Crawl using Crawl4AI"""
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(source.url)
            
            if not result or not result.success:
                raise Exception("Crawl4AI failed to crawl")
            
            item = {
                'title': getattr(result, 'title', ''),
                'content': getattr(result, 'markdown', '') or getattr(result, 'cleaned_html', ''),
                'url': source.url,
                'category': source.category,
                'source_id': source.id,
                'extraction_method': 'crawl4ai'
            }
            
            return {
                'source_id': source.id,
                'source_name': source.name,
                'url': source.url,
                'success': True,
                'items': [item] if item['content'] else [],
                'extraction_method': 'crawl4ai',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _crawl_with_playwright(self, source: Source) -> Dict[str, Any]:
        """Crawl using Playwright"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(source.url, wait_until='networkidle', timeout=30000)
                
                title = await page.title()
                content = await page.content()
                
                # Extract text content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer']):
                    element.decompose()
                
                text_content = soup.get_text().strip()
                
                item = {
                    'title': title,
                    'content': text_content[:3000] if text_content else '',  # Limit length
                    'url': source.url,
                    'category': source.category,
                    'source_id': source.id,
                    'extraction_method': 'playwright'
                }
                
                return {
                    'source_id': source.id,
                    'source_name': source.name,
                    'url': source.url,
                    'success': True,
                    'items': [item] if item['content'] else [],
                    'extraction_method': 'playwright',
                    'timestamp': datetime.now().isoformat()
                }
            
            finally:
                await browser.close()
    
    async def _crawl_with_fallback(self, source: Source) -> Dict[str, Any]:
        """Fallback crawling with basic HTTP"""
        async with self.session.get(source.url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            content = await response.text()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            text_content = soup.get_text().strip()
            
            item = {
                'title': title_text,
                'content': text_content[:2000] if text_content else '',  # Limit length
                'url': source.url,
                'category': source.category,
                'source_id': source.id,
                'extraction_method': 'fallback'
            }
            
            return {
                'source_id': source.id,
                'source_name': source.name,
                'url': source.url,
                'success': True,
                'items': [item] if item['content'] else [],
                'extraction_method': 'fallback',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Get available tools status"""
        return self._tools_available.copy()