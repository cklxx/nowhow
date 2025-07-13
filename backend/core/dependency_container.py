"""
Dependency injection container for clean architecture.
Manages all dependencies and their lifecycles.
"""

import os
from typing import Optional
from dataclasses import dataclass

from core.clean_architecture import AppConfig, Dependencies
from adapters.repositories import (
    FileBasedSourceRepository, FileBasedArticleRepository, FileBasedWorkflowRepository
)
from adapters.crawler_adapter import ModernCrawlerAdapter
# 避免循环导入，在需要时动态导入
# from use_cases.source_use_cases import SourceUseCasesImpl
# from use_cases.workflow_use_cases import WorkflowUseCasesImpl


class Container:
    """Dependency injection container"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or self._create_default_config()
        self._repositories = None
        self._services = None
        self._use_cases = None
    
    def _create_default_config(self) -> AppConfig:
        """Create default configuration from environment"""
        return AppConfig(
            api_key_ark=os.getenv('ARK_API_KEY', ''),
            api_key_firecrawl=os.getenv('FIRECRAWL_API_KEY', ''),
            database_url=os.getenv('DATABASE_URL', 'sqlite:///./app.db'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            cors_origins=['http://localhost:3000']
        )
    
    @property
    def repositories(self):
        """Get repositories (lazy initialization)"""
        if self._repositories is None:
            self._repositories = RepositoryContainer()
        return self._repositories
    
    @property
    def services(self):
        """Get services (lazy initialization)"""
        if self._services is None:
            self._services = ServiceContainer(self.config)
        return self._services
    
    @property
    def use_cases(self):
        """Get use cases (lazy initialization)"""
        if self._use_cases is None:
            self._use_cases = UseCaseContainer(
                self.repositories, 
                self.services
            )
        return self._use_cases


class RepositoryContainer:
    """Container for repositories"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._source_repository = None
        self._article_repository = None
        self._workflow_repository = None
    
    @property
    def source_repository(self):
        if self._source_repository is None:
            self._source_repository = FileBasedSourceRepository(self.data_dir)
        return self._source_repository
    
    @property
    def article_repository(self):
        if self._article_repository is None:
            self._article_repository = FileBasedArticleRepository(self.data_dir)
        return self._article_repository
    
    @property
    def workflow_repository(self):
        if self._workflow_repository is None:
            self._workflow_repository = FileBasedWorkflowRepository(self.data_dir)
        return self._workflow_repository


class ServiceContainer:
    """Container for services"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._crawler_service = None
        self._content_processor = None
        self._article_generator = None
    
    @property
    def crawler_service(self):
        if self._crawler_service is None:
            self._crawler_service = ModernCrawlerAdapter(
                firecrawl_api_key=self.config.api_key_firecrawl
            )
        return self._crawler_service
    
    @property
    def content_processor(self):
        # Optional - implement if needed
        return self._content_processor
    
    @property
    def article_generator(self):
        # Optional - implement if needed
        return self._article_generator


class UseCaseContainer:
    """Container for use cases"""
    
    def __init__(self, repositories: RepositoryContainer, services: ServiceContainer):
        self.repositories = repositories
        self.services = services
        self._source_use_cases = None
        self._workflow_use_cases = None
    
    @property
    def source_use_cases(self):
        if self._source_use_cases is None:
            from use_cases.source_use_cases import SourceUseCasesImpl
            self._source_use_cases = SourceUseCasesImpl(
                self.repositories.source_repository
            )
        return self._source_use_cases
    
    @property
    def workflow_use_cases(self):
        if self._workflow_use_cases is None:
            from use_cases.workflow_use_cases import WorkflowUseCasesImpl
            self._workflow_use_cases = WorkflowUseCasesImpl(
                workflow_repository=self.repositories.workflow_repository,
                source_repository=self.repositories.source_repository,
                article_repository=self.repositories.article_repository,
                crawler_service=self.services.crawler_service,
                content_processor=self.services.content_processor,
                article_generator=self.services.article_generator
            )
        return self._workflow_use_cases


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get global container instance"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container():
    """Reset container (useful for testing)"""
    global _container
    _container = None