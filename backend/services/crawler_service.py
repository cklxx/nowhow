"""
Crawler service implementation for content crawling operations.
"""

import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse

from config import Settings
from core.interfaces import ICrawlerService, IAuthService
from core.exceptions import CrawlingError

logger = logging.getLogger(__name__)


class WebCrawlerService(ICrawlerService):
    """Web crawler service implementation."""
    
    def __init__(self, settings: Settings, auth_service: IAuthService):
        self.settings = settings
        self.auth_service = auth_service
        self.config = settings.agents.crawler
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Safe header conversion that handles ConfigSection objects
        headers = {}
        if hasattr(self.config, 'headers') and self.config.headers:
            if hasattr(self.config.headers, 'to_dict'):
                try:
                    headers = self.config.headers.to_dict()
                except Exception:
                    headers = {}
            elif hasattr(self.config.headers, '__dict__'):
                # Handle ConfigSection objects that don't have to_dict
                try:
                    headers = {k: v for k, v in self.config.headers.__dict__.items() 
                             if not k.startswith('_') and isinstance(v, (str, int, float, bool))}
                except Exception:
                    headers = {}
            else:
                try:
                    headers = dict(self.config.headers)
                except (TypeError, ValueError):
                    headers = {}
        
        # Set a default User-Agent if none exists
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)'
            
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=getattr(self.config, 'timeout', 30)),
            headers=headers,
            connector=aiohttp.TCPConnector(limit=getattr(self.config, 'concurrent_requests', 10))
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a single source."""
        try:
            source_type = source_config.get('type', 'html')
            source_url = source_config.get('url', '')
            
            if not source_url:
                raise CrawlingError("Source URL is required")
            
            logger.info(f"Crawling source: {source_url} (type: {source_type})")
            
            # Get authentication if needed
            auth_config = await self.auth_service.find_auth_for_source(source_url)
            
            if source_type == 'rss':
                return await self._crawl_rss_feed(source_config, auth_config)
            elif source_type == 'html' or source_type == 'website':
                return await self._crawl_html_page(source_config, auth_config)
            elif source_type == 'api':
                return await self._crawl_api_endpoint(source_config, auth_config)
            elif source_type == 'json':
                return await self._crawl_json_feed(source_config, auth_config)
            else:
                raise CrawlingError(f"Unsupported source type: {source_type}")
                
        except Exception as e:
            logger.error(f"Failed to crawl source {source_config.get('url')}: {e}")
            return {
                "source_id": source_config.get('id', 'unknown'),
                "url": source_config.get('url', ''),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "content": []
            }
    
    async def crawl_multiple(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crawl multiple sources concurrently."""
        if not self.session:
            raise CrawlingError("Crawler not initialized. Use async context manager.")
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(getattr(self.config, 'concurrent_requests', 10))
        
        async def crawl_with_semaphore(source):
            async with semaphore:
                return await self.crawl_source(source)
        
        tasks = [crawl_with_semaphore(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "source_id": sources[i].get('id', 'unknown'),
                    "url": sources[i].get('url', ''),
                    "status": "failed",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat(),
                    "content": []
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def validate_source(self, source_config: Dict[str, Any]) -> bool:
        """Validate if a source is accessible."""
        try:
            if not self.session:
                raise CrawlingError("Crawler not initialized")
            
            url = source_config.get('url', '')
            if not url:
                return False
            
            async with self.session.head(url) as response:
                return response.status < 400
                
        except Exception as e:
            logger.error(f"Source validation failed for {source_config.get('url')}: {e}")
            return False
    
    async def _crawl_rss_feed(
        self,
        source_config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crawl RSS feed."""
        url = source_config['url']
        
        try:
            # Safe header conversion that handles ConfigSection objects
            headers = {}
            if hasattr(self.config, 'headers') and self.config.headers:
                if hasattr(self.config.headers, 'to_dict'):
                    try:
                        headers = self.config.headers.to_dict()
                    except Exception:
                        headers = {}
                elif hasattr(self.config.headers, '__dict__'):
                    # Handle ConfigSection objects that don't have to_dict
                    try:
                        headers = {k: v for k, v in self.config.headers.__dict__.items() 
                                 if not k.startswith('_') and isinstance(v, (str, int, float, bool))}
                    except Exception:
                        headers = {}
                else:
                    try:
                        headers = dict(self.config.headers)
                    except (TypeError, ValueError):
                        headers = {}
            
            # Set a default User-Agent if none exists
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)'
            if auth_config:
                headers.update(self._build_auth_headers(auth_config))
            
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo:
                logger.warning(f"RSS feed has parsing issues: {url}")
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 entries
                article = {
                    "id": entry.get('id', entry.get('link', '')),
                    "title": entry.get('title', ''),
                    "content": entry.get('summary', entry.get('description', '')),
                    "url": entry.get('link', ''),
                    "published": entry.get('published', ''),
                    "author": entry.get('author', ''),
                    "category": source_config.get('category', ''),
                    "source": source_config.get('name', url),
                    "source_id": source_config.get('id', ''),
                    "crawled_at": datetime.now().isoformat()
                }
                
                # Get full content if configured
                if source_config.get('extract_full_content', False):
                    article['content'] = await self._extract_full_content(article['url'])
                
                articles.append(article)
            
            return {
                "source_id": source_config.get('id', ''),
                "url": url,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "content": articles,
                "metadata": {
                    "feed_title": feed.feed.get('title', ''),
                    "feed_description": feed.feed.get('description', ''),
                    "total_entries": len(feed.entries),
                    "extracted_entries": len(articles)
                }
            }
            
        except Exception as e:
            raise CrawlingError(f"RSS crawling failed: {str(e)}")
    
    async def _crawl_html_page(
        self,
        source_config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crawl HTML page."""
        url = source_config['url']
        
        try:
            # Safe header conversion that handles ConfigSection objects
            headers = {}
            if hasattr(self.config, 'headers') and self.config.headers:
                if hasattr(self.config.headers, 'to_dict'):
                    try:
                        headers = self.config.headers.to_dict()
                    except Exception:
                        headers = {}
                elif hasattr(self.config.headers, '__dict__'):
                    # Handle ConfigSection objects that don't have to_dict
                    try:
                        headers = {k: v for k, v in self.config.headers.__dict__.items() 
                                 if not k.startswith('_') and isinstance(v, (str, int, float, bool))}
                    except Exception:
                        headers = {}
                else:
                    try:
                        headers = dict(self.config.headers)
                    except (TypeError, ValueError):
                        headers = {}
            
            # Set a default User-Agent if none exists
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)'
            if auth_config:
                headers.update(self._build_auth_headers(auth_config))
            
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract content based on selectors
            selectors = source_config.get('selectors', {})
            articles = []
            
            if selectors:
                # Use configured selectors
                article_elements = soup.select(selectors.get('article', 'article'))
                
                for element in article_elements[:10]:  # Limit to 10 articles
                    title_elem = element.select_one(selectors.get('title', 'h1, h2, h3'))
                    content_elem = element.select_one(selectors.get('content', 'p, .content'))
                    link_elem = element.select_one(selectors.get('link', 'a'))
                    
                    article = {
                        "id": link_elem.get('href', '') if link_elem else '',
                        "title": title_elem.get_text(strip=True) if title_elem else '',
                        "content": content_elem.get_text(strip=True) if content_elem else '',
                        "url": urljoin(url, link_elem.get('href', '')) if link_elem else url,
                        "source": source_config.get('name', url),
                        "source_id": source_config.get('id', ''),
                        "category": source_config.get('category', ''),
                        "crawled_at": datetime.now().isoformat()
                    }
                    articles.append(article)
            else:
                # Default extraction
                title = soup.find('title')
                content_elem = soup.find('main') or soup.find('article') or soup.find('body')
                
                article = {
                    "id": url,
                    "title": title.get_text(strip=True) if title else '',
                    "content": content_elem.get_text(strip=True) if content_elem else '',
                    "url": url,
                    "source": source_config.get('name', url),
                    "source_id": source_config.get('id', ''),
                    "category": source_config.get('category', ''),
                    "crawled_at": datetime.now().isoformat()
                }
                articles.append(article)
            
            return {
                "source_id": source_config.get('id', ''),
                "url": url,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "content": articles,
                "metadata": {
                    "page_title": soup.find('title').get_text(strip=True) if soup.find('title') else '',
                    "extracted_articles": len(articles)
                }
            }
            
        except Exception as e:
            raise CrawlingError(f"HTML crawling failed: {str(e)}")
    
    async def _crawl_api_endpoint(
        self,
        source_config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crawl API endpoint."""
        url = source_config['url']
        
        try:
            # Safe header conversion that handles ConfigSection objects
            headers = {}
            if hasattr(self.config, 'headers') and self.config.headers:
                if hasattr(self.config.headers, 'to_dict'):
                    try:
                        headers = self.config.headers.to_dict()
                    except Exception:
                        headers = {}
                elif hasattr(self.config.headers, '__dict__'):
                    # Handle ConfigSection objects that don't have to_dict
                    try:
                        headers = {k: v for k, v in self.config.headers.__dict__.items() 
                                 if not k.startswith('_') and isinstance(v, (str, int, float, bool))}
                    except Exception:
                        headers = {}
                else:
                    try:
                        headers = dict(self.config.headers)
                    except (TypeError, ValueError):
                        headers = {}
            
            # Set a default User-Agent if none exists
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)'
            if auth_config:
                headers.update(self._build_auth_headers(auth_config))
            
            # Add API-specific headers
            headers['Accept'] = 'application/json'
            
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process API response based on configuration
            articles = []
            data_path = source_config.get('data_path', [])
            
            # Navigate to data using path
            current_data = data
            for path_segment in data_path:
                if isinstance(current_data, dict):
                    current_data = current_data.get(path_segment, [])
                else:
                    break
            
            if isinstance(current_data, list):
                for item in current_data[:20]:  # Limit to 20 items
                    if isinstance(item, dict):
                        article = {
                            "id": item.get('id', item.get('url', '')),
                            "title": item.get('title', item.get('name', '')),
                            "content": item.get('content', item.get('description', item.get('summary', ''))),
                            "url": item.get('url', item.get('link', '')),
                            "published": item.get('published_at', item.get('created_at', '')),
                            "author": item.get('author', item.get('user', '')),
                            "source": source_config.get('name', url),
                            "source_id": source_config.get('id', ''),
                            "category": source_config.get('category', ''),
                            "crawled_at": datetime.now().isoformat()
                        }
                        articles.append(article)
            
            return {
                "source_id": source_config.get('id', ''),
                "url": url,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "content": articles,
                "metadata": {
                    "api_response_type": type(data).__name__,
                    "extracted_articles": len(articles)
                }
            }
            
        except Exception as e:
            raise CrawlingError(f"API crawling failed: {str(e)}")
    
    async def _crawl_json_feed(
        self,
        source_config: Dict[str, Any],
        auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crawl JSON feed."""
        return await self._crawl_api_endpoint(source_config, auth_config)
    
    async def _extract_full_content(self, url: str) -> str:
        """Extract full content from article URL."""
        try:
            if not self.session:
                return ""
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ""
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Try to find main content
                content_elem = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find(class_=lambda x: x and 'content' in x.lower()) or
                    soup.find('body')
                )
                
                if content_elem:
                    return content_elem.get_text(strip=True)
                
                return ""
                
        except Exception as e:
            logger.error(f"Failed to extract full content from {url}: {e}")
            return ""
    
    def _build_auth_headers(self, auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Build authentication headers."""
        headers = {}
        
        auth_type = auth_config.get('type', '')
        
        if auth_type == 'bearer_token':
            token = auth_config.get('token', '')
            headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'api_key':
            key = auth_config.get('key', '')
            header_name = auth_config.get('header', 'X-API-Key')
            headers[header_name] = key
        elif auth_type == 'basic':
            import base64
            username = auth_config.get('username', '')
            password = auth_config.get('password', '')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        return headers