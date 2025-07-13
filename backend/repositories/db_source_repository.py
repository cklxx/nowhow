"""SQLite 数据库信源存储库实现"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from core.interfaces import ISourceRepository
from database.connection import get_database_manager
from database.models import SourceModel, CrawlResultModel
from models.source_config import SourceConfig, CrawlResult, SourceType, ContentType

class DatabaseSourceRepository(ISourceRepository):
    """基于 SQLite 数据库的信源存储库"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    def _source_model_to_config(self, model: SourceModel) -> SourceConfig:
        """将数据库模型转换为配置对象"""
        return SourceConfig(
            id=model.id,
            name=model.name,
            url=model.url,
            type=SourceType(model.type),
            content_type=ContentType(model.content_type),
            description=model.description,
            crawl_config=model.crawl_config or {},
            auth_config=model.auth_config or {},
            content_selectors=model.content_selectors or {},
            ai_analyzed=model.ai_analyzed,
            ai_analysis_time=model.ai_analysis_time,
            ai_confidence=model.ai_confidence,
            ai_suggestions=model.ai_suggestions or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_crawled=model.last_crawled,
            crawl_count=model.crawl_count,
            success_count=model.success_count,
            error_count=model.error_count,
            is_active=model.is_active,
            is_built_in=model.is_built_in,
            created_by=model.created_by,
            quality_score=model.quality_score,
            relevance_score=model.relevance_score
        )
    
    def _config_to_source_model(self, config: SourceConfig) -> SourceModel:
        """将配置对象转换为数据库模型"""
        # 安全地获取 enum 值
        def get_enum_value(enum_obj):
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # 安全地转换复杂对象为字典
        def safe_dict_convert(obj):
            if obj is None:
                return {}
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, dict):
                return obj
            else:
                return {}
        
        return SourceModel(
            id=config.id,
            name=config.name,
            url=str(config.url),
            type=get_enum_value(config.type),
            content_type=get_enum_value(config.content_type),
            description=config.description,
            crawl_config=safe_dict_convert(config.crawl_config),
            auth_config=safe_dict_convert(config.auth_config),
            content_selectors=safe_dict_convert(config.content_selectors),
            ai_analyzed=config.ai_analyzed,
            ai_analysis_time=config.ai_analysis_time,
            ai_confidence=config.ai_confidence,
            ai_suggestions=config.ai_suggestions,
            created_at=config.created_at,
            updated_at=config.updated_at,
            last_crawled=config.last_crawled,
            crawl_count=config.crawl_count,
            success_count=config.success_count,
            error_count=config.error_count,
            is_active=config.is_active,
            is_built_in=config.is_built_in,
            created_by=config.created_by,
            quality_score=config.quality_score,
            relevance_score=config.relevance_score
        )
    
    async def create(self, source_data: Dict[str, Any]) -> str:
        """创建新的信源配置"""
        try:
            # 创建 SourceConfig 对象
            source_config = SourceConfig(**source_data)
            
            # 转换为数据库模型
            source_model = self._config_to_source_model(source_config)
            
            # 保存到数据库
            session = self.db_manager.get_sync_session()
            try:
                session.add(source_model)
                session.commit()
                return source_model.id
            finally:
                session.close()
                
        except Exception as e:
            raise Exception(f"Failed to create source: {e}")
    
    async def get_by_id(self, source_id: str) -> Optional[SourceConfig]:
        """根据ID获取信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            model = session.query(SourceModel).filter(SourceModel.id == source_id).first()
            if model:
                return self._source_model_to_config(model)
            return None
        finally:
            session.close()
    
    async def get_all(self) -> List[SourceConfig]:
        """获取所有信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            models = session.query(SourceModel).order_by(desc(SourceModel.created_at)).all()
            return [self._source_model_to_config(model) for model in models]
        finally:
            session.close()
    
    async def get_active(self) -> List[SourceConfig]:
        """获取活跃的信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            models = session.query(SourceModel).filter(
                SourceModel.is_active == True
            ).order_by(desc(SourceModel.created_at)).all()
            return [self._source_model_to_config(model) for model in models]
        finally:
            session.close()
    
    async def get_active_sources(self) -> List[Dict[str, Any]]:
        """获取活跃的信源配置（兼容性方法）"""
        configs = await self.get_active()
        # Convert SourceConfig objects to dictionaries for compatibility
        return [self._source_config_to_dict(config) for config in configs]
    
    def _source_config_to_dict(self, config: SourceConfig) -> Dict[str, Any]:
        """将 SourceConfig 转换为字典"""
        return {
            'id': config.id,
            'name': config.name,
            'url': str(config.url),
            'type': config.type.value if hasattr(config.type, 'value') else str(config.type),
            'content_type': config.content_type.value if hasattr(config.content_type, 'value') else str(config.content_type),
            'description': config.description,
            'crawl_config': config.crawl_config or {},
            'auth_config': config.auth_config or {},
            'content_selectors': config.content_selectors or {},
            'is_active': config.is_active,
            'is_built_in': config.is_built_in,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            'last_crawled': config.last_crawled.isoformat() if config.last_crawled else None,
            'crawl_count': config.crawl_count,
            'success_count': config.success_count,
            'error_count': config.error_count,
            'quality_score': config.quality_score,
            'relevance_score': config.relevance_score
        }
    
    async def get_by_type(self, source_type: str) -> List[SourceConfig]:
        """根据类型获取信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            models = session.query(SourceModel).filter(
                and_(SourceModel.type == source_type, SourceModel.is_active == True)
            ).order_by(desc(SourceModel.created_at)).all()
            return [self._source_model_to_config(model) for model in models]
        finally:
            session.close()
    
    async def get_by_category(self, category: str) -> List[SourceConfig]:
        """根据内容类型获取信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            models = session.query(SourceModel).filter(
                and_(SourceModel.content_type == category, SourceModel.is_active == True)
            ).order_by(desc(SourceModel.created_at)).all()
            return [self._source_model_to_config(model) for model in models]
        finally:
            session.close()
    
    async def update(self, source_id: str, updates: Dict[str, Any]) -> SourceConfig:
        """更新信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            model = session.query(SourceModel).filter(SourceModel.id == source_id).first()
            if not model:
                raise Exception(f"Source not found: {source_id}")
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            
            model.updated_at = datetime.now()
            session.commit()
            
            return self._source_model_to_config(model)
        finally:
            session.close()
    
    async def delete(self, source_id: str) -> bool:
        """删除信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            model = session.query(SourceModel).filter(SourceModel.id == source_id).first()
            if not model:
                return False
            
            # 不允许删除内置信源
            if model.is_built_in:
                return False
            
            session.delete(model)
            session.commit()
            return True
        finally:
            session.close()
    
    async def get_categories(self) -> List[str]:
        """获取所有内容类型分类"""
        session = self.db_manager.get_sync_session()
        try:
            categories = session.query(SourceModel.content_type).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        finally:
            session.close()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        session = self.db_manager.get_sync_session()
        try:
            total_sources = session.query(SourceModel).count()
            active_sources = session.query(SourceModel).filter(SourceModel.is_active == True).count()
            builtin_sources = session.query(SourceModel).filter(SourceModel.is_built_in == True).count()
            
            # 按类型统计
            type_stats = {}
            for source_type in SourceType:
                count = session.query(SourceModel).filter(SourceModel.type == source_type.value).count()
                type_stats[source_type.value] = count
            
            # 按内容类型统计
            content_type_stats = {}
            for content_type in ContentType:
                count = session.query(SourceModel).filter(SourceModel.content_type == content_type.value).count()
                content_type_stats[content_type.value] = count
            
            # 抓取统计
            crawl_stats = session.query(
                session.query(SourceModel.crawl_count).label('total_crawls'),
                session.query(SourceModel.success_count).label('total_successes'),
                session.query(SourceModel.error_count).label('total_errors')
            ).first()
            
            return {
                "total_sources": total_sources,
                "active_sources": active_sources,
                "builtin_sources": builtin_sources,
                "user_sources": total_sources - builtin_sources,
                "by_type": type_stats,
                "by_content_type": content_type_stats,
                "total_crawls": sum(model.crawl_count for model in session.query(SourceModel).all()),
                "total_successes": sum(model.success_count for model in session.query(SourceModel).all()),
                "total_errors": sum(model.error_count for model in session.query(SourceModel).all())
            }
        finally:
            session.close()
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[SourceConfig]:
        """搜索信源配置"""
        session = self.db_manager.get_sync_session()
        try:
            q = session.query(SourceModel)
            
            # 文本搜索
            if query:
                q = q.filter(
                    or_(
                        SourceModel.name.contains(query),
                        SourceModel.description.contains(query),
                        SourceModel.url.contains(query)
                    )
                )
            
            # 应用过滤器
            if filters:
                if filters.get('type'):
                    q = q.filter(SourceModel.type == filters['type'])
                if filters.get('content_type'):
                    q = q.filter(SourceModel.content_type == filters['content_type'])
                if filters.get('is_active') is not None:
                    q = q.filter(SourceModel.is_active == filters['is_active'])
                if filters.get('is_built_in') is not None:
                    q = q.filter(SourceModel.is_built_in == filters['is_built_in'])
            
            models = q.order_by(desc(SourceModel.created_at)).all()
            return [self._source_model_to_config(model) for model in models]
        finally:
            session.close()
    
    # 抓取结果相关方法
    async def save_crawl_result(self, result: CrawlResult) -> str:
        """保存抓取结果"""
        session = self.db_manager.get_sync_session()
        try:
            result_model = CrawlResultModel(
                source_id=result.source_id,
                url=result.url,
                success=result.success,
                timestamp=result.timestamp,
                title=result.title,
                content=result.content,
                summary=result.summary,
                author=result.author,
                publish_date=result.publish_date,
                tags=result.tags,
                images=result.images,
                error_type=result.error_type,
                error_message=result.error_message,
                http_status=result.http_status,
                response_time=result.response_time,
                content_length=result.content_length,
                content_quality=result.content_quality,
                extraction_confidence=result.extraction_confidence
            )
            
            session.add(result_model)
            
            # 更新信源统计
            source_model = session.query(SourceModel).filter(SourceModel.id == result.source_id).first()
            if source_model:
                source_model.crawl_count += 1
                source_model.last_crawled = result.timestamp
                
                if result.success:
                    source_model.success_count += 1
                else:
                    source_model.error_count += 1
            
            session.commit()
            return result_model.id
        finally:
            session.close()
    
    async def get_crawl_results(self, source_id: str, limit: int = 10) -> List[CrawlResult]:
        """获取抓取结果"""
        session = self.db_manager.get_sync_session()
        try:
            models = session.query(CrawlResultModel).filter(
                CrawlResultModel.source_id == source_id
            ).order_by(desc(CrawlResultModel.timestamp)).limit(limit).all()
            
            results = []
            for model in models:
                result = CrawlResult(
                    source_id=model.source_id,
                    url=model.url,
                    success=model.success,
                    timestamp=model.timestamp,
                    title=model.title,
                    content=model.content,
                    summary=model.summary,
                    author=model.author,
                    publish_date=model.publish_date,
                    tags=model.tags or [],
                    images=model.images or [],
                    error_type=model.error_type,
                    error_message=model.error_message,
                    http_status=model.http_status,
                    response_time=model.response_time,
                    content_length=model.content_length,
                    content_quality=model.content_quality,
                    extraction_confidence=model.extraction_confidence
                )
                results.append(result)
            
            return results
        finally:
            session.close()