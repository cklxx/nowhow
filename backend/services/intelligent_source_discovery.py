"""
Intelligent Source Discovery Service
基于主题智能发现相关信源
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup

from core.clean_architecture import Source, SourceType


logger = logging.getLogger(__name__)


@dataclass
class DiscoveredSource:
    """发现的信源"""
    url: str
    title: str
    description: str
    type: SourceType
    relevance_score: float
    content_type: str = "article"
    category: str = "discovered"


class IntelligentSourceDiscovery:
    """智能信源发现服务"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 预定义的高质量AI相关信源
        self.ai_sources = {
            "机器学习": [
                ("https://arxiv.org/rss/cs.LG", "ArXiv机器学习论文", "最新机器学习研究论文", SourceType.RSS),
                ("https://ai.googleblog.com/feeds/posts/default", "Google AI博客", "Google AI研究和产品更新", SourceType.RSS),
                ("https://openai.com/blog/rss/", "OpenAI博客", "OpenAI最新研究和产品", SourceType.RSS),
                ("https://research.facebook.com/blog/rss/", "Meta AI研究", "Meta AI研究成果", SourceType.RSS),
            ],
            "人工智能": [
                ("https://arxiv.org/rss/cs.AI", "ArXiv人工智能论文", "最新AI研究论文", SourceType.RSS),
                ("https://ai.googleblog.com/feeds/posts/default", "Google AI博客", "Google AI研究进展", SourceType.RSS),
                ("https://blogs.microsoft.com/ai/feed/", "Microsoft AI博客", "微软AI技术和应用", SourceType.RSS),
                ("https://deepmind.com/blog/feed/basic/", "DeepMind博客", "DeepMind研究突破", SourceType.RSS),
            ],
            "深度学习": [
                ("https://arxiv.org/rss/cs.LG", "ArXiv深度学习论文", "深度学习最新研究", SourceType.RSS),
                ("https://pytorch.org/blog/feed.xml", "PyTorch博客", "PyTorch框架更新", SourceType.RSS),
                ("https://blog.tensorflow.org/feeds/posts/default", "TensorFlow博客", "TensorFlow技术分享", SourceType.RSS),
                ("https://distill.pub/rss.xml", "Distill期刊", "可视化机器学习解释", SourceType.RSS),
            ],
            "自然语言处理": [
                ("https://arxiv.org/rss/cs.CL", "ArXiv NLP论文", "自然语言处理研究", SourceType.RSS),
                ("https://huggingface.co/blog/feed.xml", "Hugging Face博客", "NLP模型和工具", SourceType.RSS),
                ("https://ai.googleblog.com/feeds/posts/default", "Google AI NLP", "Google NLP研究", SourceType.RSS),
            ],
            "计算机视觉": [
                ("https://arxiv.org/rss/cs.CV", "ArXiv计算机视觉论文", "计算机视觉研究", SourceType.RSS),
                ("https://ai.googleblog.com/feeds/posts/default", "Google AI Vision", "Google视觉AI研究", SourceType.RSS),
                ("https://research.facebook.com/blog/rss/", "Meta视觉研究", "Meta计算机视觉", SourceType.RSS),
            ],
            "区块链": [
                ("https://blog.ethereum.org/feed.xml", "以太坊官方博客", "以太坊技术更新", SourceType.RSS),
                ("https://bitcoinmagazine.com/.rss/full/", "比特币杂志", "区块链技术和新闻", SourceType.RSS),
                ("https://www.coindesk.com/arc/outbound-feeds/rss/", "CoinDesk", "加密货币和区块链新闻", SourceType.RSS),
            ],
            "云计算": [
                ("https://aws.amazon.com/blogs/aws/feed/", "AWS博客", "AWS云服务更新", SourceType.RSS),
                ("https://azure.microsoft.com/en-us/blog/feed/", "Azure博客", "Microsoft Azure云计算", SourceType.RSS),
                ("https://cloud.google.com/blog/rss", "Google Cloud博客", "Google云平台技术", SourceType.RSS),
            ],
        }
        
        # 搜索引擎用于发现新信源
        self.search_engines = [
            "https://www.google.com/search?q={query}+RSS+feed",
            "https://www.bing.com/search?q={query}+blog+RSS",
        ]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'AI Content Aggregator - Source Discovery Bot 1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def discover_sources_for_topic(self, topic: str, max_sources: int = 10) -> List[DiscoveredSource]:
        """基于主题发现相关信源"""
        try:
            discovered_sources = []
            
            # 1. 从预定义源中匹配
            predefined_sources = await self._find_predefined_sources(topic)
            discovered_sources.extend(predefined_sources)
            
            # 2. 智能搜索发现新源
            if len(discovered_sources) < max_sources:
                search_sources = await self._search_for_sources(topic, max_sources - len(discovered_sources))
                discovered_sources.extend(search_sources)
            
            # 3. 按相关性排序
            discovered_sources.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"为主题 '{topic}' 发现了 {len(discovered_sources)} 个信源")
            return discovered_sources[:max_sources]
            
        except Exception as e:
            logger.error(f"为主题 '{topic}' 发现信源时出错: {e}")
            return []
    
    async def _find_predefined_sources(self, topic: str) -> List[DiscoveredSource]:
        """从预定义源中查找匹配的信源"""
        discovered = []
        topic_lower = topic.lower()
        
        for category, sources in self.ai_sources.items():
            category_lower = category.lower()
            
            # 计算相关性分数
            relevance_score = self._calculate_topic_relevance(topic_lower, category_lower)
            
            if relevance_score > 0.3:  # 相关性阈值
                for url, title, description, source_type in sources:
                    discovered_source = DiscoveredSource(
                        url=url,
                        title=title,
                        description=description,
                        type=source_type,
                        relevance_score=relevance_score,
                        content_type="article",
                        category=category
                    )
                    discovered.append(discovered_source)
        
        return discovered
    
    async def _search_for_sources(self, topic: str, max_sources: int) -> List[DiscoveredSource]:
        """通过搜索发现新的信源"""
        discovered = []
        
        try:
            # 搜索RSS feeds和博客
            search_queries = [
                f"{topic} RSS feed",
                f"{topic} 博客 RSS",
                f"{topic} 技术博客",
                f"{topic} 官方博客 RSS",
            ]
            
            for query in search_queries[:2]:  # 限制搜索次数
                sources = await self._search_rss_feeds(query)
                discovered.extend(sources)
                
                if len(discovered) >= max_sources:
                    break
            
            return discovered[:max_sources]
            
        except Exception as e:
            logger.error(f"搜索信源时出错: {e}")
            return []
    
    async def _search_rss_feeds(self, query: str) -> List[DiscoveredSource]:
        """搜索RSS feeds"""
        discovered = []
        
        try:
            # 这里可以集成真实的搜索API
            # 为演示，返回一些常用的技术博客RSS
            fallback_sources = [
                ("https://techcrunch.com/feed/", "TechCrunch", "科技新闻和创业资讯", SourceType.RSS),
                ("https://www.theverge.com/rss/index.xml", "The Verge", "科技和数字文化", SourceType.RSS),
                ("https://arstechnica.com/feeds/rss/", "Ars Technica", "技术深度分析", SourceType.RSS),
                ("https://www.wired.com/feed/rss", "Wired", "科技和创新", SourceType.RSS),
            ]
            
            for url, title, description, source_type in fallback_sources:
                # 验证RSS是否可访问
                if await self._validate_rss_feed(url):
                    relevance_score = self._calculate_topic_relevance(query.lower(), title.lower() + " " + description.lower())
                    
                    if relevance_score > 0.2:
                        discovered_source = DiscoveredSource(
                            url=url,
                            title=title,
                            description=description,
                            type=source_type,
                            relevance_score=relevance_score,
                            content_type="article",
                            category="technology"
                        )
                        discovered.append(discovered_source)
            
            return discovered
            
        except Exception as e:
            logger.error(f"搜索RSS feeds时出错: {e}")
            return []
    
    async def _validate_rss_feed(self, url: str) -> bool:
        """验证RSS feed是否可访问"""
        try:
            if not self.session:
                return False
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    # 简单检查是否包含RSS标记
                    return any(tag in content.lower() for tag in ['<rss', '<feed', '<channel'])
                return False
        except Exception:
            return False
    
    def _calculate_topic_relevance(self, topic: str, text: str) -> float:
        """计算主题相关性分数"""
        try:
            # 简单的关键词匹配算法
            topic_keywords = set(re.findall(r'\w+', topic.lower()))
            text_keywords = set(re.findall(r'\w+', text.lower()))
            
            if not topic_keywords:
                return 0.0
            
            # 计算关键词重叠度
            intersection = topic_keywords.intersection(text_keywords)
            base_score = len(intersection) / len(topic_keywords)
            
            # 加权计算
            if topic in text.lower():
                base_score += 0.3  # 完全匹配加分
            
            # 相关词汇加分
            ai_terms = {"ai", "artificial", "intelligence", "machine", "learning", "deep", "neural", "algorithm"}
            if topic_keywords.intersection(ai_terms) and text_keywords.intersection(ai_terms):
                base_score += 0.2
            
            return min(1.0, base_score)
            
        except Exception:
            return 0.0
    
    def convert_to_source(self, discovered: DiscoveredSource) -> Source:
        """将发现的信源转换为Source对象"""
        return Source(
            id=f"discovered_{hash(discovered.url)}",
            name=discovered.title,
            url=discovered.url,
            type=discovered.type,
            category=discovered.category,
            active=True,
            created_at=None,  # 会在保存时设置
            metadata={
                'discovered': True,
                'relevance_score': discovered.relevance_score,
                'description': discovered.description,
                'content_type': discovered.content_type,
                'discovery_method': 'intelligent_search'
            }
        )