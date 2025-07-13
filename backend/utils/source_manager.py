import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

from models.source_config import SourceConfig, CrawlResult, SourceType, ContentType

class SourceManager:
    """信源配置管理器"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent.parent
            base_path = current_dir
        
        self.base_path = Path(base_path)
        self.sources_path = self.base_path / "sources"
        self.results_path = self.base_path / "crawl_results"
        
        # 创建目录
        self.sources_path.mkdir(exist_ok=True)
        self.results_path.mkdir(exist_ok=True)
        
        # 初始化内置信源
        self._init_builtin_sources()
    
    def _init_builtin_sources(self):
        """初始化内置信源配置"""
        builtin_sources = [
            {
                "name": "OpenAI Blog",
                "url": "https://blog.openai.com/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.BLOG,
                "description": "OpenAI官方博客，发布最新AI研究和产品动态",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1.f-display",
                    "content": "article .post-content",
                    "summary": "meta[name='description']",
                    "publish_date": "time",
                    "exclude_selectors": ["nav", "footer", ".sidebar", "script", "style"]
                }
            },
            {
                "name": "Google AI Blog",
                "url": "https://ai.googleblog.com/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.RESEARCH,
                "description": "Google AI研究博客",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h3.post-title",
                    "content": ".post-body",
                    "author": ".post-author",
                    "publish_date": ".published",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style"]
                }
            },
            {
                "name": "ArXiv AI Papers",
                "url": "https://arxiv.org/list/cs.AI/recent",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.RESEARCH,
                "description": "ArXiv人工智能最新论文列表",
                "is_built_in": True,
                "content_selectors": {
                    "title": "div.list-title",
                    "content": "div.list-subjects + p",
                    "author": "div.list-authors",
                    "link": "dt a[href*='/abs/']",
                    "exclude_selectors": ["nav", "footer", "script", "style"]
                }
            },
            {
                "name": "Papers with Code",
                "url": "https://paperswithcode.com/latest",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.RESEARCH,
                "description": "最新机器学习论文与代码",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1",
                    "content": ".paper-abstract",
                    "tags": ".badge",
                    "link": "a[href*='/paper/']",
                    "exclude_selectors": ["nav", "footer", "script", "style"]
                }
            },
            {
                "name": "Hugging Face Papers",
                "url": "https://huggingface.co/papers",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.RESEARCH,
                "description": "Hugging Face精选AI论文",
                "is_built_in": True,
                "crawl_config": {
                    "render_js": True,
                    "wait_for_selector": ".paper-title"
                },
                "content_selectors": {
                    "title": ".paper-title",
                    "content": ".paper-description",
                    "author": ".paper-authors",
                    "tags": ".badge",
                    "exclude_selectors": ["nav", "footer", "script", "style"]
                }
            },
            # Chinese AI News Sources
            {
                "name": "机器之心",
                "url": "https://www.jiqizhixin.com/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.NEWS,
                "description": "专业的人工智能媒体和产业服务平台，关注AI领域最新动态",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1, .article-title",
                    "content": ".article-content, .content",
                    "author": ".author",
                    "publish_date": ".time, .publish-time",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "量子位",
                "url": "https://www.qbitai.com/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.NEWS,
                "description": "追踪人工智能新趋势，报道科技行业新突破",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1, .post-title",
                    "content": ".post-content, .article-content",
                    "author": ".author",
                    "publish_date": ".publish-time, .time",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "爱范儿",
                "url": "https://www.ifanr.com/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.NEWS,
                "description": "数字公民的糖，专注科技和创新产品报道",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1, .article-title",
                    "content": ".article-content, .post-content",
                    "author": ".author, .byline",
                    "publish_date": ".time, .date",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "新智元",
                "url": "https://www.synced.cn/",
                "type": SourceType.WEBSITE,
                "content_type": ContentType.NEWS,
                "description": "人工智能和机器人前沿发展报道",
                "is_built_in": True,
                "content_selectors": {
                    "title": "h1, .title",
                    "content": ".content, .article-body",
                    "author": ".author",
                    "publish_date": ".time, .date",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            # International AI News Sources
            {
                "name": "TechCrunch AI",
                "url": "https://techcrunch.com/category/artificial-intelligence/",
                "type": SourceType.RSS,
                "content_type": ContentType.NEWS,
                "description": "TechCrunch AI和人工智能新闻",
                "is_built_in": True,
                "rss_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
                "content_selectors": {
                    "title": "h1, .article-title",
                    "content": ".article-content",
                    "author": ".author",
                    "publish_date": ".date",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "VentureBeat AI",
                "url": "https://venturebeat.com/category/ai/",
                "type": SourceType.RSS,
                "content_type": ContentType.NEWS,
                "description": "VentureBeat AI新闻和分析",
                "is_built_in": True,
                "rss_url": "https://venturebeat.com/category/ai/feed/",
                "content_selectors": {
                    "title": "h1, .article-title",
                    "content": ".article-content, .entry-content",
                    "author": ".author",
                    "publish_date": ".date, .published",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "Towards Data Science",
                "url": "https://towardsdatascience.com/",
                "type": SourceType.RSS,
                "content_type": ContentType.RESEARCH,
                "description": "数据科学和机器学习文章分享平台",
                "is_built_in": True,
                "rss_url": "https://towardsdatascience.com/feed",
                "content_selectors": {
                    "title": "h1",
                    "content": "article, .post-content",
                    "author": ".author",
                    "publish_date": ".published-date",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style"]
                }
            },
            {
                "name": "AI News",
                "url": "https://www.artificialintelligence-news.com/",
                "type": SourceType.RSS,
                "content_type": ContentType.NEWS,
                "description": "国际AI新闻和分析",
                "is_built_in": True,
                "rss_url": "https://www.artificialintelligence-news.com/feed/",
                "content_selectors": {
                    "title": "h1, .entry-title",
                    "content": ".entry-content",
                    "author": ".author",
                    "publish_date": ".published",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            },
            {
                "name": "Unite AI",
                "url": "https://www.unite.ai/",
                "type": SourceType.RSS,
                "content_type": ContentType.NEWS,
                "description": "AI新闻、工具和资源",
                "is_built_in": True,
                "rss_url": "https://www.unite.ai/feed/",
                "content_selectors": {
                    "title": "h1, .entry-title",
                    "content": ".entry-content",
                    "author": ".author",
                    "publish_date": ".date",
                    "exclude_selectors": ["nav", "footer", "sidebar", "script", "style", ".ad"]
                }
            }
        ]
        
        for source_data in builtin_sources:
            # 检查是否已存在
            domain = urlparse(str(source_data["url"])).netloc
            existing = self.get_source_by_domain(domain)
            
            if not existing:
                source = SourceConfig(**source_data)
                source.id = self._generate_id()
                self.save_source(source)
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())[:8]
    
    def save_source(self, source: SourceConfig) -> str:
        """保存信源配置"""
        if not source.id:
            source.id = self._generate_id()
        
        source.updated_at = datetime.now()
        
        filepath = self.sources_path / f"{source.id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(source.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        return source.id
    
    def get_source(self, source_id: str) -> Optional[SourceConfig]:
        """获取信源配置"""
        filepath = self.sources_path / f"{source_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return SourceConfig(**data)
    
    def get_all_sources(self, include_inactive: bool = False) -> List[SourceConfig]:
        """获取所有信源配置"""
        sources = []
        
        for filepath in self.sources_path.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    source = SourceConfig(**data)
                    
                    if include_inactive or source.is_active:
                        sources.append(source)
            except Exception as e:
                print(f"Error loading source config {filepath}: {e}")
        
        # 按创建时间排序
        sources.sort(key=lambda x: x.created_at, reverse=True)
        return sources
    
    def get_active_sources(self) -> List[SourceConfig]:
        """获取激活的信源配置"""
        return self.get_all_sources(include_inactive=False)
    
    def get_sources_by_type(self, source_type: SourceType) -> List[SourceConfig]:
        """按类型获取信源"""
        all_sources = self.get_all_sources()
        return [s for s in all_sources if s.type == source_type]
    
    def get_source_by_domain(self, domain: str) -> Optional[SourceConfig]:
        """根据域名查找信源"""
        all_sources = self.get_all_sources()
        for source in all_sources:
            source_domain = urlparse(str(source.url)).netloc
            if source_domain == domain:
                return source
        return None
    
    def delete_source(self, source_id: str) -> bool:
        """删除信源配置"""
        source = self.get_source(source_id)
        if not source:
            return False
        
        # 不允许删除内置信源
        if source.is_built_in:
            return False
        
        filepath = self.sources_path / f"{source_id}.json"
        filepath.unlink()
        return True
    
    def update_source(self, source_id: str, updates: Dict[str, Any]) -> bool:
        """更新信源配置"""
        source = self.get_source(source_id)
        if not source:
            return False
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        source.updated_at = datetime.now()
        self.save_source(source)
        return True
    
    def save_crawl_result(self, result: CrawlResult) -> str:
        """保存抓取结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result_{timestamp}_{result.source_id}.json"
        filepath = self.results_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # 更新信源统计
        source = self.get_source(result.source_id)
        if source:
            source.crawl_count += 1
            source.last_crawled = result.timestamp
            
            if result.success:
                source.success_count += 1
            else:
                source.error_count += 1
            
            self.save_source(source)
        
        return str(filepath)
    
    def get_crawl_results(self, source_id: str, limit: int = 10) -> List[CrawlResult]:
        """获取抓取结果"""
        results = []
        
        pattern = f"result_*_{source_id}.json"
        for filepath in sorted(self.results_path.glob(pattern), reverse=True):
            if len(results) >= limit:
                break
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(CrawlResult(**data))
            except Exception as e:
                print(f"Error loading crawl result {filepath}: {e}")
        
        return results
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """获取信源统计信息"""
        sources = self.get_all_sources(include_inactive=True)
        
        stats = {
            "total_sources": len(sources),
            "active_sources": len([s for s in sources if s.is_active]),
            "builtin_sources": len([s for s in sources if s.is_built_in]),
            "user_sources": len([s for s in sources if not s.is_built_in]),
            "by_type": {},
            "by_content_type": {},
            "total_crawls": sum(s.crawl_count for s in sources),
            "total_successes": sum(s.success_count for s in sources),
            "total_errors": sum(s.error_count for s in sources)
        }
        
        # 按类型统计
        for source_type in SourceType:
            count = len([s for s in sources if s.type == source_type])
            stats["by_type"][source_type.value] = count
        
        # 按内容类型统计
        for content_type in ContentType:
            count = len([s for s in sources if s.content_type == content_type])
            stats["by_content_type"][content_type.value] = count
        
        return stats
    
    def export_sources(self) -> Dict[str, Any]:
        """导出所有信源配置"""
        sources = self.get_all_sources(include_inactive=True)
        return {
            "export_time": datetime.now().isoformat(),
            "total_count": len(sources),
            "sources": [source.dict() for source in sources]
        }
    
    def import_sources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """导入信源配置"""
        if "sources" not in data:
            return {"success": False, "error": "Invalid import data"}
        
        imported = 0
        skipped = 0
        errors = []
        
        for source_data in data["sources"]:
            try:
                # 检查是否已存在同样的URL
                url = source_data.get("url")
                if url:
                    domain = urlparse(str(url)).netloc
                    existing = self.get_source_by_domain(domain)
                    if existing:
                        skipped += 1
                        continue
                
                # 创建新的源配置
                source_data["id"] = None  # 重新生成ID
                source_data["is_built_in"] = False  # 导入的都是用户源
                source = SourceConfig(**source_data)
                self.save_source(source)
                imported += 1
                
            except Exception as e:
                errors.append(f"Failed to import source {source_data.get('name', 'Unknown')}: {str(e)}")
        
        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "errors": errors
        }