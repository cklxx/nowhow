"""SQLite 数据库存储服务实现"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from core.interfaces import IStorageService
from database.connection import get_database_manager
from database.models import ArticleModel, WorkflowModel, ProcessedContentModel

class DatabaseStorageService(IStorageService):
    """基于 SQLite 数据库的存储服务"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    # 工作流相关方法
    async def save_workflow_state(self, workflow_id: str, state: Dict[str, Any]) -> str:
        """保存工作流状态"""
        session = self.db_manager.get_sync_session()
        try:
            # 查找现有工作流或创建新的
            workflow = session.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
            
            if not workflow:
                workflow = WorkflowModel(
                    id=workflow_id,
                    name=state.get('name', f'Workflow {workflow_id}'),
                    description=state.get('description', ''),
                    config=state.get('config', {}),
                    status=state.get('status', 'pending'),
                    progress=state.get('progress', 0.0),
                    current_step=state.get('current_step', ''),
                    sources_count=state.get('sources_count', 0),
                    crawled_count=state.get('crawled_count', 0),
                    processed_count=state.get('processed_count', 0),
                    articles_generated=state.get('articles_generated', 0),
                    results=state.get('results', {}),
                    error_log=state.get('error_log', []),
                    started_at=state.get('started_at'),
                    completed_at=state.get('completed_at'),
                    execution_time=state.get('execution_time')
                )
                session.add(workflow)
            else:
                # 更新现有工作流
                for key, value in state.items():
                    if hasattr(workflow, key):
                        setattr(workflow, key, value)
                workflow.updated_at = datetime.now()
            
            session.commit()
            return workflow_id
        finally:
            session.close()
    
    async def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """加载工作流状态"""
        session = self.db_manager.get_sync_session()
        try:
            workflow = session.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
            if not workflow:
                return None
            
            return {
                'id': workflow.id,
                'name': workflow.name,
                'description': workflow.description,
                'config': workflow.config,
                'status': workflow.status,
                'progress': workflow.progress,
                'current_step': workflow.current_step,
                'sources_count': workflow.sources_count,
                'crawled_count': workflow.crawled_count,
                'processed_count': workflow.processed_count,
                'articles_generated': workflow.articles_generated,
                'results': workflow.results,
                'error_log': workflow.error_log,
                'created_at': workflow.created_at,
                'updated_at': workflow.updated_at,
                'started_at': workflow.started_at,
                'completed_at': workflow.completed_at,
                'execution_time': workflow.execution_time
            }
        finally:
            session.close()
    
    # 抓取内容相关方法
    async def save_crawled_content(self, workflow_id: str, content: Dict[str, Any]) -> str:
        """保存抓取的内容"""
        # 这里我们直接在 CrawlResult 中保存，不需要单独的抓取内容表
        # 但为了兼容接口，我们返回一个标识符
        return f"crawled_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def load_crawled_content(self, workflow_id: str) -> Dict[str, Any]:
        """加载抓取的内容"""
        # 从 CrawlResult 中加载内容
        # 这里返回空，因为抓取内容现在通过 CrawlResult 管理
        return {"content": [], "metadata": {}}
    
    # 处理内容相关方法
    async def save_processed_content(self, workflow_id: str, content: Dict[str, Any]) -> str:
        """保存处理后的内容"""
        session = self.db_manager.get_sync_session()
        try:
            processed_content = ProcessedContentModel(
                workflow_id=workflow_id,
                crawl_result_id=content.get('crawl_result_id'),
                title=content.get('title'),
                content=content.get('content'),
                summary=content.get('summary'),
                keywords=content.get('keywords', []),
                category=content.get('category'),
                relevance_score=content.get('relevance_score'),
                quality_score=content.get('quality_score'),
                ai_analysis=content.get('ai_analysis', {}),
                processing_model=content.get('processing_model'),
                processing_time=content.get('processing_time'),
                word_count=content.get('word_count'),
                language=content.get('language'),
                sentiment=content.get('sentiment')
            )
            
            session.add(processed_content)
            session.commit()
            return processed_content.id
        finally:
            session.close()
    
    async def load_processed_content(self, workflow_id: str) -> Dict[str, Any]:
        """加载处理后的内容"""
        session = self.db_manager.get_sync_session()
        try:
            content_models = session.query(ProcessedContentModel).filter(
                ProcessedContentModel.workflow_id == workflow_id
            ).order_by(desc(ProcessedContentModel.processed_at)).all()
            
            content_list = []
            for model in content_models:
                content_list.append({
                    'id': model.id,
                    'workflow_id': model.workflow_id,
                    'crawl_result_id': model.crawl_result_id,
                    'title': model.title,
                    'content': model.content,
                    'summary': model.summary,
                    'keywords': model.keywords,
                    'category': model.category,
                    'relevance_score': model.relevance_score,
                    'quality_score': model.quality_score,
                    'ai_analysis': model.ai_analysis,
                    'processed_at': model.processed_at,
                    'processing_model': model.processing_model,
                    'processing_time': model.processing_time,
                    'word_count': model.word_count,
                    'language': model.language,
                    'sentiment': model.sentiment
                })
            
            return {
                'content': content_list,
                'metadata': {
                    'total_count': len(content_list),
                    'workflow_id': workflow_id,
                    'loaded_at': datetime.now().isoformat()
                }
            }
        finally:
            session.close()
    
    # 生成文章相关方法
    async def save_generated_articles(self, workflow_id: str, articles: List[Dict[str, Any]]) -> str:
        """保存生成的文章"""
        session = self.db_manager.get_sync_session()
        try:
            article_ids = []
            
            for article_data in articles:
                article = ArticleModel(
                    workflow_id=workflow_id,
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    summary=article_data.get('summary'),
                    category=article_data.get('category'),
                    tags=article_data.get('tags', []),
                    word_count=article_data.get('word_count'),
                    reading_time=article_data.get('reading_time'),
                    language=article_data.get('language', 'zh'),
                    quality_score=article_data.get('quality_score'),
                    relevance_score=article_data.get('relevance_score'),
                    ai_confidence=article_data.get('ai_confidence'),
                    source_articles=article_data.get('source_articles', []),
                    research_topics=article_data.get('research_topics', []),
                    generation_model=article_data.get('generation_model'),
                    status=article_data.get('status', 'published')
                )
                
                session.add(article)
                session.flush()  # 获取ID
                article_ids.append(article.id)
            
            session.commit()
            
            # 更新工作流统计
            workflow = session.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
            if workflow:
                workflow.articles_generated = len(articles)
                session.commit()
            
            return f"articles_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        finally:
            session.close()
    
    async def load_generated_articles(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """加载生成的文章"""
        session = self.db_manager.get_sync_session()
        try:
            query = session.query(ArticleModel)
            
            if workflow_id:
                query = query.filter(ArticleModel.workflow_id == workflow_id)
            
            articles = query.order_by(desc(ArticleModel.created_at)).all()
            
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'workflow_id': article.workflow_id,
                    'title': article.title,
                    'content': article.content,
                    'summary': article.summary,
                    'category': article.category,
                    'tags': article.tags,
                    'word_count': article.word_count,
                    'reading_time': article.reading_time,
                    'language': article.language,
                    'quality_score': article.quality_score,
                    'relevance_score': article.relevance_score,
                    'ai_confidence': article.ai_confidence,
                    'source_articles': article.source_articles,
                    'research_topics': article.research_topics,
                    'generation_model': article.generation_model,
                    'status': article.status,
                    'created_at': article.created_at.isoformat() if article.created_at else None,
                    'updated_at': article.updated_at.isoformat() if article.updated_at else None
                })
            
            return result
        finally:
            session.close()
    
    # 文件操作相关方法
    async def save_json(self, data: Union[Dict, List], filename: str, workflow_id: Optional[str] = None) -> Path:
        """保存JSON数据到文件"""
        # 为了向后兼容，保留文件保存功能
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    async def load_json(self, filepath: Union[str, Path]) -> Union[Dict, List]:
        """从文件加载JSON数据"""
        filepath = Path(filepath)
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def list_files(self, pattern: str) -> List[str]:
        """列出符合模式的文件"""
        # 为了向后兼容，返回空列表
        return []
    
    async def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        return Path(filename).exists()
    
    async def delete_file(self, filename: str) -> bool:
        """删除文件"""
        try:
            Path(filename).unlink()
            return True
        except:
            return False
    
    # 实现抽象方法
    async def save_text(self, content: str, filename: str) -> str:
        """保存文本到文件"""
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    async def load_text(self, filename: str) -> str:
        """从文件加载文本"""
        filepath = Path(filename)
        if not filepath.exists():
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def get_file_path(self, filename: str) -> str:
        """获取文件路径"""
        return str(Path(filename).absolute())
    
    # 统计和缓存方法
    async def get_article_statistics(self) -> Dict[str, Any]:
        """获取文章统计信息"""
        session = self.db_manager.get_sync_session()
        try:
            total_articles = session.query(ArticleModel).count()
            
            # 按分类统计
            category_stats = session.query(
                ArticleModel.category,
                func.count(ArticleModel.id)
            ).group_by(ArticleModel.category).all()
            
            categories = {cat: count for cat, count in category_stats if cat}
            
            # 总字数
            total_words = session.query(func.sum(ArticleModel.word_count)).scalar() or 0
            avg_words = total_words / total_articles if total_articles > 0 else 0
            
            # 按状态统计
            status_stats = session.query(
                ArticleModel.status,
                func.count(ArticleModel.id)
            ).group_by(ArticleModel.status).all()
            
            return {
                'total_articles': total_articles,
                'categories': categories,
                'total_words': total_words,
                'average_words': int(avg_words),
                'by_status': {status: count for status, count in status_stats}
            }
        finally:
            session.close()
    
    async def get_latest_articles(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最新文章"""
        session = self.db_manager.get_sync_session()
        try:
            articles = session.query(ArticleModel).order_by(
                desc(ArticleModel.created_at)
            ).limit(limit).all()
            
            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'workflow_id': article.workflow_id,
                    'title': article.title,
                    'content': article.content,
                    'summary': article.summary,
                    'category': article.category,
                    'tags': article.tags,
                    'word_count': article.word_count,
                    'reading_time': article.reading_time,
                    'language': article.language,
                    'quality_score': article.quality_score,
                    'relevance_score': article.relevance_score,
                    'ai_confidence': article.ai_confidence,
                    'source_articles': article.source_articles,
                    'research_topics': article.research_topics,
                    'generation_model': article.generation_model,
                    'status': article.status,
                    'created_at': article.created_at.isoformat() if article.created_at else None,
                    'updated_at': article.updated_at.isoformat() if article.updated_at else None
                })
            
            return result
        finally:
            session.close()
    
    # 数据迁移辅助方法
    async def migrate_from_files(self, data_dir: Path):
        """从文件系统迁移数据到数据库"""
        session = self.db_manager.get_sync_session()
        try:
            # 迁移文章数据
            articles_dir = data_dir / "articles"
            if articles_dir.exists():
                for json_file in articles_dir.glob("articles_*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # 提取 workflow_id
                        filename = json_file.stem
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            workflow_id = parts[-1]
                        else:
                            workflow_id = "migrated_" + filename
                        
                        # 处理文章数据
                        articles = data.get('articles', []) if isinstance(data, dict) else data
                        
                        for article_data in articles:
                            # 检查是否已存在
                            existing = session.query(ArticleModel).filter(
                                and_(
                                    ArticleModel.title == article_data.get('title'),
                                    ArticleModel.workflow_id == workflow_id
                                )
                            ).first()
                            
                            if not existing:
                                article = ArticleModel(
                                    workflow_id=workflow_id,
                                    title=article_data.get('title'),
                                    content=article_data.get('content'),
                                    summary=article_data.get('summary'),
                                    category=article_data.get('category'),
                                    tags=article_data.get('tags', []),
                                    word_count=len(article_data.get('content', '').split()) if article_data.get('content') else 0,
                                    language=article_data.get('language', 'zh'),
                                    quality_score=article_data.get('quality_score'),
                                    relevance_score=article_data.get('relevance_score'),
                                    ai_confidence=article_data.get('ai_confidence'),
                                    source_articles=article_data.get('source_articles', []),
                                    research_topics=article_data.get('research_topics', []),
                                    generation_model=article_data.get('generation_model'),
                                    status='published'
                                )
                                session.add(article)
                    
                    except Exception as e:
                        print(f"Failed to migrate article file {json_file}: {e}")
            
            # 迁移工作流数据
            workflows_dir = data_dir / "workflows"
            if workflows_dir.exists():
                for json_file in workflows_dir.glob("workflow_*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        workflow_id = data.get('id', json_file.stem)
                        
                        # 检查是否已存在
                        existing = session.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
                        
                        if not existing:
                            workflow = WorkflowModel(
                                id=workflow_id,
                                name=data.get('name', f'Migrated Workflow {workflow_id}'),
                                description=data.get('description', ''),
                                config=data.get('config', {}),
                                status=data.get('status', 'completed'),
                                progress=data.get('progress', 100.0),
                                current_step=data.get('current_step', ''),
                                sources_count=data.get('sources_count', 0),
                                crawled_count=data.get('crawled_count', 0),
                                processed_count=data.get('processed_count', 0),
                                articles_generated=data.get('articles_generated', 0),
                                results=data.get('results', {}),
                                error_log=data.get('error_log', []),
                                execution_time=data.get('execution_time')
                            )
                            session.add(workflow)
                    
                    except Exception as e:
                        print(f"Failed to migrate workflow file {json_file}: {e}")
            
            session.commit()
            print("Data migration completed successfully")
            
        except Exception as e:
            session.rollback()
            print(f"Migration failed: {e}")
            raise
        finally:
            session.close()