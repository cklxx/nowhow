import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Comment
import feedparser
from langchain_core.messages import HumanMessage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from urllib.parse import urljoin, urlparse
from datetime import datetime

from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage
from utils.source_manager import SourceManager
from services.ai_analyzer import AIWebAnalyzer
from services.mock_auth_finder import MockAuthFinder
from models.source_config import (
    SourceConfig, SourceType, ContentType, CrawlResult, 
    AIAnalysisRequest, MockAuthRequest, AuthType
)

class EnhancedCrawlerAgent(BaseAgent):
    """增强版爬虫代理，支持用户自定义信源和AI智能配置"""
    
    def __init__(self, api_key: str = None):
        super().__init__("EnhancedCrawlerAgent")
        self.file_storage = FileStorage()
        self.source_manager = SourceManager()
        self.ai_analyzer = AIWebAnalyzer(api_key)
        self.mock_auth_finder = MockAuthFinder()
        
        # 用户代理池
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行增强版爬虫任务"""
        try:
            state.current_step = "enhanced_crawling"
            
            # 获取所有激活的信源
            sources = self.source_manager.get_active_sources()
            
            # 初始化进度跟踪
            state.progress = {
                "current_step": "enhanced_crawling",
                "total_sources": len(sources),
                "completed_sources": 0,
                "current_source": "",
                "status": "starting",
                "sources_detail": [],
                "rss_articles": 0,
                "web_pages": 0,
                "total_items": 0
            }
            
            print(f"🎯 开始增强版内容抓取...")
            print(f"📊 发现 {len(sources)} 个配置的信源")
            print("=" * 60)
            
            all_content = []
            
            for i, source in enumerate(sources, 1):
                try:
                    state.progress["current_source"] = str(source.url)
                    state.progress["completed_sources"] = i - 1
                    
                    print(f"  [{i}/{len(sources)}] 处理信源: {source.name}")
                    print(f"    URL: {source.url}")
                    print(f"    类型: {source.type.value} | 内容类型: {source.content_type.value}")
                    
                    # 记录开始时间
                    start_time = time.time()
                    
                    # 根据信源类型进行抓取
                    if source.type == SourceType.RSS:
                        content = await self._crawl_rss_source(source, state)
                    else:
                        content = await self._crawl_web_source(source, state)
                    
                    # 计算响应时间
                    response_time = time.time() - start_time
                    
                    if content:
                        all_content.extend(content)
                        
                        # 保存抓取结果
                        for item in content:
                            result = CrawlResult(
                                source_id=source.id,
                                url=item.get("url", str(source.url)),
                                success=True,
                                title=item.get("title"),
                                content=item.get("content"),
                                summary=item.get("summary"),
                                author=item.get("author"),
                                publish_date=item.get("published"),
                                tags=item.get("tags", []),
                                response_time=response_time,
                                content_length=len(item.get("content", "")),
                                content_quality=item.get("quality_score", 0.8)
                            )
                            self.source_manager.save_crawl_result(result)
                        
                        print(f"    ✅ 成功获取 {len(content)} 项内容")
                        
                        # 更新进度
                        if source.type == SourceType.RSS:
                            state.progress["rss_articles"] += len(content)
                        else:
                            state.progress["web_pages"] += len(content)
                        
                        state.progress["total_items"] = len(all_content)
                    
                    else:
                        print(f"    ⚠️ 未获取到内容")
                        
                        # 记录失败结果
                        result = CrawlResult(
                            source_id=source.id,
                            url=str(source.url),
                            success=False,
                            error_type="no_content",
                            error_message="未能提取到有效内容",
                            response_time=response_time
                        )
                        self.source_manager.save_crawl_result(result)
                    
                    # 更新源详情
                    source_detail = {
                        "id": source.id,
                        "name": source.name,
                        "url": str(source.url),
                        "type": source.type.value,
                        "content_type": source.content_type.value,
                        "status": "completed" if content else "no_content",
                        "items_count": len(content) if content else 0,
                        "response_time": response_time,
                        "ai_analyzed": source.ai_analyzed
                    }
                    
                    if content:
                        source_detail["sample_titles"] = [
                            item.get("title", "无标题")[:60] + ("..." if len(item.get("title", "")) > 60 else "")
                            for item in content[:3]
                        ]
                    
                    state.progress["sources_detail"].append(source_detail)
                    
                    # 添加请求间隔
                    if i < len(sources):
                        delay = source.crawl_config.delay
                        if delay > 0:
                            await asyncio.sleep(delay)
                
                except Exception as e:
                    print(f"    ❌ 处理信源失败: {e}")
                    
                    # 记录错误结果
                    result = CrawlResult(
                        source_id=source.id,
                        url=str(source.url),
                        success=False,
                        error_type="crawl_error",
                        error_message=str(e)
                    )
                    self.source_manager.save_crawl_result(result)
                    
                    # 添加错误详情到进度
                    state.progress["sources_detail"].append({
                        "id": source.id,
                        "name": source.name,
                        "url": str(source.url),
                        "type": source.type.value,
                        "status": "error",
                        "error": str(e)
                    })
                    continue
            
            # 完成抓取
            state.progress["completed_sources"] = len(sources)
            state.progress["status"] = "completed"
            
            print("=" * 60)
            print(f"✅ 增强版抓取完成!")
            print(f"📊 总计获取: {len(all_content)} 项内容")
            print(f"📡 RSS文章: {state.progress['rss_articles']} 篇")
            print(f"🌐 网页内容: {state.progress['web_pages']} 个")
            print("=" * 60)
            
            # 组合所有内容
            enhanced_content = {
                "enhanced_content": all_content,
                "crawl_timestamp": datetime.now().timestamp(),
                "progress": state.progress,
                "sources_used": len(sources),
                "total_items": len(all_content),
                "stats": {
                    "rss_articles": state.progress["rss_articles"],
                    "web_pages": state.progress["web_pages"],
                    "total_sources": len(sources),
                    "successful_sources": len([s for s in state.progress["sources_detail"] if s.get("status") == "completed"])
                }
            }
            
            state.data["crawled_content"] = enhanced_content
            
            # 保存爬取内容到文件
            workflow_id = state.data.get("workflow_id", "default")
            saved_path = self.file_storage.save_crawled_content(enhanced_content, workflow_id)
            state.data["crawled_content_file"] = saved_path
            
            state.messages.append(
                HumanMessage(content=f"Enhanced crawling completed: {len(all_content)} items from {len(sources)} sources")
            )
            
            return state
            
        except Exception as e:
            state.error = f"Enhanced crawler error: {str(e)}"
            print(f"❌ 增强版爬虫错误: {e}")
            return state
    
    async def _crawl_rss_source(self, source: SourceConfig, state: AgentState) -> List[Dict[str, Any]]:
        """抓取RSS信源"""
        try:
            # 设置请求头
            headers = dict(source.auth_config.headers) if source.auth_config.headers else {}
            if not headers.get("User-Agent"):
                headers["User-Agent"] = random.choice(self.user_agents)
            
            # 解析RSS
            feed = feedparser.parse(str(source.url))
            
            articles = []
            max_items = min(10, len(feed.entries))  # 最多取10篇文章
            
            for entry in feed.entries[:max_items]:
                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "content": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
                    "author": entry.get("author", ""),
                    "published": entry.get("published", ""),
                    "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
                    "source": str(source.url),
                    "source_name": source.name,
                    "type": "rss",
                    "content_type": source.content_type.value
                }
                
                # 如果没有内容，尝试获取全文
                if not article["content"] and article["url"]:
                    try:
                        full_content = await self._fetch_full_article(article["url"], source)
                        if full_content:
                            article["content"] = full_content
                    except Exception as e:
                        print(f"      获取全文失败: {e}")
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"    RSS抓取错误: {e}")
            return []
    
    async def _crawl_web_source(self, source: SourceConfig, state: AgentState) -> List[Dict[str, Any]]:
        """抓取网页信源"""
        try:
            # 检查是否需要AI分析
            if not source.ai_analyzed:
                print(f"    🔍 执行AI结构分析...")
                await self._analyze_with_ai(source)
            
            # 获取网页内容
            if source.crawl_config.render_js:
                content = await self._fetch_with_selenium(source)
            else:
                content = await self._fetch_with_aiohttp(source)
            
            if not content:
                return []
            
            # 解析内容
            soup = BeautifulSoup(content, 'html.parser')
            
            # 使用配置的选择器提取内容
            extracted_items = self._extract_content_with_selectors(soup, source)
            
            return extracted_items
            
        except Exception as e:
            print(f"    网页抓取错误: {e}")
            return []
    
    async def _analyze_with_ai(self, source: SourceConfig):
        """使用AI分析网页结构"""
        try:
            request = AIAnalysisRequest(
                url=source.url,
                content_type=source.content_type
            )
            
            analysis_result = await self.ai_analyzer.analyze_webpage(request)
            
            # 更新源配置
            source.content_selectors = analysis_result.suggested_selectors
            source.ai_analyzed = True
            source.ai_analysis_time = datetime.now()
            source.ai_confidence = analysis_result.confidence
            source.ai_suggestions = analysis_result.recommendations
            
            # 更新JS渲染需求
            if analysis_result.requires_js:
                source.crawl_config.render_js = True
            
            # 如果需要认证，尝试查找mock配置
            if analysis_result.requires_auth:
                print(f"      🔐 检测到需要认证，查找mock配置...")
                await self._find_mock_auth(source)
            
            # 保存更新的配置
            self.source_manager.save_source(source)
            
            print(f"      ✅ AI分析完成，置信度: {analysis_result.confidence:.2f}")
            
        except Exception as e:
            print(f"      ⚠️ AI分析失败: {e}")
    
    async def _find_mock_auth(self, source: SourceConfig):
        """查找mock认证配置"""
        try:
            domain = urlparse(str(source.url)).netloc
            
            request = MockAuthRequest(
                url=source.url,
                site_domain=domain,
                auth_type=AuthType.COOKIE
            )
            
            mock_result = await self.mock_auth_finder.find_mock_auth(request)
            
            if mock_result.found and mock_result.auth_config:
                # 更新认证配置
                source.auth_config = mock_result.auth_config
                print(f"      🔑 找到认证配置: {', '.join(mock_result.sources)}")
                
                # 如果包含placeholder，给出提示
                if any("placeholder" in str(v) for v in source.auth_config.headers.values()) or \
                   any("placeholder" in str(v) for v in source.auth_config.cookies.values()):
                    print(f"      ⚠️ 认证配置包含placeholder，需要手动替换真实值")
            
        except Exception as e:
            print(f"      ⚠️ 查找认证配置失败: {e}")
    
    async def _fetch_with_aiohttp(self, source: SourceConfig) -> Optional[str]:
        """使用aiohttp获取网页内容"""
        headers = dict(source.auth_config.headers) if source.auth_config.headers else {}
        cookies = dict(source.auth_config.cookies) if source.auth_config.cookies else {}
        
        if not headers.get("User-Agent"):
            if source.crawl_config.random_user_agent:
                headers["User-Agent"] = random.choice(self.user_agents)
            else:
                headers["User-Agent"] = source.crawl_config.user_agent or self.user_agents[0]
        
        timeout = aiohttp.ClientTimeout(total=source.crawl_config.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for attempt in range(source.crawl_config.retry_count):
                try:
                    async with session.get(
                        str(source.url),
                        headers=headers,
                        cookies=cookies,
                        proxy=source.crawl_config.proxy
                    ) as response:
                        if response.status == 200:
                            content = await response.text(encoding=source.crawl_config.encoding)
                            return content
                        else:
                            print(f"      HTTP {response.status} (尝试 {attempt + 1}/{source.crawl_config.retry_count})")
                
                except Exception as e:
                    print(f"      请求失败 (尝试 {attempt + 1}/{source.crawl_config.retry_count}): {e}")
                    if attempt < source.crawl_config.retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    async def _fetch_with_selenium(self, source: SourceConfig) -> Optional[str]:
        """使用Selenium获取需要JS渲染的网页内容"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # 设置User-Agent
        user_agent = source.auth_config.headers.get("User-Agent")
        if not user_agent:
            user_agent = random.choice(self.user_agents) if source.crawl_config.random_user_agent else self.user_agents[0]
        options.add_argument(f'--user-agent={user_agent}')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(source.crawl_config.timeout)
            
            # 设置cookies
            if source.auth_config.cookies:
                driver.get(str(source.url))
                for name, value in source.auth_config.cookies.items():
                    if "placeholder" not in value:
                        driver.add_cookie({"name": name, "value": value})
            
            # 加载页面
            driver.get(str(source.url))
            
            # 等待特定元素加载
            if source.crawl_config.wait_for_selector:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, source.crawl_config.wait_for_selector))
                    )
                except Exception:
                    print(f"      等待元素超时: {source.crawl_config.wait_for_selector}")
            else:
                # 默认等待页面加载
                time.sleep(3)
            
            return driver.page_source
            
        except Exception as e:
            print(f"      Selenium抓取失败: {e}")
            return None
        
        finally:
            if driver:
                driver.quit()
    
    def _extract_content_with_selectors(self, soup: BeautifulSoup, source: SourceConfig) -> List[Dict[str, Any]]:
        """使用选择器提取内容"""
        items = []
        selectors = source.content_selectors
        
        try:
            # 移除不需要的元素
            for exclude_selector in selectors.exclude_selectors:
                for element in soup.select(exclude_selector):
                    element.decompose()
            
            # 移除注释
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # 根据页面类型决定提取策略
            if source.content_type in [ContentType.RESEARCH, ContentType.NEWS]:
                # 研究论文或新闻列表页面，提取多个项目
                items = self._extract_multiple_items(soup, selectors, source)
            else:
                # 单篇文章或博客页面
                item = self._extract_single_item(soup, selectors, source)
                if item:
                    items = [item]
            
            # 内容质量过滤
            filtered_items = []
            for item in items:
                content_length = len(item.get("content", ""))
                if (content_length >= source.crawl_config.min_content_length and 
                    content_length <= source.crawl_config.max_content_length):
                    
                    # 计算质量分数
                    item["quality_score"] = self._calculate_quality_score(item)
                    filtered_items.append(item)
            
            return filtered_items
            
        except Exception as e:
            print(f"      内容提取失败: {e}")
            return []
    
    def _extract_multiple_items(self, soup: BeautifulSoup, selectors, source: SourceConfig) -> List[Dict[str, Any]]:
        """提取多个内容项目（用于列表页面）"""
        items = []
        
        # 查找内容容器
        content_containers = []
        
        # 尝试不同的容器选择器
        container_selectors = [
            "article", ".article", ".post", ".paper", ".entry",
            ".list-item", ".content-item", "[itemtype*='Article']"
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            if containers:
                content_containers = containers
                break
        
        # 如果没有找到容器，尝试基于标题查找
        if not content_containers and selectors.title:
            title_elements = soup.select(selectors.title)
            content_containers = [elem.find_parent() for elem in title_elements if elem.find_parent()]
        
        # 提取每个容器的内容
        for container in content_containers[:10]:  # 限制最多10个项目
            try:
                item = self._extract_item_from_container(container, selectors, source)
                if item:
                    items.append(item)
            except Exception as e:
                print(f"        提取项目失败: {e}")
                continue
        
        return items
    
    def _extract_single_item(self, soup: BeautifulSoup, selectors, source: SourceConfig) -> Optional[Dict[str, Any]]:
        """提取单个内容项目"""
        try:
            item = {
                "url": str(source.url),
                "source": str(source.url),
                "source_name": source.name,
                "type": "webpage",
                "content_type": source.content_type.value
            }
            
            # 提取各个字段
            if selectors.title:
                title_elem = soup.select_one(selectors.title)
                if title_elem:
                    item["title"] = title_elem.get_text().strip()
            
            if selectors.content:
                content_elem = soup.select_one(selectors.content)
                if content_elem:
                    item["content"] = content_elem.get_text().strip()
            
            if selectors.summary:
                summary_elem = soup.select_one(selectors.summary)
                if summary_elem:
                    item["summary"] = summary_elem.get_text().strip()
            
            if selectors.author:
                author_elem = soup.select_one(selectors.author)
                if author_elem:
                    item["author"] = author_elem.get_text().strip()
            
            if selectors.publish_date:
                date_elem = soup.select_one(selectors.publish_date)
                if date_elem:
                    item["published"] = date_elem.get_text().strip()
            
            if selectors.tags:
                tag_elems = soup.select(selectors.tags)
                item["tags"] = [elem.get_text().strip() for elem in tag_elems]
            
            # 如果没有提取到标题和内容，返回None
            if not item.get("title") and not item.get("content"):
                return None
            
            return item
            
        except Exception as e:
            print(f"        单项提取失败: {e}")
            return None
    
    def _extract_item_from_container(self, container, selectors, source: SourceConfig) -> Optional[Dict[str, Any]]:
        """从容器中提取内容项目"""
        try:
            item = {
                "source": str(source.url),
                "source_name": source.name,
                "type": "webpage",
                "content_type": source.content_type.value
            }
            
            # 在容器内查找各个字段
            if selectors.title:
                title_elem = container.select_one(selectors.title)
                if title_elem:
                    item["title"] = title_elem.get_text().strip()
            
            if selectors.link:
                link_elem = container.select_one(selectors.link)
                if link_elem:
                    href = link_elem.get("href", "")
                    if href:
                        item["url"] = urljoin(str(source.url), href)
            
            if selectors.content:
                content_elem = container.select_one(selectors.content)
                if content_elem:
                    item["content"] = content_elem.get_text().strip()
            
            if selectors.summary:
                summary_elem = container.select_one(selectors.summary)
                if summary_elem:
                    item["summary"] = summary_elem.get_text().strip()
            
            if selectors.author:
                author_elem = container.select_one(selectors.author)
                if author_elem:
                    item["author"] = author_elem.get_text().strip()
            
            if selectors.publish_date:
                date_elem = container.select_one(selectors.publish_date)
                if date_elem:
                    item["published"] = date_elem.get_text().strip()
            
            if selectors.tags:
                tag_elems = container.select(selectors.tags)
                item["tags"] = [elem.get_text().strip() for elem in tag_elems]
            
            # 设置默认URL
            if not item.get("url"):
                item["url"] = str(source.url)
            
            # 验证必要字段
            if not item.get("title"):
                return None
            
            return item
            
        except Exception as e:
            print(f"        容器提取失败: {e}")
            return None
    
    def _calculate_quality_score(self, item: Dict[str, Any]) -> float:
        """计算内容质量分数"""
        score = 0.5  # 基础分数
        
        # 标题质量
        title = item.get("title", "")
        if title:
            if len(title) > 10:
                score += 0.1
            if len(title) < 200:  # 标题不应该太长
                score += 0.1
        
        # 内容质量
        content = item.get("content", "")
        if content:
            content_length = len(content)
            if content_length > 100:
                score += 0.1
            if content_length > 500:
                score += 0.1
            if content_length < 10000:  # 内容不应该太长
                score += 0.1
        
        # 元数据完整性
        if item.get("author"):
            score += 0.05
        if item.get("published"):
            score += 0.05
        if item.get("summary"):
            score += 0.1
        if item.get("tags"):
            score += 0.05
        
        return min(1.0, score)
    
    async def _fetch_full_article(self, url: str, source: SourceConfig) -> Optional[str]:
        """获取RSS条目的完整文章内容"""
        try:
            headers = dict(source.auth_config.headers) if source.auth_config.headers else {}
            if not headers.get("User-Agent"):
                headers["User-Agent"] = random.choice(self.user_agents)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 使用简单的内容提取策略
                        content_selectors = [
                            'article', '.content', '.post-content', 
                            '.entry-content', 'main', '.main'
                        ]
                        
                        for selector in content_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                return content_elem.get_text().strip()
                        
                        # 回退到body
                        body = soup.find('body')
                        if body:
                            return body.get_text().strip()[:2000]
        
        except Exception:
            pass
        
        return None