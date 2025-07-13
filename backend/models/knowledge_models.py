"""
知识认知和来源追踪数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class KnowledgeType(str, Enum):
    """知识类型"""
    FACT = "fact"                    # 事实
    OPINION = "opinion"              # 观点
    DEFINITION = "definition"        # 定义
    STATISTIC = "statistic"          # 统计数据
    QUOTE = "quote"                  # 引用
    PREDICTION = "prediction"        # 预测
    RESEARCH_FINDING = "research_finding"  # 研究发现
    TREND = "trend"                  # 趋势
    COMPARISON = "comparison"        # 比较
    EXPLANATION = "explanation"      # 解释

class ConfidenceLevel(str, Enum):
    """置信度级别"""
    HIGH = "high"        # 高置信度 (0.8-1.0)
    MEDIUM = "medium"    # 中等置信度 (0.5-0.8)
    LOW = "low"          # 低置信度 (0.0-0.5)

class SourceReference(BaseModel):
    """来源引用信息"""
    source_id: str = Field(..., description="源文档ID")
    source_url: str = Field(..., description="源文档URL")
    source_title: str = Field(..., description="源文档标题")
    
    # 段落级别引用
    paragraph_index: int = Field(..., description="段落索引（从0开始）")
    paragraph_text: str = Field(..., description="完整段落文本")
    
    # 句子级别引用
    sentence_index: int = Field(..., description="句子索引（段落内从0开始）")
    sentence_text: str = Field(..., description="具体句子文本")
    
    # 字符级别位置（可选，用于精确定位）
    char_start: Optional[int] = Field(None, description="字符开始位置")
    char_end: Optional[int] = Field(None, description="字符结束位置")
    
    # 上下文信息
    context_before: Optional[str] = Field(None, description="前文上下文")
    context_after: Optional[str] = Field(None, description="后文上下文")
    
    # 元数据
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="提取时间")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性分数")

class KnowledgeClaim(BaseModel):
    """一句话知识认知"""
    
    # 核心知识内容
    claim_text: str = Field(..., description="核心知识声明（一句话）")
    knowledge_type: KnowledgeType = Field(..., description="知识类型")
    
    # 置信度和质量
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI提取置信度")
    confidence_level: ConfidenceLevel = Field(..., description="置信度级别")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="内容质量分数")
    
    # 主题和分类
    topic: str = Field(..., description="主题")
    keywords: List[str] = Field(default=[], description="关键词")
    entities: List[str] = Field(default=[], description="命名实体")
    
    # 来源引用（支持多个来源）
    source_references: List[SourceReference] = Field(..., description="来源引用列表")
    
    # 语义信息
    semantic_embedding: Optional[List[float]] = Field(None, description="语义向量（用于相似性搜索）")
    
    # 事实验证
    fact_check_status: Optional[str] = Field(None, description="事实检查状态")
    verification_sources: List[str] = Field(default=[], description="验证来源")
    
    # 时间信息
    temporal_info: Optional[Dict[str, Any]] = Field(None, description="时间相关信息")
    
    # 处理元数据
    extraction_method: str = Field(default="ai_analysis", description="提取方法")
    processor_version: str = Field(default="1.0", description="处理器版本")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class EnhancedSentence(BaseModel):
    """增强的句子分析"""
    
    # 基本信息
    sentence_text: str = Field(..., description="句子文本")
    sentence_index: int = Field(..., description="句子在段落中的索引")
    paragraph_index: int = Field(..., description="段落索引")
    
    # 位置信息
    char_start: int = Field(..., description="字符开始位置")
    char_end: int = Field(..., description="字符结束位置")
    
    # 语言分析
    language: str = Field(default="zh", description="语言")
    word_count: int = Field(..., description="词数")
    
    # 内容分析
    importance_score: float = Field(..., ge=0.0, le=1.0, description="重要性分数")
    informativeness: float = Field(..., ge=0.0, le=1.0, description="信息量")
    novelty_score: float = Field(..., ge=0.0, le=1.0, description="新颖性分数")
    
    # 知识提取
    knowledge_claims: List[KnowledgeClaim] = Field(default=[], description="提取的知识声明")
    
    # 语义信息
    semantic_embedding: Optional[List[float]] = Field(None, description="语义向量")
    named_entities: List[Dict[str, Any]] = Field(default=[], description="命名实体")
    
    # 语法分析
    pos_tags: List[Dict[str, str]] = Field(default=[], description="词性标注")
    dependencies: List[Dict[str, Any]] = Field(default=[], description="依存关系")

class EnhancedParagraph(BaseModel):
    """增强的段落分析"""
    
    # 基本信息
    paragraph_text: str = Field(..., description="段落文本")
    paragraph_index: int = Field(..., description="段落索引")
    
    # 句子分解
    sentences: List[EnhancedSentence] = Field(..., description="句子列表")
    
    # 段落级别分析
    main_topic: str = Field(..., description="主要主题")
    key_points: List[str] = Field(default=[], description="关键要点")
    summary: str = Field(..., description="段落摘要")
    
    # 质量评估
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="连贯性分数")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性分数")
    
    # 知识密度
    knowledge_density: float = Field(..., ge=0.0, le=1.0, description="知识密度")
    fact_count: int = Field(default=0, description="事实数量")

class SourceDocumentAnalysis(BaseModel):
    """源文档完整分析"""
    
    # 文档基本信息
    document_id: str = Field(..., description="文档ID")
    source_url: str = Field(..., description="源URL")
    title: str = Field(..., description="文档标题")
    author: Optional[str] = Field(None, description="作者")
    publish_date: Optional[str] = Field(None, description="发布日期")
    
    # 段落分析
    paragraphs: List[EnhancedParagraph] = Field(..., description="段落分析列表")
    
    # 文档级别知识
    document_claims: List[KnowledgeClaim] = Field(default=[], description="文档级别知识声明")
    
    # 文档摘要
    executive_summary: str = Field(..., description="执行摘要")
    key_insights: List[str] = Field(default=[], description="关键洞察")
    
    # 质量评估
    overall_quality: float = Field(..., ge=0.0, le=1.0, description="整体质量")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="可信度分数")
    
    # 处理信息
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")
    processing_version: str = Field(default="1.0", description="处理版本")

class ArticleWithSources(BaseModel):
    """带来源引用的文章"""
    
    # 基本文章信息
    title: str = Field(..., description="文章标题")
    content: str = Field(..., description="文章内容")
    summary: str = Field(..., description="文章摘要")
    category: str = Field(..., description="文章分类")
    
    # 带引用的内容结构
    structured_content: List[Dict[str, Any]] = Field(..., description="结构化内容，包含段落和引用")
    
    # 来源映射
    source_mapping: Dict[str, SourceReference] = Field(..., description="来源引用映射")
    
    # 知识声明
    knowledge_claims: List[KnowledgeClaim] = Field(..., description="文章中的知识声明")
    
    # 引用统计
    citation_count: int = Field(default=0, description="引用总数")
    unique_sources: int = Field(default=0, description="独特来源数")
    
    # 质量指标
    source_diversity: float = Field(..., ge=0.0, le=1.0, description="来源多样性")
    citation_density: float = Field(..., ge=0.0, le=1.0, description="引用密度")
    
    # 元数据
    generation_model: str = Field(..., description="生成模型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class CitationStyle(str, Enum):
    """引用样式"""
    INLINE = "inline"           # 行内引用 [1]
    FOOTNOTE = "footnote"       # 脚注引用
    PARENTHETICAL = "parenthetical"  # 括号引用 (Source, 2024)
    SUPERSCRIPT = "superscript" # 上标引用¹

class FormattedCitation(BaseModel):
    """格式化的引用"""
    citation_id: str = Field(..., description="引用ID")
    citation_text: str = Field(..., description="引用文本")
    style: CitationStyle = Field(..., description="引用样式")
    source_reference: SourceReference = Field(..., description="来源引用")
    
    # 显示选项
    show_url: bool = Field(default=True, description="是否显示URL")
    show_date: bool = Field(default=True, description="是否显示日期")
    truncate_text: bool = Field(default=True, description="是否截断长文本")