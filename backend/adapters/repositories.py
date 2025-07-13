"""
Repository implementations using file-based storage.
Clean architecture: Infrastructure layer that can be easily swapped.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.clean_architecture import (
    Source, Article, WorkflowRun, SourceType, WorkflowStatus,
    SourceRepository, ArticleRepository, WorkflowRepository
)


class FileBasedSourceRepository:
    """File-based source repository implementation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.sources_file = self.data_dir / "sources.json"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        self.data_dir.mkdir(exist_ok=True)
        if not self.sources_file.exists():
            self._save_sources({})
    
    def _load_sources(self) -> Dict[str, Dict[str, Any]]:
        """Load sources from file"""
        try:
            with open(self.sources_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_sources(self, sources: Dict[str, Dict[str, Any]]):
        """Save sources to file"""
        with open(self.sources_file, 'w') as f:
            json.dump(sources, f, indent=2, default=str)
    
    def _source_to_dict(self, source: Source) -> Dict[str, Any]:
        """Convert source entity to dictionary"""
        return {
            'id': source.id,
            'name': source.name,
            'url': source.url,
            'type': source.type.value,
            'category': source.category,
            'active': source.active,
            'created_at': source.created_at.isoformat(),
            'metadata': source.metadata
        }
    
    def _dict_to_source(self, data: Dict[str, Any]) -> Source:
        """Convert dictionary to source entity"""
        return Source(
            id=data['id'],
            name=data['name'],
            url=data['url'],
            type=SourceType(data['type']),
            category=data.get('category', 'general'),
            active=data.get('active', True),
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data.get('metadata', {})
        )
    
    async def save(self, source: Source) -> Source:
        """Save source"""
        sources = self._load_sources()
        sources[source.id] = self._source_to_dict(source)
        self._save_sources(sources)
        return source
    
    async def find_by_id(self, source_id: str) -> Optional[Source]:
        """Find source by ID"""
        sources = self._load_sources()
        source_data = sources.get(source_id)
        if source_data:
            return self._dict_to_source(source_data)
        return None
    
    async def find_all(self, active_only: bool = True) -> List[Source]:
        """Find all sources"""
        sources = self._load_sources()
        result = []
        for source_data in sources.values():
            if not active_only or source_data.get('active', True):
                result.append(self._dict_to_source(source_data))
        return sorted(result, key=lambda s: s.created_at, reverse=True)
    
    async def find_by_category(self, category: str) -> List[Source]:
        """Find sources by category"""
        sources = self._load_sources()
        result = []
        for source_data in sources.values():
            if (source_data.get('category', 'general') == category and 
                source_data.get('active', True)):
                result.append(self._dict_to_source(source_data))
        return sorted(result, key=lambda s: s.created_at, reverse=True)
    
    async def update(self, source: Source) -> Source:
        """Update source"""
        sources = self._load_sources()
        if source.id not in sources:
            raise ValueError(f"Source not found: {source.id}")
        sources[source.id] = self._source_to_dict(source)
        self._save_sources(sources)
        return source
    
    async def delete(self, source_id: str) -> bool:
        """Delete source"""
        sources = self._load_sources()
        if source_id in sources:
            del sources[source_id]
            self._save_sources(sources)
            return True
        return False


class FileBasedArticleRepository:
    """File-based article repository implementation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.articles_dir = self.data_dir / "articles"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directories exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.articles_dir.mkdir(exist_ok=True)
    
    def _article_to_dict(self, article: Article) -> Dict[str, Any]:
        """Convert article entity to dictionary"""
        return {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'url': article.url,
            'source_id': article.source_id,
            'category': article.category,
            'author': article.author,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'created_at': article.created_at.isoformat(),
            'quality_score': article.quality_score,
            'metadata': article.metadata
        }
    
    def _dict_to_article(self, data: Dict[str, Any]) -> Article:
        """Convert dictionary to article entity"""
        return Article(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            url=data['url'],
            source_id=data['source_id'],
            category=data.get('category', 'general'),
            author=data.get('author', ''),
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
            created_at=datetime.fromisoformat(data['created_at']),
            quality_score=data.get('quality_score', 0.0),
            metadata=data.get('metadata', {})
        )
    
    async def save(self, article: Article) -> Article:
        """Save article"""
        file_path = self.articles_dir / f"{article.id}.json"
        with open(file_path, 'w') as f:
            json.dump(self._article_to_dict(article), f, indent=2, default=str)
        return article
    
    async def find_by_workflow(self, workflow_id: str) -> List[Article]:
        """Find articles by workflow ID"""
        articles = []
        for file_path in self.articles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('metadata', {}).get('workflow_id') == workflow_id:
                        articles.append(self._dict_to_article(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(articles, key=lambda a: a.created_at, reverse=True)
    
    async def find_by_category(self, category: str) -> List[Article]:
        """Find articles by category"""
        articles = []
        for file_path in self.articles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('category') == category:
                        articles.append(self._dict_to_article(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(articles, key=lambda a: a.created_at, reverse=True)
    
    async def find_recent(self, limit: int = 20) -> List[Article]:
        """Find recent articles"""
        articles = []
        for file_path in self.articles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    articles.append(self._dict_to_article(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(articles, key=lambda a: a.created_at, reverse=True)[:limit]


class FileBasedWorkflowRepository:
    """File-based workflow repository implementation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.workflows_file = self.data_dir / "workflows.json"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        self.data_dir.mkdir(exist_ok=True)
        if not self.workflows_file.exists():
            self._save_workflows({})
    
    def _load_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load workflows from file"""
        try:
            with open(self.workflows_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_workflows(self, workflows: Dict[str, Dict[str, Any]]):
        """Save workflows to file"""
        with open(self.workflows_file, 'w') as f:
            json.dump(workflows, f, indent=2, default=str)
    
    def _workflow_to_dict(self, workflow: WorkflowRun) -> Dict[str, Any]:
        """Convert workflow entity to dictionary"""
        return {
            'id': workflow.id,
            'status': workflow.status.value,
            'started_at': workflow.started_at.isoformat(),
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'error_message': workflow.error_message,
            'config': workflow.config,
            'results': workflow.results
        }
    
    def _dict_to_workflow(self, data: Dict[str, Any]) -> WorkflowRun:
        """Convert dictionary to workflow entity"""
        return WorkflowRun(
            id=data['id'],
            status=WorkflowStatus(data['status']),
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_message=data.get('error_message'),
            config=data.get('config', {}),
            results=data.get('results', {})
        )
    
    async def save(self, workflow: WorkflowRun) -> WorkflowRun:
        """Save workflow"""
        workflows = self._load_workflows()
        workflows[workflow.id] = self._workflow_to_dict(workflow)
        self._save_workflows(workflows)
        return workflow
    
    async def find_by_id(self, workflow_id: str) -> Optional[WorkflowRun]:
        """Find workflow by ID"""
        workflows = self._load_workflows()
        workflow_data = workflows.get(workflow_id)
        if workflow_data:
            return self._dict_to_workflow(workflow_data)
        return None
    
    async def find_recent(self, limit: int = 10) -> List[WorkflowRun]:
        """Find recent workflows"""
        workflows = self._load_workflows()
        result = []
        for workflow_data in workflows.values():
            result.append(self._dict_to_workflow(workflow_data))
        return sorted(result, key=lambda w: w.started_at, reverse=True)[:limit]
    
    async def update_status(self, workflow_id: str, status: WorkflowStatus, 
                           error_message: str = None) -> bool:
        """Update workflow status"""
        workflows = self._load_workflows()
        if workflow_id in workflows:
            workflows[workflow_id]['status'] = status.value
            if error_message:
                workflows[workflow_id]['error_message'] = error_message
            if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                workflows[workflow_id]['completed_at'] = datetime.now().isoformat()
            self._save_workflows(workflows)
            return True
        return False