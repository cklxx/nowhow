import asyncio
import aiohttp
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import feedparser
from langchain_core.messages import HumanMessage
from .base_agent import BaseAgent, AgentState

class CrawlerAgent(BaseAgent):
    """Agent responsible for crawling AI-related content from various sources"""
    
    def __init__(self):
        super().__init__("CrawlerAgent")
        self.sources = {
            "rss_feeds": [
                "https://feeds.feedburner.com/oreilly/radar",
                "https://distill.pub/rss.xml",
                "https://blog.openai.com/rss/",
                "https://ai.googleblog.com/feeds/posts/default",
                "https://blog.deepmind.com/rss.xml"
            ],
            "websites": [
                "https://arxiv.org/list/cs.AI/recent",
                "https://paperswithcode.com/latest",
                "https://huggingface.co/papers",
                "https://towards-ai.net/",
                "https://machinelearningmastery.com/"
            ]
        }
    
    async def execute(self, state: AgentState) -> AgentState:
        """Crawl content from configured sources"""
        try:
            state.current_step = "crawling_content"
            
            # Crawl RSS feeds
            rss_content = await self._crawl_rss_feeds()
            
            # Crawl websites
            web_content = await self._crawl_websites()
            
            # Combine all content
            all_content = {
                "rss_content": rss_content,
                "web_content": web_content,
                "crawl_timestamp": asyncio.get_event_loop().time()
            }
            
            state.data["crawled_content"] = all_content
            state.messages.append(
                HumanMessage(content=f"Crawled {len(rss_content)} RSS articles and {len(web_content)} web pages")
            )
            
            return state
            
        except Exception as e:
            state.error = f"Crawler error: {str(e)}"
            return state
    
    async def _crawl_rss_feeds(self) -> List[Dict[str, Any]]:
        """Crawl RSS feeds for AI content"""
        articles = []
        
        for feed_url in self.sources["rss_feeds"]:
            try:
                # Use feedparser to parse RSS feeds
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                    article = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", ""),
                        "source": feed_url,
                        "type": "rss"
                    }
                    articles.append(article)
                    
            except Exception as e:
                print(f"Error crawling RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    async def _crawl_websites(self) -> List[Dict[str, Any]]:
        """Crawl websites for AI content"""
        pages = []
        
        async with aiohttp.ClientSession() as session:
            for url in self.sources["websites"]:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract basic content
                            title = soup.find('title')
                            title_text = title.get_text() if title else ""
                            
                            # Extract main content (customize based on site structure)
                            content = self._extract_main_content(soup)
                            
                            page = {
                                "title": title_text,
                                "url": url,
                                "content": content,
                                "source": url,
                                "type": "webpage"
                            }
                            pages.append(page)
                            
                except Exception as e:
                    print(f"Error crawling website {url}: {e}")
                    continue
        
        return pages
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = ""
        
        # Common content selectors
        content_selectors = [
            'main', 'article', '.content', '#content', 
            '.post', '.entry', '.article-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem.get_text(strip=True)
                break
        
        # Fallback to body if no main content found
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(strip=True)
        
        # Limit content length
        return main_content[:2000] if main_content else ""