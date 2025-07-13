"""
Interface definitions for dependency injection and clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel


class IModelService(ABC):
    """Interface for AI model services."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using the model."""
        pass
    
    @abstractmethod
    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using the model."""
        pass
    
    @abstractmethod
    async def score_relevance(
        self,
        content: str,
        criteria: str,
        **kwargs
    ) -> float:
        """Score content relevance."""
        pass


class IStorageService(ABC):
    """Interface for file storage operations."""
    
    @abstractmethod
    async def save_json(
        self,
        data: Union[Dict, List],
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save data as JSON file."""
        pass
    
    @abstractmethod
    async def load_json(self, filepath: Union[str, Path]) -> Union[Dict, List]:
        """Load data from JSON file."""
        pass
    
    @abstractmethod
    async def save_text(
        self,
        content: str,
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save content as text file."""
        pass
    
    @abstractmethod
    async def load_text(self, filepath: Union[str, Path]) -> str:
        """Load content from text file."""
        pass
    
    @abstractmethod
    def get_file_path(
        self,
        pattern: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Get file path based on pattern."""
        pass
    
    # Enhanced storage methods
    async def load_and_merge_files(
        self,
        pattern: str,
        content_type: str,
        limit: Optional[int] = None,
        sort_by: str = "timestamp",
        merge_strategy: str = "auto"
    ) -> Dict[str, Any]:
        """Load and automatically merge multiple files matching a pattern."""
        pass
    
    async def load_latest_by_type(
        self,
        content_type: str,
        workflow_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Load latest files of a specific type with automatic merging."""
        pass
    
    async def load_workflow_history(
        self,
        workflow_id: str,
        include_steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Load complete history for a specific workflow."""
        pass


class ISourceRepository(ABC):
    """Interface for source management operations."""
    
    @abstractmethod
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all sources."""
        pass
    
    @abstractmethod
    async def get_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source by ID."""
        pass
    
    @abstractmethod
    async def create(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new source."""
        pass
    
    @abstractmethod
    async def update(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing source."""
        pass
    
    @abstractmethod
    async def delete(self, source_id: str) -> bool:
        """Delete source."""
        pass
    
    @abstractmethod
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get sources by category."""
        pass


class ICrawlerService(ABC):
    """Interface for content crawling operations."""
    
    @abstractmethod
    async def crawl_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a single source."""
        pass
    
    @abstractmethod
    async def crawl_multiple(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crawl multiple sources concurrently."""
        pass
    
    @abstractmethod
    async def validate_source(self, source_config: Dict[str, Any]) -> bool:
        """Validate if a source is accessible."""
        pass


class IContentProcessor(ABC):
    """Interface for content processing operations."""
    
    @abstractmethod
    async def process_content(
        self,
        content: Dict[str, Any],
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a single piece of content."""
        pass
    
    @abstractmethod
    async def process_batch(
        self,
        content_list: List[Dict[str, Any]],
        processing_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple pieces of content."""
        pass
    
    @abstractmethod
    async def filter_by_relevance(
        self,
        content_list: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Filter content by relevance score."""
        pass


class IArticleWriter(ABC):
    """Interface for article writing operations."""
    
    @abstractmethod
    async def generate_article(
        self,
        content_group: List[Dict[str, Any]],
        category: str,
        style_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate an article from content group."""
        pass
    
    @abstractmethod
    async def group_content_by_category(
        self,
        content_list: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group content by category."""
        pass


class IWorkflowOrchestrator(ABC):
    """Interface for workflow orchestration."""
    
    @abstractmethod
    async def run_workflow(
        self,
        workflow_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run complete content generation workflow."""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        pass
    
    @abstractmethod
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow."""
        pass


class IAuthService(ABC):
    """Interface for authentication operations."""
    
    @abstractmethod
    async def find_auth_for_source(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Find authentication configuration for source."""
        pass
    
    @abstractmethod
    async def validate_auth(self, auth_config: Dict[str, Any]) -> bool:
        """Validate authentication configuration."""
        pass