"""
Fixed crawler agent that resolves ConfigSection serialization issues
and uses premium AI sources for reliable content crawling.
"""

import asyncio
import aiohttp
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import feedparser
import yaml
from pathlib import Path
from langchain_core.messages import HumanMessage
from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage
from utils.config_fix import safe_dict_convert, safe_headers_extract
from services.enhanced_crawler_service import EnhancedCrawlerService
from config import get_settings


class FixedCrawlerAgent(BaseAgent):
    """Fixed crawler agent with reliable sources and proper error handling"""
    
    def __init__(self):
        super().__init__("FixedCrawlerAgent")
        self.file_storage = FileStorage()
        self.settings = get_settings()
        
        # Load premium sources
        self.premium_sources = self._load_premium_sources()
        
    def _load_premium_sources(self) -> Dict[str, Any]:
        """Load premium AI sources from configuration file"""
        sources_file = Path(__file__).parent.parent / "sources_premium.yml"
        
        if sources_file.exists():
            with open(sources_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # Fallback to hardcoded premium sources
            return {
                "sources": {
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
                            "name": "VentureBeat AI",
                            "url": "https://venturebeat.com/ai/feed/",
                            "category": "news",
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
                        }
                    ]
                }
            }
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute crawling with enhanced error handling and premium sources"""
        try:
            state.current_step = "premium_crawling"
            
            # Get premium sources
            rss_sources = self.premium_sources.get("sources", {}).get("rss_feeds", [])
            web_sources = self.premium_sources.get("sources", {}).get("websites", [])
            
            # Initialize progress tracking
            total_sources = len(rss_sources) + len(web_sources)
            state.progress = {
                "current_step": "premium_crawling",
                "total_sources": total_sources,
                "completed_sources": 0,
                "current_source": "",
                "status": "starting",
                "sources_detail": [],
                "rss_articles": 0,
                "web_pages": 0,
                "total_items": 0,
                "failed_sources": 0
            }
            
            print(f"🎯 开始使用优质AI信源抓取...")
            print(f"📊 优质RSS源: {len(rss_sources)} 个")
            print(f"🌐 优质网站: {len(web_sources)} 个")
            print(f"📈 总计信源: {total_sources} 个")
            print("=" * 60)
            
            all_content = {
                "rss_content": [],
                "web_content": []
            }
            
            # Use enhanced crawler service
            async with EnhancedCrawlerService(self.settings, None) as crawler:
                # Process RSS feeds
                for i, source in enumerate(rss_sources, 1):
                    try:
                        state.progress["current_source"] = source["url"]
                        state.progress["completed_sources"] = i - 1
                        
                        print(f"  [{i}/{total_sources}] RSS: {source['name']}")
                        print(f"    URL: {source['url']}")
                        
                        articles = await self._crawl_rss_safe(crawler, source)
                        
                        if articles:
                            all_content["rss_content"].extend(articles)
                            state.progress["rss_articles"] += len(articles)
                            state.progress["total_items"] = len(all_content["rss_content"]) + len(all_content["web_content"])
                            
                            print(f"    ✅ 成功获取 {len(articles)} 篇文章")
                            
                            state.progress["sources_detail"].append({
                                "name": source["name"],
                                "url": source["url"],
                                "type": "rss",
                                "status": "success",
                                "articles_count": len(articles),
                                "category": source.get("category", "unknown")
                            })
                        else:
                            print(f"    ⚠️ 未获取到内容")
                            state.progress["failed_sources"] += 1
                            state.progress["sources_detail"].append({
                                "name": source["name"],
                                "url": source["url"],
                                "type": "rss",
                                "status": "no_content",
                                "category": source.get("category", "unknown")
                            })
                        
                        # Rate limiting
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        print(f"    ❌ 抓取失败: {e}")
                        state.progress["failed_sources"] += 1
                        state.progress["sources_detail"].append({
                            "name": source["name"],
                            "url": source["url"],
                            "type": "rss",
                            "status": "error",
                            "error": str(e),
                            "category": source.get("category", "unknown")
                        })
                        continue
                
                # Process websites
                start_index = len(rss_sources) + 1
                for i, source in enumerate(web_sources, start_index):
                    try:
                        state.progress["current_source"] = source["url"]
                        state.progress["completed_sources"] = i - 1
                        
                        print(f"  [{i}/{total_sources}] 网站: {source['name']}")
                        print(f"    URL: {source['url']}")
                        
                        pages = await self._crawl_website_safe(crawler, source)
                        
                        if pages:
                            all_content["web_content"].extend(pages)
                            state.progress["web_pages"] += len(pages)
                            state.progress["total_items"] = len(all_content["rss_content"]) + len(all_content["web_content"])
                            
                            print(f"    ✅ 成功获取 {len(pages)} 个页面")
                            
                            state.progress["sources_detail"].append({
                                "name": source["name"],
                                "url": source["url"],
                                "type": "website",
                                "status": "success",
                                "pages_count": len(pages),
                                "category": source.get("category", "unknown")
                            })
                        else:
                            print(f"    ⚠️ 未获取到内容")
                            state.progress["failed_sources"] += 1
                            state.progress["sources_detail"].append({
                                "name": source["name"],
                                "url": source["url"],
                                "type": "website",
                                "status": "no_content",
                                "category": source.get("category", "unknown")
                            })
                        
                        # Rate limiting
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        print(f"    ❌ 抓取失败: {e}")
                        state.progress["failed_sources"] += 1
                        state.progress["sources_detail"].append({
                            "name": source["name"],
                            "url": source["url"],
                            "type": "website",
                            "status": "error",
                            "error": str(e),
                            "category": source.get("category", "unknown")
                        })
                        continue
            
            # Final statistics
            state.progress["completed_sources"] = total_sources
            state.progress["status"] = "completed"
            
            total_items = len(all_content["rss_content"]) + len(all_content["web_content"])
            successful_sources = total_sources - state.progress["failed_sources"]
            
            print("=" * 60)
            print(f"✅ 优质信源抓取完成!")
            print(f"📊 成功信源: {successful_sources}/{total_sources}")
            print(f"📡 RSS文章: {len(all_content['rss_content'])} 篇")
            print(f"🌐 网页内容: {len(all_content['web_content'])} 个")
            print(f"📈 总计: {total_items} 项内容")
            print("=" * 60)
            
            # Prepare final content structure
            crawled_content = {
                "rss_content": all_content["rss_content"],
                "web_content": all_content["web_content"],
                "crawl_timestamp": asyncio.get_event_loop().time(),
                "progress": state.progress,
                "stats": {
                    "total_expected": total_sources,
                    "total_actual": total_items,
                    "successful_sources": successful_sources,
                    "failed_sources": state.progress["failed_sources"],
                    "rss_articles_count": len(all_content["rss_content"]),
                    "web_pages_count": len(all_content["web_content"])
                },
                "source_quality": "premium",
                "crawler_version": "fixed_v1.0"
            }
            
            state.data["crawled_content"] = crawled_content
            
            # Save crawled content to local file
            workflow_id = state.data.get("workflow_id", "default")
            saved_path = self.file_storage.save_crawled_content(crawled_content, workflow_id)
            state.data["crawled_content_file"] = saved_path
            
            state.messages.append(
                HumanMessage(content=f"Premium crawling completed: {total_items} items from {successful_sources}/{total_sources} sources")
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Fixed crawler error: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _crawl_rss_safe(self, crawler: EnhancedCrawlerService, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safely crawl RSS source with proper error handling"""
        try:
            url = source["url"]
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml'
            }
            
            async with crawler.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_rss_content(content, source)
                else:
                    print(f"      HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"      RSS抓取错误: {e}")
            return []
    
    async def _crawl_website_safe(self, crawler: EnhancedCrawlerService, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safely crawl website source with proper error handling"""
        try:
            url = source["url"]
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            async with crawler.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_website_content(content, source)
                else:
                    print(f"      HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"      网站抓取错误: {e}")
            return []
    
    def _parse_rss_content(self, content: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse RSS content with enhanced error handling"""
        try:
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                print(f"      RSS解析警告: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                try:
                    # Extract content with fallbacks
                    content_text = ""
                    if hasattr(entry, 'content') and entry.content:
                        content_text = entry.content[0].value if entry.content else ""
                    elif hasattr(entry, 'summary'):
                        content_text = entry.summary
                    elif hasattr(entry, 'description'):
                        content_text = entry.description
                    
                    # Clean HTML tags
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
                        "category": source.get('category', 'unknown'),
                        "type": "rss"
                    }
                    
                    # Only include articles with title and some content
                    if article["title"] and (article["content"] or article["summary"]):
                        articles.append(article)
                        
                except Exception as e:
                    print(f"        文章解析错误: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            print(f"      RSS内容解析错误: {e}")
            return []
    
    def _parse_website_content(self, content: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse website content with basic extraction"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            # Extract basic page info
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ''
            
            # Try to find main content
            main_elem = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_elem:
                main_content = main_elem.get_text().strip()
            else:
                # Fallback to body
                body_elem = soup.find('body')
                main_content = body_elem.get_text().strip() if body_elem else ''
            
            # Limit content length
            if len(main_content) > 2000:
                main_content = main_content[:2000] + "..."
            
            if title or main_content:
                return [{
                    "title": title,
                    "url": source["url"],
                    "content": main_content,
                    "summary": main_content[:300] + "..." if len(main_content) > 300 else main_content,
                    "source": source['name'],
                    "source_url": source['url'],
                    "category": source.get('category', 'unknown'),
                    "type": "webpage"
                }]
            else:
                return []
                
        except Exception as e:
            print(f"      网站内容解析错误: {e}")
            return []