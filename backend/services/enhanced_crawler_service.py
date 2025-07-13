"""
Enhanced crawler service with modern best practices for 2024.
Implements rate limiting, retry mechanisms, user agent rotation, and high-quality AI sources.
"""

import asyncio
import random
import time
import ssl
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import json
import logging

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.interfaces import ICrawlerService, IAuthService
from core.exceptions import CrawlingError
from config import Settings

logger = logging.getLogger(__name__)


class EnhancedCrawlerService(ICrawlerService):
    """Enhanced web crawler service with 2024 best practices."""
    
    # High-quality AI news sources verified for 2024
    PREMIUM_AI_SOURCES = {
        "rss_feeds": [
            {
                "name": "Google AI Blog",
                "url": "https://ai.googleblog.com/feeds/posts/default",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "Berkeley AI Research (BAIR)",
                "url": "https://bair.berkeley.edu/blog/feed.xml",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "MIT AI News",
                "url": "https://news.mit.edu/rss/topic/artificial-intelligence",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "DeepMind Research",
                "url": "https://deepmind.google/discover/blog/rss.xml",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "OpenAI Research",
                "url": "https://openai.com/research/rss.xml",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "Anthropic News", 
                "url": "https://www.anthropic.com/news/rss",
                "category": "research",
                "priority": "high"
            },
            {
                "name": "VentureBeat AI",
                "url": "https://venturebeat.com/ai/feed/",
                "category": "news",
                "priority": "medium"
            },
            {
                "name": "The Gradient",
                "url": "https://thegradient.pub/rss/",
                "category": "analysis",
                "priority": "medium"
            },
            {
                "name": "Towards Data Science",
                "url": "https://towardsdatascience.com/feed",
                "category": "education",
                "priority": "medium"
            },
            {
                "name": "Machine Learning Mastery",
                "url": "https://machinelearningmastery.com/feed/",
                "category": "education",
                "priority": "medium"
            }
        ],
        "websites": [
            {
                "name": "ArXiv AI Latest",
                "url": "https://arxiv.org/list/cs.AI/recent",
                "category": "research",
                "priority": "high",
                "requires_parsing": True
            },
            {
                "name": "Papers With Code Latest",
                "url": "https://paperswithcode.com/latest",
                "category": "research", 
                "priority": "high",
                "requires_parsing": True
            },
            {
                "name": "Hugging Face Papers",
                "url": "https://huggingface.co/papers",
                "category": "research",
                "priority": "medium",
                "requires_parsing": True
            }
        ]
    }
    
    # Updated user agent strings for 2024/2025 - based on real browser statistics
    USER_AGENTS = [
        # Chrome 124+ (Most popular - 65% market share)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        
        # Edge 124+ (Growing market share)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        
        # Firefox 125+ (12% market share)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        
        # Safari 17+ (18% market share)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        
        # Mobile Chrome (Android - for mobile-optimized sites)
        "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36"
    ]
    
    # Site-specific user agents for better success rates
    SITE_SPECIFIC_AGENTS = {
        'arxiv.org': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        'github.com': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        'reddit.com': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        'twitter.com': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        'x.com': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        'openai.com': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        'deepmind.google': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    def __init__(self, settings: Settings, auth_service: IAuthService):
        self.settings = settings
        self.auth_service = auth_service
        self.config = settings.agents.crawler if hasattr(settings, 'agents') else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
        self.failed_sources: Set[str] = set()
        self.source_stats = {}
        
    async def __aenter__(self):
        """Async context manager entry with enhanced configuration."""
        # Create SSL context with relaxed settings for compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create connector with optimized settings for 2024
        connector = aiohttp.TCPConnector(
            limit=30,  # Increased total connection limit
            limit_per_host=8,  # Increased per-host connection limit  
            ttl_dns_cache=600,  # Longer DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=45,  # Longer keepalive
            enable_cleanup_closed=True,
            ssl=ssl_context,  # Use custom SSL context
            force_close=False  # Reuse connections when possible
        )
        
        # Create timeout optimized for modern web crawling
        timeout = aiohttp.ClientTimeout(
            total=60,  # Increased total timeout for slow sites
            connect=20,  # Increased connection timeout
            sock_read=45,  # Increased socket read timeout
            sock_connect=15  # Socket connection timeout
        )
        
        # Enhanced base headers for 2024 compatibility
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',  # Added zstd support
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        }
        
        # Create session with enhanced configuration
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
            trace_request_ctx={'start_time': time.time()},  # Add request timing
            raise_for_status=False,  # Handle status codes manually
            auto_decompress=True  # Auto-decompress responses
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_premium_sources(self) -> Dict[str, Any]:
        """Crawl high-quality AI sources with advanced error handling."""
        if not self.session:
            raise CrawlingError("Crawler not initialized. Use async context manager.")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "rss_articles": [],
            "web_pages": [],
            "stats": {
                "total_sources": 0,
                "successful_sources": 0,
                "failed_sources": 0,
                "total_articles": 0
            },
            "source_details": []
        }
        
        # Process RSS feeds
        rss_sources = self.PREMIUM_AI_SOURCES["rss_feeds"]
        for source in rss_sources:
            try:
                domain = urlparse(source["url"]).netloc
                await self.rate_limiter.wait(domain)
                articles = await self._crawl_rss_with_retry(source)
                self.rate_limiter.record_success(domain)
                if articles:
                    results["rss_articles"].extend(articles)
                    results["stats"]["successful_sources"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "success",
                        "articles_count": len(articles),
                        "category": source["category"]
                    })
                else:
                    results["stats"]["failed_sources"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "no_content",
                        "category": source["category"]
                    })
            except Exception as e:
                logger.error(f"Failed to crawl RSS source {source['name']}: {e}")
                domain = urlparse(source["url"]).netloc
                self.rate_limiter.record_failure(domain)
                results["stats"]["failed_sources"] += 1
                results["source_details"].append({
                    "name": source["name"],
                    "url": source["url"],
                    "status": "error",
                    "error": str(e),
                    "category": source["category"]
                })
        
        # Process website sources
        web_sources = self.PREMIUM_AI_SOURCES["websites"]
        for source in web_sources:
            try:
                domain = urlparse(source["url"]).netloc
                await self.rate_limiter.wait(domain)
                pages = await self._crawl_website_with_retry(source)
                self.rate_limiter.record_success(domain)
                if pages:
                    results["web_pages"].extend(pages)
                    results["stats"]["successful_sources"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "success",
                        "pages_count": len(pages),
                        "category": source["category"]
                    })
                else:
                    results["stats"]["failed_sources"] += 1
                    results["source_details"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": "no_content",
                        "category": source["category"]
                    })
            except Exception as e:
                logger.error(f"Failed to crawl website source {source['name']}: {e}")
                domain = urlparse(source["url"]).netloc
                self.rate_limiter.record_failure(domain)
                results["stats"]["failed_sources"] += 1
                results["source_details"].append({
                    "name": source["name"],
                    "url": source["url"],
                    "status": "error",
                    "error": str(e),
                    "category": source["category"]
                })
        
        results["stats"]["total_sources"] = len(rss_sources) + len(web_sources)
        results["stats"]["total_articles"] = len(results["rss_articles"]) + len(results["web_pages"])
        
        return results
    
    @retry(
        stop=stop_after_attempt(4),  # Increased retry attempts
        wait=wait_exponential(multiplier=2, min=3, max=30),  # Better backoff strategy
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, aiohttp.ServerTimeoutError))
    )
    async def _crawl_rss_with_retry(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl RSS feed with enhanced retry logic and error handling."""
        url = source["url"]
        headers = self._get_random_headers(url)
        
        # Add intelligent delay based on domain
        domain = urlparse(url).netloc
        base_delay = self._get_domain_specific_delay(domain)
        await asyncio.sleep(random.uniform(base_delay, base_delay * 1.5))
        
        try:
            async with self.session.get(url, headers=headers, ssl=False) as response:
                # Handle different status codes intelligently
                if response.status == 200:
                    content = await response.text(encoding='utf-8', errors='replace')
                    return self._parse_rss_content(content, source)
                elif response.status == 429:
                    # Rate limited - exponential backoff with jitter
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = min(int(retry_after) if retry_after.isdigit() else 60, 300)
                    jitter = random.uniform(0.5, 1.5)
                    await asyncio.sleep(wait_time * jitter)
                    raise aiohttp.ClientError(f"Rate limited: {response.status}")
                elif response.status in [301, 302, 303, 307, 308]:
                    # Handle redirects manually for better control
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        logger.info(f"Following redirect from {url} to {redirect_url}")
                        source_copy = source.copy()
                        source_copy['url'] = redirect_url
                        return await self._crawl_rss_with_retry(source_copy)
                elif response.status == 403:
                    # Forbidden - try with different user agent and Cloudflare handling
                    headers_alt = self._get_alternative_headers(url)
                    async with self.session.get(url, headers=headers_alt, ssl=False) as alt_response:
                        if alt_response.status == 200:
                            content = await alt_response.text(encoding='utf-8', errors='replace')
                            if self._validate_response_content(content, "rss"):
                                return self._parse_rss_content(content, source)
                    
                    # Try Cloudflare bypass
                    cloudflare_content = await self._handle_cloudflare_protection(url)
                    if cloudflare_content and self._validate_response_content(cloudflare_content, "rss"):
                        return self._parse_rss_content(cloudflare_content, source)
                    
                    logger.warning(f"Access forbidden for RSS feed: {url}")
                    return []
                elif response.status >= 500:
                    # Server error - retry with exponential backoff
                    raise aiohttp.ClientError(f"Server error: {response.status}")
                else:
                    logger.warning(f"RSS feed returned status {response.status}: {url}")
                    return []
        except (aiohttp.ClientConnectorError, aiohttp.ClientSSLError) as e:
            logger.warning(f"Connection error for {url}: {e}")
            # Try with different SSL settings
            try:
                connector = aiohttp.TCPConnector(ssl=False, verify_ssl=False)
                async with aiohttp.ClientSession(connector=connector) as fallback_session:
                    async with fallback_session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text(encoding='utf-8', errors='replace')
                            return self._parse_rss_content(content, source)
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"Error crawling RSS {url}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(4),  # Increased retry attempts
        wait=wait_exponential(multiplier=2, min=3, max=30),  # Better backoff strategy
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, aiohttp.ServerTimeoutError))
    )
    async def _crawl_website_with_retry(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl website with enhanced retry logic and error handling."""
        url = source["url"]
        headers = self._get_random_headers(url)
        
        # Add intelligent delay based on domain
        domain = urlparse(url).netloc
        base_delay = self._get_domain_specific_delay(domain)
        await asyncio.sleep(random.uniform(base_delay, base_delay * 1.5))
        
        try:
            async with self.session.get(url, headers=headers, ssl=False, allow_redirects=True) as response:
                # Handle different status codes intelligently
                if response.status == 200:
                    content = await response.text(encoding='utf-8', errors='replace')
                    return self._parse_website_content(content, source)
                elif response.status == 429:
                    # Rate limited - exponential backoff with jitter
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = min(int(retry_after) if retry_after.isdigit() else 60, 300)
                    jitter = random.uniform(0.5, 1.5)
                    await asyncio.sleep(wait_time * jitter)
                    raise aiohttp.ClientError(f"Rate limited: {response.status}")
                elif response.status == 403:
                    # Forbidden - try with different user agent and headers
                    headers_alt = self._get_alternative_headers(url)
                    async with self.session.get(url, headers=headers_alt, ssl=False) as alt_response:
                        if alt_response.status == 200:
                            content = await alt_response.text(encoding='utf-8', errors='replace')
                            if self._validate_response_content(content, "html"):
                                return self._parse_website_content(content, source)
                    
                    # Try Cloudflare bypass
                    cloudflare_content = await self._handle_cloudflare_protection(url)
                    if cloudflare_content and self._validate_response_content(cloudflare_content, "html"):
                        return self._parse_website_content(cloudflare_content, source)
                    
                    logger.warning(f"Access forbidden for website: {url}")
                    return []
                elif response.status == 404:
                    logger.warning(f"Website not found: {url}")
                    return []
                elif response.status >= 500:
                    # Server error - retry with exponential backoff
                    raise aiohttp.ClientError(f"Server error: {response.status}")
                else:
                    logger.warning(f"Website returned status {response.status}: {url}")
                    return []
        except (aiohttp.ClientConnectorError, aiohttp.ClientSSLError) as e:
            logger.warning(f"Connection error for {url}: {e}")
            # Try with different SSL settings
            try:
                connector = aiohttp.TCPConnector(ssl=False, verify_ssl=False)
                async with aiohttp.ClientSession(connector=connector) as fallback_session:
                    async with fallback_session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text(encoding='utf-8', errors='replace')
                            return self._parse_website_content(content, source)
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"Error crawling website {url}: {e}")
            raise
    
    def _get_random_headers(self, url: str = "") -> Dict[str, str]:
        """Get randomized headers to avoid detection with site-specific optimization."""
        # Get site-specific user agent if available
        domain = urlparse(url).netloc if url else ""
        user_agent = self.SITE_SPECIFIC_AGENTS.get(domain, random.choice(self.USER_AGENTS))
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-US,en;q=0.9,zh-CN;q=0.8',
                'en-GB,en;q=0.9',
                'en-US,en;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': random.choice(['"Windows"', '"macOS"', '"Linux"'])
        }
        
        # Add randomized optional headers for better human simulation
        if random.random() < 0.4:
            headers['Cache-Control'] = random.choice(['max-age=0', 'no-cache', 'no-store'])
        
        if random.random() < 0.3:
            headers['Pragma'] = 'no-cache'
        
        # Add viewport hint for mobile optimization
        if 'Mobile' in user_agent:
            headers['Viewport-Width'] = str(random.randint(360, 414))
        
        return headers
    
    def _parse_rss_content(self, content: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse RSS content with enhanced error handling."""
        try:
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parsing issues for {source['url']}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:15]:  # Limit to 15 articles per feed
                try:
                    article = {
                        "id": entry.get('id', entry.get('link', '')),
                        "title": entry.get('title', '').strip(),
                        "content": self._extract_content_from_entry(entry),
                        "summary": entry.get('summary', '').strip(),
                        "url": entry.get('link', ''),
                        "published": entry.get('published', ''),
                        "author": entry.get('author', ''),
                        "category": source.get('category', ''),
                        "source": source['name'],
                        "source_url": source['url'],
                        "crawled_at": datetime.now().isoformat(),
                        "quality_score": self._calculate_quality_score(entry)
                    }
                    
                    # Only include articles with sufficient quality
                    if article["quality_score"] >= 0.6:
                        articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Error parsing RSS entry: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS content: {e}")
            return []
    
    def _extract_content_from_entry(self, entry) -> str:
        """Extract content from RSS entry with fallbacks."""
        # Try different content fields
        content_sources = [
            entry.get('content', []),
            entry.get('summary', ''),
            entry.get('description', '')
        ]
        
        for content_source in content_sources:
            if isinstance(content_source, list) and content_source:
                # Handle content array
                for content_item in content_source:
                    if isinstance(content_item, dict):
                        text = content_item.get('value', '')
                        if text and len(text.strip()) > 100:
                            return BeautifulSoup(text, 'html.parser').get_text().strip()
            elif isinstance(content_source, str) and len(content_source.strip()) > 100:
                return BeautifulSoup(content_source, 'html.parser').get_text().strip()
        
        return ""
    
    def _parse_website_content(self, content: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse website content with intelligent extraction."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            pages = []
            
            if source.get('requires_parsing'):
                # Extract multiple items for listing pages
                items = self._extract_multiple_items(soup, source)
                pages.extend(items)
            else:
                # Extract single page content
                page = self._extract_single_page(soup, source)
                if page:
                    pages.append(page)
            
            return pages
            
        except Exception as e:
            logger.error(f"Error parsing website content: {e}")
            return []
    
    def _extract_multiple_items(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract multiple items from listing pages."""
        items = []
        
        # Different strategies based on the source
        if 'arxiv.org' in source['url']:
            items = self._extract_arxiv_papers(soup, source)
        elif 'paperswithcode.com' in source['url']:
            items = self._extract_pwc_papers(soup, source)
        elif 'huggingface.co' in source['url']:
            items = self._extract_hf_papers(soup, source)
        
        return items[:10]  # Limit to 10 items
    
    def _extract_arxiv_papers(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract papers from ArXiv recent listings."""
        papers = []
        
        # ArXiv has a specific structure
        paper_elements = soup.find_all('dd')
        
        for element in paper_elements[:15]:
            try:
                title_elem = element.find('div', class_='list-title')
                authors_elem = element.find('div', class_='list-authors')
                abstract_elem = element.find('p', class_='mathjax')
                
                if title_elem:
                    title = title_elem.get_text().replace('Title:', '').strip()
                    authors = authors_elem.get_text().replace('Authors:', '').strip() if authors_elem else ''
                    abstract = abstract_elem.get_text().strip() if abstract_elem else ''
                    
                    # Try to find paper link
                    link_elem = element.find('a', href=True)
                    paper_url = urljoin(source['url'], link_elem['href']) if link_elem else source['url']
                    
                    paper = {
                        "title": title,
                        "content": abstract,
                        "summary": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                        "author": authors,
                        "url": paper_url,
                        "source": source['name'],
                        "source_url": source['url'],
                        "category": source['category'],
                        "type": "research_paper",
                        "crawled_at": datetime.now().isoformat(),
                        "quality_score": 0.8  # ArXiv papers are generally high quality
                    }
                    
                    papers.append(paper)
                    
            except Exception as e:
                logger.warning(f"Error extracting ArXiv paper: {e}")
                continue
        
        return papers
    
    def _extract_pwc_papers(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract papers from Papers With Code."""
        papers = []
        
        # Papers With Code structure
        paper_elements = soup.find_all('div', class_='paper-card') or soup.find_all('h1') or soup.find_all('article')
        
        for element in paper_elements[:15]:
            try:
                title_elem = element.find('h1') or element.find('h2') or element.find('h3')
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    
                    # Find description or abstract
                    desc_elem = element.find('p') or element.find('div', class_='paper-abstract')
                    description = desc_elem.get_text().strip() if desc_elem else ''
                    
                    # Find link
                    link_elem = element.find('a', href=True) or title_elem.find('a', href=True)
                    paper_url = urljoin(source['url'], link_elem['href']) if link_elem else source['url']
                    
                    paper = {
                        "title": title,
                        "content": description,
                        "summary": description[:200] + "..." if len(description) > 200 else description,
                        "url": paper_url,
                        "source": source['name'],
                        "source_url": source['url'],
                        "category": source['category'],
                        "type": "research_paper",
                        "crawled_at": datetime.now().isoformat(),
                        "quality_score": 0.8
                    }
                    
                    papers.append(paper)
                    
            except Exception as e:
                logger.warning(f"Error extracting PWC paper: {e}")
                continue
        
        return papers
    
    def _extract_hf_papers(self, soup: BeautifulSoup, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract papers from Hugging Face."""
        papers = []
        
        # Hugging Face structure
        paper_elements = soup.find_all('article') or soup.find_all('div', class_='paper')
        
        for element in paper_elements[:15]:
            try:
                title_elem = element.find('h3') or element.find('h2') or element.find('h1')
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    
                    # Find abstract or description
                    abstract_elem = element.find('p') or element.find('div', class_='abstract')
                    abstract = abstract_elem.get_text().strip() if abstract_elem else ''
                    
                    # Find authors
                    authors_elem = element.find('div', class_='authors') or element.find('span', class_='author')
                    authors = authors_elem.get_text().strip() if authors_elem else ''
                    
                    # Find link
                    link_elem = element.find('a', href=True)
                    paper_url = urljoin(source['url'], link_elem['href']) if link_elem else source['url']
                    
                    paper = {
                        "title": title,
                        "content": abstract,
                        "summary": abstract[:200] + "..." if len(abstract) > 200 else abstract,
                        "author": authors,
                        "url": paper_url,
                        "source": source['name'],
                        "source_url": source['url'],
                        "category": source['category'],
                        "type": "research_paper",
                        "crawled_at": datetime.now().isoformat(),
                        "quality_score": 0.8
                    }
                    
                    papers.append(paper)
                    
            except Exception as e:
                logger.warning(f"Error extracting HF paper: {e}")
                continue
        
        return papers
    
    def _extract_single_page(self, soup: BeautifulSoup, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content from a single page."""
        try:
            title_elem = soup.find('title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else ''
            
            # Find main content
            content_elem = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', class_='content') or
                soup.find('div', id='content')
            )
            
            content = ''
            if content_elem:
                content = content_elem.get_text().strip()
            
            if not title and not content:
                return None
            
            return {
                "title": title,
                "content": content,
                "summary": content[:300] + "..." if len(content) > 300 else content,
                "url": source['url'],
                "source": source['name'],
                "source_url": source['url'],
                "category": source['category'],
                "type": "webpage",
                "crawled_at": datetime.now().isoformat(),
                "quality_score": self._calculate_page_quality_score(title, content)
            }
            
        except Exception as e:
            logger.error(f"Error extracting single page: {e}")
            return None
    
    def _calculate_quality_score(self, entry) -> float:
        """Calculate quality score for RSS entry."""
        score = 0.5
        
        title = entry.get('title', '')
        content = self._extract_content_from_entry(entry)
        
        # Title quality
        if title and len(title) > 10:
            score += 0.1
        if len(title) < 200:
            score += 0.1
        
        # Content quality
        if content and len(content) > 100:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        
        # Metadata presence
        if entry.get('author'):
            score += 0.05
        if entry.get('published'):
            score += 0.05
        if entry.get('summary'):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_page_quality_score(self, title: str, content: str) -> float:
        """Calculate quality score for webpage with enhanced metrics."""
        score = 0.3  # Lower base score to be more selective
        
        # Title quality scoring
        if title:
            title_len = len(title.strip())
            if 10 <= title_len <= 150:  # Optimal title length
                score += 0.15
            elif title_len > 150:
                score += 0.05  # Penalize overly long titles
            
            # Check for meaningful title (not just domain/site name)
            if not any(word in title.lower() for word in ['404', 'error', 'not found', 'access denied']):
                score += 0.1
        
        # Content quality scoring
        if content:
            content_len = len(content.strip())
            if content_len > 100:
                score += 0.1
            if content_len > 500:
                score += 0.15
            if content_len > 1500:
                score += 0.1
            
            # Penalize overly long content (likely scraped poorly)
            if content_len > 50000:
                score -= 0.2
            
            # Check content quality indicators
            content_lower = content.lower()
            quality_indicators = ['published', 'author', 'date', 'article', 'research']
            quality_score = sum(1 for indicator in quality_indicators if indicator in content_lower)
            score += min(0.1, quality_score * 0.02)
            
            # Penalize spam indicators
            spam_indicators = ['click here', 'buy now', 'limited time', 'act now']
            spam_score = sum(1 for spam in spam_indicators if spam in content_lower)
            score -= min(0.3, spam_score * 0.1)
        
        return max(0.0, min(1.0, score))
    
    def _validate_response_content(self, content: str, expected_type: str = "html") -> bool:
        """Validate response content quality and type."""
        if not content or len(content.strip()) < 50:
            return False
        
        content_lower = content.lower()
        
        # Check for error pages
        error_indicators = [
            '404 not found', '403 forbidden', '500 internal server error',
            'access denied', 'page not found', 'server error',
            'temporarily unavailable', 'maintenance mode'
        ]
        
        if any(error in content_lower for error in error_indicators):
            return False
        
        # Validate content type
        if expected_type == "rss":
            return any(tag in content_lower for tag in ['<rss', '<feed', '<channel', '<item', '<entry'])
        elif expected_type == "html":
            return any(tag in content_lower for tag in ['<html', '<body', '<head', '<div', '<article'])
        
        return True
    
    async def _handle_cloudflare_protection(self, url: str) -> Optional[str]:
        """Handle Cloudflare protection if detected."""
        try:
            # Basic Cloudflare bypass attempt with different headers
            bypass_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': f'https://{urlparse(url).netloc}/',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Wait a bit longer for Cloudflare
            await asyncio.sleep(random.uniform(3, 6))
            
            async with self.session.get(url, headers=bypass_headers) as response:
                if response.status == 200:
                    content = await response.text()
                    if self._validate_response_content(content, "html"):
                        return content
            
            return None
        except Exception:
            return None
    
    # Legacy compatibility methods
    async def crawl_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy compatibility method."""
        return await self.crawl_premium_sources()
    
    async def crawl_multiple(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy compatibility method."""
        result = await self.crawl_premium_sources()
        return [result]
    
    async def validate_source(self, source_config: Dict[str, Any]) -> bool:
        """Validate if a source is accessible."""
        try:
            if not self.session:
                return False
            
            url = source_config.get('url', '')
            if not url:
                return False
            
            headers = self._get_random_headers()
            async with self.session.head(url, headers=headers) as response:
                return response.status < 400
                
        except Exception:
            return False


    def _get_domain_specific_delay(self, domain: str) -> float:
        """Get domain-specific delay to respect server limits."""
        domain_delays = {
            'arxiv.org': 3.0,  # Academic sites often have strict limits
            'github.com': 2.0,
            'reddit.com': 4.0,  # Reddit is strict about rate limiting
            'twitter.com': 5.0,
            'x.com': 5.0,
            'google.com': 1.0,
            'openai.com': 3.0,
            'anthropic.com': 3.0,
            'deepmind.com': 2.0,
            'default': 1.5
        }
        
        return domain_delays.get(domain, domain_delays['default'])
    
    def _get_alternative_headers(self, url: str) -> Dict[str, str]:
        """Get alternative headers for 403 errors."""
        # Use a more basic browser profile for strict sites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        domain = urlparse(url).netloc
        
        # Site-specific header adjustments
        if 'arxiv.org' in domain:
            headers['User-Agent'] = 'Mozilla/5.0 (compatible; Academic Research Bot)'
            headers['Accept'] = 'application/rss+xml, application/xml, text/xml'
        elif 'github.com' in domain:
            headers['Accept'] = 'application/vnd.github.v3+json, text/html'
        
        return headers


class RateLimiter:
    """Smart rate limiter with adaptive delays and domain-specific handling."""
    
    def __init__(self, base_delay: float = 2.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.domain_stats = {}  # Track per-domain statistics
        self.global_last_request = 0
    
    async def wait(self, domain: str = "default"):
        """Wait appropriate amount of time before next request with domain-specific logic."""
        current_time = time.time()
        
        # Initialize domain stats if not exists
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                'last_request_time': 0,
                'consecutive_failures': 0,
                'total_requests': 0,
                'successful_requests': 0
            }
        
        stats = self.domain_stats[domain]
        time_since_last = current_time - stats['last_request_time']
        global_time_since_last = current_time - self.global_last_request
        
        # Calculate delay based on failure count and domain
        base_delay = self._get_domain_base_delay(domain)
        delay = base_delay * (1.8 ** stats['consecutive_failures'])
        delay = min(delay, self.max_delay)
        
        # Add intelligent jitter based on success rate
        success_rate = stats['successful_requests'] / max(stats['total_requests'], 1)
        jitter_factor = 0.5 if success_rate > 0.8 else 0.8
        delay += random.uniform(0, delay * jitter_factor)
        
        # Ensure minimum global delay between any requests
        min_global_delay = 0.5
        if global_time_since_last < min_global_delay:
            await asyncio.sleep(min_global_delay - global_time_since_last)
        
        # Wait for domain-specific delay
        if time_since_last < delay:
            await asyncio.sleep(delay - time_since_last)
        
        # Update timers
        stats['last_request_time'] = time.time()
        stats['total_requests'] += 1
        self.global_last_request = time.time()
    
    def _get_domain_base_delay(self, domain: str) -> float:
        """Get base delay for specific domains."""
        domain_delays = {
            'arxiv.org': 4.0,
            'github.com': 2.5,
            'reddit.com': 6.0,
            'twitter.com': 8.0,
            'x.com': 8.0,
            'openai.com': 3.0,
            'anthropic.com': 3.0,
            'deepmind.com': 2.5,
            'google.com': 1.5,
            'default': 2.0
        }
        
        return domain_delays.get(domain, domain_delays['default'])
    
    def record_success(self, domain: str = "default"):
        """Record successful request for domain."""
        if domain in self.domain_stats:
            stats = self.domain_stats[domain]
            stats['consecutive_failures'] = max(0, stats['consecutive_failures'] - 1)
            stats['successful_requests'] += 1
    
    def record_failure(self, domain: str = "default"):
        """Record failed request for domain."""
        if domain in self.domain_stats:
            self.domain_stats[domain]['consecutive_failures'] += 1
    
    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a specific domain."""
        return self.domain_stats.get(domain, {})