"""
Clean Architecture implementation for AI content aggregator.
Following Uncle Bob's Clean Architecture principles with high cohesion and low coupling.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# === ENTITIES (Core Business Logic) ===

class SourceType(Enum):
    RSS = "rss"
    HTML = "html"
    API = "api"
    WEBSITE = "website"

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Source:
    """Core source entity"""
    id: str
    name: str
    url: str
    type: SourceType
    category: str = "general"
    active: bool = True
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Article:
    """Core article entity"""
    id: str
    title: str
    content: str
    url: str
    source_id: str
    category: str = "general"
    author: str = ""
    published_at: datetime = None
    created_at: datetime = None
    quality_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class WorkflowRun:
    """Core workflow entity"""
    id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = None
    results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.results is None:
            self.results = {}


# === USE CASES (Application Business Rules) ===

class SourceUseCases(ABC):
    """Source management use cases"""
    
    @abstractmethod
    async def create_source(self, source_data: Dict[str, Any]) -> Source:
        pass
    
    @abstractmethod
    async def get_source(self, source_id: str) -> Optional[Source]:
        pass
    
    @abstractmethod
    async def list_sources(self, active_only: bool = True) -> List[Source]:
        pass
    
    @abstractmethod
    async def update_source(self, source_id: str, updates: Dict[str, Any]) -> Source:
        pass
    
    @abstractmethod
    async def delete_source(self, source_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_sources_by_category(self, category: str) -> List[Source]:
        pass

class CrawlerUseCases(ABC):
    """Crawler use cases"""
    
    @abstractmethod
    async def crawl_sources(self, source_ids: List[str] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def validate_source(self, source: Source) -> bool:
        pass

class WorkflowUseCases(ABC):
    """Workflow management use cases"""
    
    @abstractmethod
    async def start_workflow(self, config: Dict[str, Any]) -> WorkflowRun:
        pass
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowRun]:
        pass
    
    @abstractmethod
    async def list_workflows(self, limit: int = 10) -> List[WorkflowRun]:
        pass
    
    @abstractmethod
    async def cancel_workflow(self, workflow_id: str) -> bool:
        pass

class ArticleUseCases(ABC):
    """Article management use cases"""
    
    @abstractmethod
    async def get_articles(self, 
                          workflow_id: str = None, 
                          category: str = None, 
                          limit: int = 20) -> List[Article]:
        pass
    
    @abstractmethod
    async def get_article_statistics(self) -> Dict[str, Any]:
        pass


# === INTERFACE ADAPTERS (Frameworks & Drivers) ===

class SourceRepository(Protocol):
    """Source repository interface"""
    
    async def save(self, source: Source) -> Source:
        ...
    
    async def find_by_id(self, source_id: str) -> Optional[Source]:
        ...
    
    async def find_all(self, active_only: bool = True) -> List[Source]:
        ...
    
    async def find_by_category(self, category: str) -> List[Source]:
        ...
    
    async def update(self, source: Source) -> Source:
        ...
    
    async def delete(self, source_id: str) -> bool:
        ...

class ArticleRepository(Protocol):
    """Article repository interface"""
    
    async def save(self, article: Article) -> Article:
        ...
    
    async def find_by_workflow(self, workflow_id: str) -> List[Article]:
        ...
    
    async def find_by_category(self, category: str) -> List[Article]:
        ...
    
    async def find_recent(self, limit: int = 20) -> List[Article]:
        ...

class WorkflowRepository(Protocol):
    """Workflow repository interface"""
    
    async def save(self, workflow: WorkflowRun) -> WorkflowRun:
        ...
    
    async def find_by_id(self, workflow_id: str) -> Optional[WorkflowRun]:
        ...
    
    async def find_recent(self, limit: int = 10) -> List[WorkflowRun]:
        ...
    
    async def update_status(self, workflow_id: str, status: WorkflowStatus, 
                           error_message: str = None) -> bool:
        ...

class CrawlerService(Protocol):
    """Crawler service interface"""
    
    async def crawl_source(self, source: Source) -> Dict[str, Any]:
        ...
    
    async def validate_source_url(self, url: str) -> bool:
        ...

class ContentProcessor(Protocol):
    """Content processing interface"""
    
    async def process_content(self, raw_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...

class ArticleGenerator(Protocol):
    """Article generation interface"""
    
    async def generate_articles(self, processed_content: List[Dict[str, Any]]) -> List[Article]:
        ...


# === DEPENDENCY INJECTION ===

@dataclass
class Dependencies:
    """Dependency container following IoC principle"""
    source_repository: SourceRepository
    article_repository: ArticleRepository
    workflow_repository: WorkflowRepository
    crawler_service: CrawlerService
    content_processor: ContentProcessor
    article_generator: ArticleGenerator


# === CONFIGURATION ===

@dataclass
class AppConfig:
    """Application configuration"""
    api_key_ark: str = ""
    api_key_firecrawl: str = ""
    database_url: str = "sqlite:///./app.db"
    log_level: str = "INFO"
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]


# === COMMON TYPES ===

class Result:
    """Result type for error handling"""
    
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def ok(cls, data: Any = None):
        return cls(True, data)
    
    @classmethod
    def error(cls, error: str):
        return cls(False, None, error)
    
    def is_success(self) -> bool:
        return self.success
    
    def is_error(self) -> bool:
        return not self.success