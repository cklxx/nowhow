from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class SourceType(str, Enum):
    """信源类型"""
    RSS = "rss"
    WEBSITE = "website"
    API = "api"

class ContentType(str, Enum):
    """内容类型"""
    ARTICLE = "article"
    BLOG = "blog"
    NEWS = "news"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"

class AuthType(str, Enum):
    """认证类型"""
    NONE = "none"
    COOKIE = "cookie"
    HEADER = "header"
    TOKEN = "token"
    BASIC_AUTH = "basic_auth"

class ContentSelector(BaseModel):
    """内容选择器配置"""
    title: Optional[str] = None              # 标题选择器
    content: Optional[str] = None            # 正文选择器
    summary: Optional[str] = None            # 摘要选择器
    author: Optional[str] = None             # 作者选择器
    publish_date: Optional[str] = None       # 发布日期选择器
    tags: Optional[str] = None               # 标签选择器
    category: Optional[str] = None           # 分类选择器
    image: Optional[str] = None              # 图片选择器
    link: Optional[str] = None               # 链接选择器
    
    # 排除选择器（要删除的元素）
    exclude_selectors: List[str] = []
    
    # 自定义提取规则
    custom_rules: Dict[str, str] = {}

class AuthConfig(BaseModel):
    """认证配置"""
    type: AuthType = AuthType.NONE
    cookies: Dict[str, str] = {}             # Cookie键值对
    headers: Dict[str, str] = {}             # 请求头键值对
    username: Optional[str] = None           # 用户名（基础认证）
    password: Optional[str] = None           # 密码（基础认证）
    token: Optional[str] = None              # Token
    token_header: str = "Authorization"      # Token请求头名称
    
    # Mock数据来源信息
    mock_source: Optional[str] = None        # Mock数据来源URL或描述
    last_verified: Optional[datetime] = None # 最后验证时间
    is_verified: bool = False                # 是否已验证有效

class CrawlConfig(BaseModel):
    """抓取配置"""
    # 请求配置
    timeout: int = 30                        # 超时时间（秒）
    retry_count: int = 3                     # 重试次数
    delay: float = 1.0                       # 请求间隔（秒）
    
    # User-Agent配置
    user_agent: Optional[str] = None
    random_user_agent: bool = True           # 是否使用随机User-Agent
    
    # 代理配置
    proxy: Optional[str] = None
    
    # 渲染配置
    render_js: bool = False                  # 是否渲染JavaScript
    wait_for_selector: Optional[str] = None  # 等待特定元素加载
    
    # 内容过滤
    min_content_length: int = 100            # 最小内容长度
    max_content_length: int = 50000          # 最大内容长度
    
    # 编码设置
    encoding: Optional[str] = None

class SourceConfig(BaseModel):
    """信源配置模型"""
    # 基本信息
    id: Optional[str] = None                 # 配置ID
    name: str                                # 信源名称
    url: HttpUrl                             # 信源URL
    type: SourceType                         # 信源类型
    content_type: ContentType                # 内容类型
    description: Optional[str] = None        # 描述
    
    # 抓取配置
    crawl_config: CrawlConfig = CrawlConfig()
    auth_config: AuthConfig = AuthConfig()
    content_selectors: ContentSelector = ContentSelector()
    
    # AI分析结果
    ai_analyzed: bool = False                # 是否已AI分析
    ai_analysis_time: Optional[datetime] = None
    ai_confidence: Optional[float] = None    # AI分析置信度
    ai_suggestions: List[str] = []           # AI建议
    
    # 使用统计
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    last_crawled: Optional[datetime] = None
    crawl_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    # 用户配置
    is_active: bool = True                   # 是否启用
    is_built_in: bool = False                # 是否内置信源
    created_by: str = "user"                 # 创建者
    
    # 质量评估
    quality_score: Optional[float] = None    # 内容质量分数
    relevance_score: Optional[float] = None  # 相关性分数
    
    class Config:
        use_enum_values = True

class CrawlResult(BaseModel):
    """抓取结果模型"""
    source_id: str
    url: str
    success: bool
    timestamp: datetime = datetime.now()
    
    # 成功结果
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: List[str] = []
    images: List[str] = []
    
    # 错误信息
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    http_status: Optional[int] = None
    
    # 性能指标
    response_time: Optional[float] = None    # 响应时间（秒）
    content_length: Optional[int] = None     # 内容长度
    
    # 质量评估
    content_quality: Optional[float] = None  # 内容质量分数
    extraction_confidence: Optional[float] = None  # 提取置信度

class AIAnalysisRequest(BaseModel):
    """AI分析请求模型"""
    url: HttpUrl
    html_sample: Optional[str] = None        # HTML样本（可选）
    content_type: ContentType
    existing_selectors: Optional[ContentSelector] = None

class AIAnalysisResult(BaseModel):
    """AI分析结果模型"""
    url: str
    confidence: float                        # 置信度 0-1
    suggested_selectors: ContentSelector
    page_structure: Dict[str, Any]           # 页面结构分析
    content_patterns: List[str]              # 内容模式
    recommendations: List[str]               # 建议
    potential_issues: List[str]              # 潜在问题
    requires_auth: bool                      # 是否需要认证
    requires_js: bool                        # 是否需要JavaScript渲染
    estimated_quality: float                 # 估计内容质量
    
class MockAuthRequest(BaseModel):
    """Mock认证查找请求"""
    url: HttpUrl
    site_domain: str
    auth_type: AuthType = AuthType.COOKIE

class MockAuthResult(BaseModel):
    """Mock认证结果"""
    found: bool
    auth_config: Optional[AuthConfig] = None
    sources: List[str] = []                  # 数据来源
    confidence: float                        # 可信度
    last_updated: Optional[datetime] = None
    usage_notes: Optional[str] = None        # 使用说明