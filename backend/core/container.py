"""
Dependency injection container for managing application dependencies.
"""

from functools import lru_cache
from typing import Dict, Any, TypeVar, Type, Optional

from config.settings import Settings, get_settings
from core.interfaces import (
    IModelService,
    IStorageService,
    ISourceRepository,
    ICrawlerService,
    IContentProcessor,
    IArticleWriter,
    IWorkflowOrchestrator,
    IAuthService
)

T = TypeVar('T')


class Container:
    """Dependency injection container."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        
    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True):
        """Register a service implementation."""
        self._services[interface] = implementation
        if singleton:
            self._singletons[interface] = None
    
    def register_instance(self, interface: Type[T], instance: T):
        """Register a service instance."""
        self._services[interface] = instance
        self._singletons[interface] = instance
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance."""
        if interface not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered")
        
        # Check if it's a singleton and already instantiated
        if interface in self._singletons and self._singletons[interface] is not None:
            return self._singletons[interface]
        
        # Get the implementation
        implementation = self._services[interface]
        
        # If it's already an instance, return it
        if not isinstance(implementation, type):
            return implementation
        
        # Create new instance
        instance = self._create_instance(implementation)
        
        # Store singleton if needed
        if interface in self._singletons:
            self._singletons[interface] = instance
        
        return instance
    
    def _create_instance(self, implementation_class: Type[T]) -> T:
        """Create instance with dependency injection."""
        # Import here to avoid circular imports
        from agents.research_agent import ResearchAgent
        
        # Special handling for complex dependencies
        if implementation_class.__name__ == "LangGraphOrchestrator":
            return implementation_class(
                self.settings,
                self.get(ICrawlerService),
                self.get(IContentProcessor), 
                self.get(IArticleWriter),
                self.get(IStorageService),
                self.get(ISourceRepository),
                self.get(ResearchAgent)
            )
        elif implementation_class.__name__ in ["JsonSourceRepository", "DatabaseSourceRepository"]:
            return implementation_class()
        elif implementation_class.__name__ == "WebCrawlerService":
            return implementation_class(self.settings, self.get(IAuthService))
        elif implementation_class.__name__ in ["AIContentProcessor", "AIArticleWriter", "EnhancedContentProcessor", "EnhancedArticleWriter"]:
            return implementation_class(self.get(IModelService))
        
        # Default constructor patterns
        try:
            # Try to create with settings and container
            return implementation_class(self.settings, self)
        except TypeError:
            try:
                # Try to create with just settings
                return implementation_class(self.settings)
            except TypeError:
                # Try to create without parameters
                return implementation_class()
    
    @property
    def model_service(self) -> IModelService:
        """Get model service."""
        return self.get(IModelService)
    
    @property
    def storage_service(self) -> IStorageService:
        """Get storage service."""
        return self.get(IStorageService)
    
    @property
    def source_repository(self) -> ISourceRepository:
        """Get source repository."""
        return self.get(ISourceRepository)
    
    @property
    def crawler_service(self) -> ICrawlerService:
        """Get crawler service."""
        return self.get(ICrawlerService)
    
    @property
    def content_processor(self) -> IContentProcessor:
        """Get content processor."""
        return self.get(IContentProcessor)
    
    @property
    def article_writer(self) -> IArticleWriter:
        """Get article writer."""
        return self.get(IArticleWriter)
    
    @property
    def workflow_orchestrator(self) -> IWorkflowOrchestrator:
        """Get workflow orchestrator."""
        return self.get(IWorkflowOrchestrator)
    
    @property
    def auth_service(self) -> IAuthService:
        """Get auth service."""
        return self.get(IAuthService)


def create_container(settings: Optional[Settings] = None) -> Container:
    """Create and configure dependency injection container."""
    if settings is None:
        settings = get_settings()
    
    container = Container(settings)
    
    # Import implementations here to avoid circular imports
    from services.model_service import ARKModelService
    from services.db_storage_service import DatabaseStorageService
    from repositories.db_source_repository import DatabaseSourceRepository
    from services.crawler_service import WebCrawlerService
    from services.enhanced_content_processor import EnhancedContentProcessor
    from services.enhanced_article_writer import EnhancedArticleWriter
    from services.workflow_orchestrator import LangGraphOrchestrator
    from services.auth_service import MockAuthService
    from agents.research_agent import ResearchAgent
    
    # Initialize database
    from database.connection import init_database
    init_database()
    
    # Register core services first
    container.register(IModelService, ARKModelService, singleton=True)
    container.register(IStorageService, DatabaseStorageService, singleton=True)
    container.register(IAuthService, MockAuthService, singleton=True)
    
    # Register repository (using new database repository)
    container.register(ISourceRepository, DatabaseSourceRepository, singleton=True)
    
    # Register business services
    container.register(ICrawlerService, WebCrawlerService, singleton=True)
    container.register(IContentProcessor, EnhancedContentProcessor, singleton=True)
    container.register(IArticleWriter, EnhancedArticleWriter, singleton=True)
    
    # Create research agent instance manually due to complex dependencies
    model_service = container.get(IModelService)
    research_agent = ResearchAgent(settings, model_service)
    container.register_instance(ResearchAgent, research_agent)
    
    # Register workflow orchestrator (depends on all other services)
    container.register(IWorkflowOrchestrator, LangGraphOrchestrator, singleton=True)
    
    return container


@lru_cache()
def get_container() -> Container:
    """Get cached container instance."""
    return create_container()