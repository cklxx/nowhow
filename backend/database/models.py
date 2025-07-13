"""SQLite database models using SQLAlchemy."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class SourceModel(Base):
    """信源配置数据库模型"""
    __tablename__ = 'sources'
    
    # 主键和基本信息
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    name = Column(String(200), nullable=False, index=True)
    url = Column(Text, nullable=False)
    type = Column(String(20), nullable=False, index=True)  # rss, website, api
    content_type = Column(String(20), nullable=False, index=True)  # article, blog, news, research, documentation
    description = Column(Text)
    
    # 抓取配置 (JSON 存储)
    crawl_config = Column(JSON, default={})
    auth_config = Column(JSON, default={})
    content_selectors = Column(JSON, default={})
    
    # AI分析结果
    ai_analyzed = Column(Boolean, default=False)
    ai_analysis_time = Column(DateTime)
    ai_confidence = Column(Float)
    ai_suggestions = Column(JSON, default=[])
    
    # 使用统计
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_crawled = Column(DateTime, index=True)
    crawl_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # 用户配置
    is_active = Column(Boolean, default=True, index=True)
    is_built_in = Column(Boolean, default=False, index=True)
    created_by = Column(String(100), default="user")
    
    # 质量评估
    quality_score = Column(Float)
    relevance_score = Column(Float)
    
    # 关联关系
    crawl_results = relationship("CrawlResultModel", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SourceModel(id='{self.id}', name='{self.name}', type='{self.type}')>"

class CrawlResultModel(Base):
    """抓取结果数据库模型"""
    __tablename__ = 'crawl_results'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(50), ForeignKey('sources.id'), nullable=False, index=True)
    url = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # 成功结果
    title = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    author = Column(String(200))
    publish_date = Column(String(100))  # 存储原始日期字符串
    tags = Column(JSON, default=[])
    images = Column(JSON, default=[])
    
    # 错误信息
    error_type = Column(String(100))
    error_message = Column(Text)
    http_status = Column(Integer)
    
    # 性能指标
    response_time = Column(Float)  # 响应时间（秒）
    content_length = Column(Integer)  # 内容长度
    
    # 质量评估
    content_quality = Column(Float)  # 内容质量分数
    extraction_confidence = Column(Float)  # 提取置信度
    
    # 关联关系
    source = relationship("SourceModel", back_populates="crawl_results")
    
    def __repr__(self):
        return f"<CrawlResultModel(id='{self.id}', source_id='{self.source_id}', success={self.success})>"

class ArticleModel(Base):
    """生成文章数据库模型"""
    __tablename__ = 'articles'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(50), nullable=False, index=True)
    
    # 文章基本信息
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    category = Column(String(100), index=True)
    tags = Column(JSON, default=[])
    
    # 元数据
    word_count = Column(Integer)
    reading_time = Column(Integer)  # 预估阅读时间（分钟）
    language = Column(String(10), default="zh")
    
    # 质量和相关性
    quality_score = Column(Float)
    relevance_score = Column(Float)
    ai_confidence = Column(Float)
    
    # 来源信息
    source_articles = Column(JSON, default=[])  # 源文章ID列表
    research_topics = Column(JSON, default=[])
    generation_model = Column(String(100))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 状态
    status = Column(String(20), default="published", index=True)  # draft, published, archived
    
    def __repr__(self):
        return f"<ArticleModel(id='{self.id}', title='{self.title[:50]}...', workflow_id='{self.workflow_id}')>"

class WorkflowModel(Base):
    """工作流状态数据库模型"""
    __tablename__ = 'workflows'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 工作流配置
    name = Column(String(200))
    description = Column(Text)
    config = Column(JSON, default={})  # 工作流配置
    
    # 状态和进度
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 进度百分比 0-100
    current_step = Column(String(100))
    
    # 统计信息
    sources_count = Column(Integer, default=0)
    crawled_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    articles_generated = Column(Integer, default=0)
    
    # 结果存储
    results = Column(JSON, default={})
    error_log = Column(JSON, default=[])
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 性能指标
    execution_time = Column(Float)  # 执行时间（秒）
    
    def __repr__(self):
        return f"<WorkflowModel(id='{self.id}', status='{self.status}', progress={self.progress})>"

class ProcessedContentModel(Base):
    """处理后内容数据库模型"""
    __tablename__ = 'processed_content'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(50), nullable=False, index=True)
    crawl_result_id = Column(String(50), ForeignKey('crawl_results.id'), index=True)
    
    # 处理后的内容
    title = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    keywords = Column(JSON, default=[])
    category = Column(String(100), index=True)
    
    # AI分析结果
    relevance_score = Column(Float, index=True)
    quality_score = Column(Float)
    ai_analysis = Column(JSON, default={})
    
    # 处理状态
    processed_at = Column(DateTime, default=datetime.now, index=True)
    processing_model = Column(String(100))
    processing_time = Column(Float)  # 处理时间（秒）
    
    # 内容特征
    word_count = Column(Integer)
    language = Column(String(10))
    sentiment = Column(String(20))  # positive, negative, neutral
    
    def __repr__(self):
        return f"<ProcessedContentModel(id='{self.id}', workflow_id='{self.workflow_id}', relevance_score={self.relevance_score})>"

class KnowledgeClaimModel(Base):
    """知识声明数据库模型"""
    __tablename__ = 'knowledge_claims'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 核心知识内容
    claim_text = Column(Text, nullable=False, index=True)
    knowledge_type = Column(String(20), nullable=False, index=True)  # fact, opinion, definition, etc.
    
    # 置信度和质量
    confidence_score = Column(Float, nullable=False, index=True)
    confidence_level = Column(String(10), nullable=False)  # high, medium, low
    quality_score = Column(Float, nullable=False, index=True)
    
    # 主题和分类
    topic = Column(String(200), index=True)
    keywords = Column(JSON, default=[])
    entities = Column(JSON, default=[])
    
    # 语义信息
    semantic_embedding = Column(JSON)  # 存储向量嵌入
    
    # 事实验证
    fact_check_status = Column(String(20))  # verified, unverified, disputed, unknown
    verification_sources = Column(JSON, default=[])
    
    # 时间信息
    temporal_info = Column(JSON)
    
    # 处理元数据
    extraction_method = Column(String(50), default="ai_analysis")
    processor_version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # 关联关系
    source_references = relationship("SourceReferenceModel", back_populates="knowledge_claim", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeClaimModel(id='{self.id}', claim_text='{self.claim_text[:50]}...', type='{self.knowledge_type}')>"

class SourceReferenceModel(Base):
    """来源引用数据库模型"""
    __tablename__ = 'source_references'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_claim_id = Column(String(50), ForeignKey('knowledge_claims.id'), nullable=False, index=True)
    
    # 来源信息
    source_id = Column(String(50), index=True)
    source_url = Column(Text, nullable=False)
    source_title = Column(Text, nullable=False)
    
    # 段落级别引用
    paragraph_index = Column(Integer, nullable=False, index=True)
    paragraph_text = Column(Text)
    
    # 句子级别引用
    sentence_index = Column(Integer, nullable=False, index=True)
    sentence_text = Column(Text, nullable=False)
    
    # 字符级别位置
    char_start = Column(Integer)
    char_end = Column(Integer)
    
    # 上下文信息
    context_before = Column(Text)
    context_after = Column(Text)
    
    # 元数据
    extraction_timestamp = Column(DateTime, default=datetime.now)
    relevance_score = Column(Float, nullable=False, index=True)
    
    # 关联关系
    knowledge_claim = relationship("KnowledgeClaimModel", back_populates="source_references")
    
    def __repr__(self):
        return f"<SourceReferenceModel(id='{self.id}', source_title='{self.source_title[:30]}...', sentence_index={self.sentence_index})>"

class EnhancedArticleModel(Base):
    """增强的文章模型（带来源引用）"""
    __tablename__ = 'enhanced_articles'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(50), nullable=False, index=True)
    
    # 基本文章信息
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    category = Column(String(100), index=True)
    tags = Column(JSON, default=[])
    
    # 结构化内容（包含引用）
    structured_content = Column(JSON, nullable=False)  # 包含段落和引用的结构化内容
    source_mapping = Column(JSON, nullable=False)      # 来源引用映射
    
    # 引用统计
    citation_count = Column(Integer, default=0)
    unique_sources = Column(Integer, default=0)
    
    # 质量指标
    source_diversity = Column(Float, default=0.0)
    citation_density = Column(Float, default=0.0)
    
    # 元数据
    word_count = Column(Integer)
    reading_time = Column(Integer)
    language = Column(String(10), default="zh")
    
    # 质量和相关性
    quality_score = Column(Float)
    relevance_score = Column(Float)
    ai_confidence = Column(Float)
    
    # 生成信息
    generation_model = Column(String(100))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 状态
    status = Column(String(20), default="published", index=True)
    
    def __repr__(self):
        return f"<EnhancedArticleModel(id='{self.id}', title='{self.title[:50]}...', citations={self.citation_count})>"

class DocumentAnalysisModel(Base):
    """文档分析结果数据库模型"""
    __tablename__ = 'document_analyses'
    
    # 主键
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 文档基本信息
    document_id = Column(String(50), nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    author = Column(String(200))
    publish_date = Column(String(100))
    
    # 分析结果
    paragraphs_analysis = Column(JSON, nullable=False)  # 段落分析结果
    sentences_analysis = Column(JSON, nullable=False)   # 句子分析结果
    
    # 文档级别知识
    document_claims_ids = Column(JSON, default=[])  # 关联的知识声明ID列表
    
    # 文档摘要
    executive_summary = Column(Text, nullable=False)
    key_insights = Column(JSON, default=[])
    
    # 质量评估
    overall_quality = Column(Float, nullable=False)
    credibility_score = Column(Float, nullable=False)
    knowledge_density = Column(Float, default=0.0)
    
    # 统计信息
    total_paragraphs = Column(Integer, default=0)
    total_sentences = Column(Integer, default=0)
    total_claims = Column(Integer, default=0)
    
    # 处理信息
    analysis_timestamp = Column(DateTime, default=datetime.now, index=True)
    processing_version = Column(String(20), default="1.0")
    extraction_method = Column(String(50), default="ai_analysis")
    
    def __repr__(self):
        return f"<DocumentAnalysisModel(id='{self.id}', title='{self.title[:50]}...', claims={self.total_claims})>"

# 创建索引以优化查询性能
from sqlalchemy import Index

# 复合索引
Index('idx_sources_type_active', SourceModel.type, SourceModel.is_active)
Index('idx_sources_content_type_active', SourceModel.content_type, SourceModel.is_active)
Index('idx_crawl_results_source_timestamp', CrawlResultModel.source_id, CrawlResultModel.timestamp)
Index('idx_articles_workflow_category', ArticleModel.workflow_id, ArticleModel.category)
Index('idx_articles_created_status', ArticleModel.created_at, ArticleModel.status)
Index('idx_processed_content_workflow_relevance', ProcessedContentModel.workflow_id, ProcessedContentModel.relevance_score)

# 知识声明和来源引用相关索引
Index('idx_knowledge_claims_type_confidence', KnowledgeClaimModel.knowledge_type, KnowledgeClaimModel.confidence_score)
Index('idx_knowledge_claims_topic_quality', KnowledgeClaimModel.topic, KnowledgeClaimModel.quality_score)
Index('idx_knowledge_claims_created', KnowledgeClaimModel.created_at)
Index('idx_source_references_claim_id', SourceReferenceModel.knowledge_claim_id)
Index('idx_source_references_source_para', SourceReferenceModel.source_id, SourceReferenceModel.paragraph_index)
Index('idx_enhanced_articles_workflow_citations', EnhancedArticleModel.workflow_id, EnhancedArticleModel.citation_count)
Index('idx_document_analyses_document_id', DocumentAnalysisModel.document_id)
Index('idx_document_analyses_quality', DocumentAnalysisModel.overall_quality, DocumentAnalysisModel.credibility_score)