import asyncio
import aiohttp
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import feedparser
from langchain_core.messages import HumanMessage
from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage

class CrawlerAgent(BaseAgent):
    """Agent responsible for crawling AI-related content from various sources"""
    
    def __init__(self):
        super().__init__("CrawlerAgent")
        self.file_storage = FileStorage()
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
            
            # Calculate total expected items
            total_rss_feeds = len(self.sources["rss_feeds"])
            total_websites = len(self.sources["websites"])
            expected_articles_per_feed = 5  # We limit to 5 articles per feed
            total_expected = (total_rss_feeds * expected_articles_per_feed) + total_websites
            
            # Initialize progress tracking
            state.progress = {
                "current_step": "crawling_content",
                "total_expected": total_expected,
                "total_rss_feeds": total_rss_feeds,
                "total_websites": total_websites,
                "expected_articles_per_feed": expected_articles_per_feed,
                "rss_feeds_completed": 0,
                "websites_completed": 0,
                "articles_found": 0,
                "current_source": "",
                "status": "starting",
                "sources_detail": []
            }
            
            print(f"🎯 开始抓取内容...")
            print(f"📊 预计抓取: RSS源 {total_rss_feeds} 个 (每个最多 {expected_articles_per_feed} 篇) + 网站 {total_websites} 个")
            print(f"📈 总预计项目数: {total_expected}")
            print("=" * 60)
            
            # Crawl RSS feeds with progress tracking
            rss_content = await self._crawl_rss_feeds_with_progress(state)
            
            # Crawl websites with progress tracking
            web_content = await self._crawl_websites_with_progress(state)
            
            # Final summary
            actual_total = len(rss_content) + len(web_content)
            state.progress["status"] = "completed"
            state.progress["total_actual"] = actual_total
            state.progress["rss_articles_count"] = len(rss_content)
            state.progress["web_pages_count"] = len(web_content)
            
            print("=" * 60)
            print(f"✅ 抓取完成!")
            print(f"📊 实际抓取: RSS文章 {len(rss_content)} 篇 + 网页 {len(web_content)} 个")
            print(f"📈 总计: {actual_total} 项 (预计 {total_expected} 项)")
            print("=" * 60)
            
            # Combine all content
            all_content = {
                "rss_content": rss_content,
                "web_content": web_content,
                "crawl_timestamp": asyncio.get_event_loop().time(),
                "progress": state.progress,
                "stats": {
                    "total_expected": total_expected,
                    "total_actual": actual_total,
                    "rss_feeds_count": total_rss_feeds,
                    "rss_articles_count": len(rss_content),
                    "websites_count": total_websites,
                    "web_pages_count": len(web_content)
                }
            }
            
            state.data["crawled_content"] = all_content
            
            # Save crawled content to local file
            workflow_id = state.data.get("workflow_id", "default")
            saved_path = self.file_storage.save_crawled_content(all_content, workflow_id)
            state.data["crawled_content_file"] = saved_path
            
            state.messages.append(
                HumanMessage(content=f"Crawled {len(rss_content)} RSS articles and {len(web_content)} web pages")
            )
            
            return state
            
        except Exception as e:
            state.error = f"Crawler error: {str(e)}"
            return state
    
    async def _crawl_rss_feeds_with_progress(self, state: AgentState) -> List[Dict[str, Any]]:
        """Crawl RSS feeds for AI content with progress tracking"""
        articles = []
        
        state.progress["status"] = "crawling_rss"
        print("📡 开始抓取RSS源...")
        
        for i, feed_url in enumerate(self.sources["rss_feeds"], 1):
            try:
                state.progress["current_source"] = feed_url
                state.progress["rss_feeds_completed"] = i - 1
                print(f"  [{i}/{len(self.sources['rss_feeds'])}] 抓取: {feed_url}")
                
                # Use feedparser to parse RSS feeds
                feed = feedparser.parse(feed_url)
                feed_title = feed.feed.get('title', '未知RSS源') if hasattr(feed, 'feed') else '未知RSS源'
                print(f"    📰 RSS源标题: {feed_title}")
                
                feed_articles = []
                source_detail = {
                    "url": feed_url,
                    "title": feed_title,
                    "type": "rss",
                    "status": "processing",
                    "articles": []
                }
                
                for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                    article = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", ""),
                        "source": feed_url,
                        "type": "rss"
                    }
                    feed_articles.append(article)
                    source_detail["articles"].append({
                        "title": article["title"],
                        "url": article["url"]
                    })
                    # Show article being crawled
                    print(f"      📄 {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}")
                
                articles.extend(feed_articles)
                source_detail["status"] = "completed"
                source_detail["articles_count"] = len(feed_articles)
                state.progress["sources_detail"].append(source_detail)
                state.progress["articles_found"] = len(articles)
                
                print(f"    ✅ 完成，获取 {len(feed_articles)} 篇文章")
                    
            except Exception as e:
                print(f"    ❌ 错误: {e}")
                source_detail = {
                    "url": feed_url,
                    "title": "抓取失败",
                    "type": "rss",
                    "status": "error",
                    "error": str(e),
                    "articles_count": 0
                }
                state.progress["sources_detail"].append(source_detail)
                continue
        
        state.progress["rss_feeds_completed"] = len(self.sources["rss_feeds"])
        print(f"📡 RSS抓取完成，总计获取 {len(articles)} 篇文章")
        return articles
    
    async def _crawl_rss_feeds(self) -> List[Dict[str, Any]]:
        """Crawl RSS feeds for AI content (legacy method for compatibility)"""
        # Create a temporary state for legacy calls
        temp_state = AgentState()
        temp_state.progress = {"sources_detail": []}
        return await self._crawl_rss_feeds_with_progress(temp_state)
    
    async def _crawl_websites_with_progress(self, state: AgentState) -> List[Dict[str, Any]]:
        """Crawl websites for AI content with progress tracking"""
        pages = []
        
        state.progress["status"] = "crawling_websites"
        print("🌐 开始抓取网站...")
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(self.sources["websites"], 1):
                try:
                    state.progress["current_source"] = url
                    state.progress["websites_completed"] = i - 1
                    print(f"  [{i}/{len(self.sources['websites'])}] 抓取: {url}")
                    
                    source_detail = {
                        "url": url,
                        "title": "",
                        "type": "website",
                        "status": "processing",
                        "description": ""
                    }
                    
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract basic content
                            title = soup.find('title')
                            title_text = title.get_text().strip() if title else ""
                            
                            # Extract meta description
                            meta_desc = soup.find('meta', attrs={'name': 'description'})
                            description = meta_desc.get('content', '') if meta_desc else ''
                            
                            source_detail["title"] = title_text
                            source_detail["description"] = description
                            
                            print(f"    🏷️  网站标题: {title_text[:80]}{'...' if len(title_text) > 80 else ''}")
                            if description:
                                print(f"    📝 网站描述: {description[:100]}{'...' if len(description) > 100 else ''}")
                            
                            # Extract main content (customize based on site structure)
                            content = self._extract_main_content(soup)
                            
                            page = {
                                "title": title_text,
                                "url": url,
                                "content": content,
                                "description": description,
                                "source": url,
                                "type": "webpage"
                            }
                            pages.append(page)
                            
                            source_detail["status"] = "completed"
                            source_detail["content_length"] = len(content)
                            print(f"    ✅ 完成，内容长度: {len(content)} 字符")
                        else:
                            source_detail["status"] = "error"
                            source_detail["error"] = f"HTTP {response.status}"
                            print(f"    ❌ HTTP错误: {response.status}")
                    
                    state.progress["sources_detail"].append(source_detail)
                            
                except Exception as e:
                    print(f"    ❌ 抓取错误: {e}")
                    source_detail = {
                        "url": url,
                        "title": "抓取失败",
                        "type": "website",
                        "status": "error",
                        "error": str(e)
                    }
                    state.progress["sources_detail"].append(source_detail)
                    continue
        
        state.progress["websites_completed"] = len(self.sources["websites"])
        state.progress["status"] = "completed"
        print(f"🌐 网站抓取完成，总计获取 {len(pages)} 个网页")
        return pages
    
    async def _crawl_websites(self) -> List[Dict[str, Any]]:
        """Crawl websites for AI content (legacy method for compatibility)"""
        # Create a temporary state for legacy calls
        temp_state = AgentState()
        temp_state.progress = {"sources_detail": []}
        return await self._crawl_websites_with_progress(temp_state)
    
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