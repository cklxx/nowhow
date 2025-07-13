"""
Workflow use cases implementation.
Orchestrates the complete content generation pipeline.
"""

import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.clean_architecture import (
    WorkflowRun, WorkflowStatus, Article, Source,
    WorkflowUseCases, SourceRepository, ArticleRepository, WorkflowRepository,
    CrawlerService, ContentProcessor, ArticleGenerator
)
from services.intelligent_source_discovery import IntelligentSourceDiscovery

logger = logging.getLogger(__name__)


class WorkflowUseCasesImpl(WorkflowUseCases):
    """Workflow use cases implementation"""
    
    def __init__(self,
                 workflow_repository: WorkflowRepository,
                 source_repository: SourceRepository,
                 article_repository: ArticleRepository,
                 crawler_service: CrawlerService,
                 content_processor: Optional[ContentProcessor] = None,
                 article_generator: Optional[ArticleGenerator] = None):
        self._workflow_repository = workflow_repository
        self._source_repository = source_repository
        self._article_repository = article_repository
        self._crawler_service = crawler_service
        self._content_processor = content_processor
        self._article_generator = article_generator
    
    async def start_workflow(self, config: Dict[str, Any]) -> WorkflowRun:
        """Start a new workflow"""
        workflow_id = str(uuid.uuid4())
        
        workflow = WorkflowRun(
            id=workflow_id,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now(),
            config=config
        )
        
        # Save initial workflow
        await self._workflow_repository.save(workflow)
        
        # Start workflow execution in background
        asyncio.create_task(self._execute_workflow(workflow))
        
        return workflow
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowRun]:
        """Get workflow status"""
        return await self._workflow_repository.find_by_id(workflow_id)
    
    async def list_workflows(self, limit: int = 10) -> List[WorkflowRun]:
        """List recent workflows"""
        return await self._workflow_repository.find_recent(limit)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow = await self._workflow_repository.find_by_id(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            return await self._workflow_repository.update_status(
                workflow_id, WorkflowStatus.CANCELLED
            )
        return False
    
    async def _execute_workflow(self, workflow: WorkflowRun):
        """Execute workflow steps"""
        try:
            # Update status to running
            await self._workflow_repository.update_status(workflow.id, WorkflowStatus.RUNNING)
            
            # Step 1: Crawl sources
            crawl_results = await self._crawl_step(workflow)
            
            # Step 2: Process content (optional)
            if self._content_processor and crawl_results.get('items'):
                processed_results = await self._process_step(workflow, crawl_results['items'])
            else:
                processed_results = crawl_results.get('items', [])
            
            # Step 3: Generate articles (optional)
            if self._article_generator and processed_results:
                articles = await self._generate_step(workflow, processed_results)
            else:
                articles = await self._create_articles_from_items(workflow, processed_results)
            
            # Save articles
            for article in articles:
                await self._article_repository.save(article)
            
            # Update workflow with results
            workflow.results = {
                'crawl_results': crawl_results,
                'articles_generated': len(articles),
                'articles': [article.id for article in articles]
            }
            workflow.completed_at = datetime.now()
            workflow.status = WorkflowStatus.COMPLETED
            
            await self._workflow_repository.save(workflow)
            
        except Exception as e:
            # Update workflow with error
            await self._workflow_repository.update_status(
                workflow.id, WorkflowStatus.FAILED, str(e)
            )
    
    async def _crawl_step(self, workflow: WorkflowRun) -> Dict[str, Any]:
        """Execute crawling step"""
        # Get sources to crawl
        source_ids = workflow.config.get('source_ids', [])
        category = workflow.config.get('category')
        topic = workflow.config.get('topic')
        
        if source_ids:
            # 使用指定的信源ID
            sources = []
            for source_id in source_ids:
                source = await self._source_repository.find_by_id(source_id)
                if source:
                    sources.append(source)
        elif topic:
            # 基于主题智能发现信源
            sources = await self._discover_sources_for_topic(topic)
        elif category:
            # 使用特定类别的信源
            sources = await self._source_repository.find_by_category(category)
        else:
            # 使用所有活跃信源
            sources = await self._source_repository.find_all(active_only=True)
        
        # Crawl sources
        all_items = []
        successful_sources = 0
        failed_sources = 0
        
        async with self._crawler_service as crawler:
            for source in sources:
                try:
                    result = await crawler.crawl_source(source)
                    if result.get('success'):
                        all_items.extend(result.get('items', []))
                        successful_sources += 1
                    else:
                        failed_sources += 1
                except Exception as e:
                    failed_sources += 1
                
                # Add delay between sources
                await asyncio.sleep(1)
        
        return {
            'total_sources': len(sources),
            'successful_sources': successful_sources,
            'failed_sources': failed_sources,
            'items': all_items,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _process_step(self, workflow: WorkflowRun, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute content processing step"""
        if not self._content_processor:
            return await self._enhance_items_with_topic(workflow, items)
        
        try:
            # 将主题信息传递给内容处理器
            processing_config = {
                'topic': workflow.config.get('topic'),
                'category': workflow.config.get('category'),
                'workflow_id': workflow.id
            }
            
            processed_items = await self._content_processor.process_content(items, processing_config)
            return await self._enhance_items_with_topic(workflow, processed_items)
        except Exception as e:
            logger.warning(f"内容处理失败，使用原始内容: {e}")
            # Fallback to original items if processing fails
            return await self._enhance_items_with_topic(workflow, items)
    
    async def _generate_step(self, workflow: WorkflowRun, processed_items: List[Dict[str, Any]]) -> List[Article]:
        """Execute article generation step"""
        if not self._article_generator:
            return await self._create_articles_from_items(workflow, processed_items)
        
        try:
            # 将主题信息传递给文章生成器
            generation_config = {
                'topic': workflow.config.get('topic'),
                'category': workflow.config.get('category'),
                'workflow_id': workflow.id
            }
            
            return await self._article_generator.generate_articles(processed_items, generation_config)
        except Exception as e:
            logger.warning(f"文章生成失败，使用默认方法: {e}")
            # Fallback to creating articles from items
            return await self._create_articles_from_items(workflow, processed_items)
    
    async def _create_articles_from_items(self, workflow: WorkflowRun, items: List[Dict[str, Any]]) -> List[Article]:
        """Create articles from crawled items"""
        articles = []
        topic = workflow.config.get('topic')
        
        for item in items:
            if not item.get('title') or not item.get('content'):
                continue
            
            # 增强文章内容以突出主题相关性
            enhanced_title = await self._enhance_title_for_topic(item['title'], topic)
            enhanced_category = self._determine_category_from_topic(topic, item.get('category', 'general'))
            
            article = Article(
                id=str(uuid.uuid4()),
                title=enhanced_title,
                content=item['content'],
                url=item.get('url', ''),
                source_id=item.get('source_id', ''),
                category=enhanced_category,
                author=item.get('author', ''),
                published_at=self._parse_datetime(item.get('published')),
                created_at=datetime.now(),
                quality_score=self._calculate_quality_score(item),
                metadata={
                    'workflow_id': workflow.id,
                    'extraction_method': item.get('extraction_method', 'unknown'),
                    'original_item': item,
                    'topic': topic,
                    'topic_relevance': item.get('topic_relevance', 0.5)
                }
            )
            
            articles.append(article)
        
        return articles
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string with fallback"""
        if not date_str:
            return None
        
        try:
            # Try common datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%a, %d %b %Y %H:%M:%S %Z'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _calculate_quality_score(self, item: Dict[str, Any]) -> float:
        """Calculate basic quality score for an item"""
        score = 0.5  # Base score
        
        title = item.get('title', '')
        content = item.get('content', '')
        
        # Title quality
        if title and 10 <= len(title) <= 200:
            score += 0.2
        
        # Content quality
        if content:
            content_length = len(content)
            if content_length > 100:
                score += 0.1
            if content_length > 500:
                score += 0.1
            if content_length < 5000:  # Not too long
                score += 0.1
        
        # Has URL
        if item.get('url'):
            score += 0.1
        
        return min(1.0, score)
    
    async def _discover_sources_for_topic(self, topic: str) -> List[Source]:
        """基于主题智能发现信源"""
        try:
            logger.info(f"开始为主题 '{topic}' 发现相关信源")
            
            # 使用智能信源发现服务
            async with IntelligentSourceDiscovery() as discovery_service:
                discovered_sources = await discovery_service.discover_sources_for_topic(topic, max_sources=8)
            
            sources = []
            for discovered in discovered_sources:
                # 检查是否已经存在
                existing_source = await self._find_existing_source_by_url(discovered.url)
                
                if existing_source:
                    # 使用现有信源，但更新相关性分数
                    existing_source.metadata['topic_relevance'] = discovered.relevance_score
                    existing_source.metadata['discovered_for_topic'] = topic
                    sources.append(existing_source)
                else:
                    # 创建新信源
                    source = discovery_service.convert_to_source(discovered)
                    source.metadata['discovered_for_topic'] = topic
                    
                    # 保存新发现的信源
                    try:
                        await self._source_repository.save(source)
                        sources.append(source)
                        logger.info(f"保存了新发现的信源: {source.name}")
                    except Exception as e:
                        logger.warning(f"保存信源失败 {source.url}: {e}")
                        # 即使保存失败，也继续使用这个信源进行爬取
                        sources.append(source)
            
            logger.info(f"为主题 '{topic}' 发现了 {len(sources)} 个信源")
            return sources
            
        except Exception as e:
            logger.error(f"为主题 '{topic}' 发现信源时出错: {e}")
            # 回退到默认信源
            return await self._source_repository.find_all(active_only=True)
    
    async def _find_existing_source_by_url(self, url: str) -> Optional[Source]:
        """通过URL查找现有信源"""
        try:
            # 这需要在repository中实现find_by_url方法
            # 暂时通过获取所有信源然后过滤来实现
            all_sources = await self._source_repository.find_all(active_only=False)
            
            for source in all_sources:
                if source.url == url:
                    return source
            
            return None
        except Exception as e:
            logger.error(f"查找现有信源时出错: {e}")
            return None
    
    async def _enhance_items_with_topic(self, workflow: WorkflowRun, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用主题信息增强内容项"""
        topic = workflow.config.get('topic')
        if not topic:
            return items
        
        enhanced_items = []
        for item in items:
            enhanced_item = item.copy()
            
            # 计算与主题的相关性
            title = item.get('title', '')
            content = item.get('content', '')
            topic_relevance = self._calculate_topic_relevance_score(topic, title, content)
            
            enhanced_item.update({
                'topic': topic,
                'topic_relevance': topic_relevance,
                'enhanced_category': self._determine_category_from_topic(topic, item.get('category', 'general'))
            })
            
            enhanced_items.append(enhanced_item)
        
        # 按主题相关性排序
        enhanced_items.sort(key=lambda x: x.get('topic_relevance', 0), reverse=True)
        
        return enhanced_items
    
    async def _enhance_title_for_topic(self, original_title: str, topic: Optional[str]) -> str:
        """为标题增加主题相关性"""
        if not topic or not original_title:
            return original_title
        
        # 简单的标题增强：如果标题中不包含主题关键词，不修改
        # 在实际实现中，可以使用AI来重写标题
        topic_lower = topic.lower()
        title_lower = original_title.lower()
        
        # 如果标题已经包含主题关键词，直接返回
        topic_keywords = set(topic_lower.split())
        title_keywords = set(title_lower.split())
        
        if topic_keywords.intersection(title_keywords):
            return original_title
        
        # 可以在这里添加AI标题重写逻辑
        return original_title
    
    def _determine_category_from_topic(self, topic: Optional[str], original_category: str) -> str:
        """根据主题确定文章类别"""
        if not topic:
            return original_category
        
        topic_lower = topic.lower()
        
        # 主题到类别的映射
        topic_category_map = {
            '机器学习': 'machine_learning',
            '深度学习': 'deep_learning',
            '人工智能': 'artificial_intelligence',
            '自然语言处理': 'nlp',
            '计算机视觉': 'computer_vision',
            '区块链': 'blockchain',
            '云计算': 'cloud_computing',
            '物联网': 'iot',
            '数据科学': 'data_science',
            '网络安全': 'cybersecurity'
        }
        
        # 查找匹配的类别
        for topic_key, category in topic_category_map.items():
            if topic_key.lower() in topic_lower or any(keyword in topic_lower for keyword in topic_key.lower().split()):
                return category
        
        # 如果没有匹配，使用原始类别
        return original_category
    
    def _calculate_topic_relevance_score(self, topic: str, title: str, content: str) -> float:
        """计算内容与主题的相关性分数"""
        try:
            import re
            
            topic_lower = topic.lower()
            title_lower = title.lower()
            content_lower = content.lower()
            
            # 提取关键词
            topic_keywords = set(re.findall(r'\w+', topic_lower))
            title_keywords = set(re.findall(r'\w+', title_lower))
            content_keywords = set(re.findall(r'\w+', content_lower))
            
            if not topic_keywords:
                return 0.5
            
            # 计算标题匹配度
            title_intersection = topic_keywords.intersection(title_keywords)
            title_score = len(title_intersection) / len(topic_keywords) if topic_keywords else 0
            
            # 计算内容匹配度
            content_intersection = topic_keywords.intersection(content_keywords)
            content_score = len(content_intersection) / len(topic_keywords) if topic_keywords else 0
            
            # 加权计算最终分数
            final_score = (title_score * 0.6) + (content_score * 0.4)
            
            # 完全匹配加分
            if topic_lower in title_lower:
                final_score += 0.3
            elif topic_lower in content_lower:
                final_score += 0.1
            
            return min(1.0, final_score)
            
        except Exception as e:
            logger.error(f"计算主题相关性时出错: {e}")
            return 0.5