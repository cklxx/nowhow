"""
Clean Architecture FastAPI application.
High cohesion, low coupling, dependency injection.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.dependency_container import get_container, Container
from core.clean_architecture import Source, SourceType, WorkflowStatus
from use_cases.source_use_cases import SourceUseCasesImpl
from use_cases.workflow_use_cases import WorkflowUseCasesImpl

logger = logging.getLogger(__name__)


# === REQUEST/RESPONSE MODELS ===

class SourceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(rss|html|api|website)$")
    category: str = Field(default="general", max_length=50)
    active: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SourceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = Field(None, min_length=1)
    type: Optional[str] = Field(None, pattern="^(rss|html|api|website)$")
    category: Optional[str] = Field(None, max_length=50)
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class SourceResponse(BaseModel):
    id: str
    name: str
    url: str
    type: str
    category: str
    active: bool
    created_at: str
    metadata: Dict[str, Any]

class WorkflowStartRequest(BaseModel):
    source_ids: Optional[List[str]] = None
    category: Optional[str] = None
    topic: Optional[str] = None  # 新增主题参数
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WorkflowResponse(BaseModel):
    id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    config: Dict[str, Any]
    results: Dict[str, Any]

class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# === DEPENDENCY INJECTION ===

def get_source_use_cases() -> SourceUseCasesImpl:
    """Get source use cases dependency"""
    container = get_container()
    return container.use_cases.source_use_cases

def get_workflow_use_cases() -> WorkflowUseCasesImpl:
    """Get workflow use cases dependency"""
    container = get_container()
    return container.use_cases.workflow_use_cases


# === APPLICATION FACTORY ===

def create_clean_app() -> FastAPI:
    """Create clean architecture FastAPI application"""
    
    # Initialize container
    container = get_container()
    
    app = FastAPI(
        title="AI Content Aggregator - Clean Architecture",
        version="3.0.0",
        description="Clean architecture implementation with high cohesion and low coupling"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=container.config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # === HEALTH CHECK ===
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Check tool availability
            crawler_tools = container.services.crawler_service.get_available_tools()
            available_tools = [tool for tool, available in crawler_tools.items() if available]
            
            return ApiResponse(
                success=True,
                data={
                    "status": "healthy",
                    "version": "3.0.0",
                    "architecture": "clean",
                    "available_tools": available_tools,
                    "api_keys_configured": {
                        "ark": bool(container.config.api_key_ark),
                        "firecrawl": bool(container.config.api_key_firecrawl)
                    }
                },
                message="System healthy"
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ApiResponse(
                success=False,
                message=f"System unhealthy: {str(e)}"
            )
    
    # === SOURCE MANAGEMENT ===
    
    @app.post("/sources", response_model=ApiResponse)
    async def create_source(
        request: SourceCreateRequest,
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """Create a new source"""
        try:
            source = await source_use_cases.create_source(request.dict())
            
            return ApiResponse(
                success=True,
                data=SourceResponse(
                    id=source.id,
                    name=source.name,
                    url=source.url,
                    type=source.type.value,
                    category=source.category,
                    active=source.active,
                    created_at=source.created_at.isoformat(),
                    metadata=source.metadata
                ),
                message="Source created successfully"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create source: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/sources", response_model=ApiResponse)
    async def list_sources(
        active_only: bool = True,
        category: Optional[str] = None,
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """List sources"""
        try:
            if category:
                sources = await source_use_cases.get_sources_by_category(category)
            else:
                sources = await source_use_cases.list_sources(active_only)
            
            source_responses = [
                SourceResponse(
                    id=source.id,
                    name=source.name,
                    url=source.url,
                    type=source.type.value,
                    category=source.category,
                    active=source.active,
                    created_at=source.created_at.isoformat(),
                    metadata=source.metadata
                )
                for source in sources
            ]
            
            return ApiResponse(
                success=True,
                data={
                    "sources": source_responses,
                    "total": len(source_responses)
                },
                message=f"Found {len(source_responses)} sources"
            )
        except Exception as e:
            logger.error(f"Failed to list sources: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/sources/statistics", response_model=ApiResponse)
    async def get_source_statistics(
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """Get source statistics"""
        try:
            stats = await source_use_cases.get_source_statistics()
            
            return ApiResponse(
                success=True,
                data=stats,
                message="Source statistics retrieved"
            )
        except Exception as e:
            logger.error(f"Failed to get source statistics: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/sources/{source_id}", response_model=ApiResponse)
    async def get_source(
        source_id: str,
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """Get source by ID"""
        try:
            source = await source_use_cases.get_source(source_id)
            
            if not source:
                raise HTTPException(status_code=404, detail="Source not found")
            
            return ApiResponse(
                success=True,
                data=SourceResponse(
                    id=source.id,
                    name=source.name,
                    url=source.url,
                    type=source.type.value,
                    category=source.category,
                    active=source.active,
                    created_at=source.created_at.isoformat(),
                    metadata=source.metadata
                ),
                message="Source found"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get source: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.put("/sources/{source_id}", response_model=ApiResponse)
    async def update_source(
        source_id: str,
        request: SourceUpdateRequest,
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """Update source"""
        try:
            # Filter out None values
            updates = {k: v for k, v in request.dict().items() if v is not None}
            
            source = await source_use_cases.update_source(source_id, updates)
            
            return ApiResponse(
                success=True,
                data=SourceResponse(
                    id=source.id,
                    name=source.name,
                    url=source.url,
                    type=source.type.value,
                    category=source.category,
                    active=source.active,
                    created_at=source.created_at.isoformat(),
                    metadata=source.metadata
                ),
                message="Source updated successfully"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to update source: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.delete("/sources/{source_id}", response_model=ApiResponse)
    async def delete_source(
        source_id: str,
        source_use_cases: SourceUseCasesImpl = Depends(get_source_use_cases)
    ):
        """Delete source"""
        try:
            success = await source_use_cases.delete_source(source_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Source not found")
            
            return ApiResponse(
                success=True,
                message="Source deleted successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete source: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # === WORKFLOW MANAGEMENT ===
    
    @app.post("/workflows", response_model=ApiResponse)
    async def start_workflow(
        request: WorkflowStartRequest,
        background_tasks: BackgroundTasks,
        workflow_use_cases: WorkflowUseCasesImpl = Depends(get_workflow_use_cases)
    ):
        """Start a new workflow"""
        try:
            workflow = await workflow_use_cases.start_workflow(request.dict())
            
            return ApiResponse(
                success=True,
                data=WorkflowResponse(
                    id=workflow.id,
                    status=workflow.status.value,
                    started_at=workflow.started_at.isoformat(),
                    completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
                    error_message=workflow.error_message,
                    config=workflow.config,
                    results=workflow.results
                ),
                message="Workflow started successfully"
            )
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/workflows/{workflow_id}", response_model=ApiResponse)
    async def get_workflow(
        workflow_id: str,
        workflow_use_cases: WorkflowUseCasesImpl = Depends(get_workflow_use_cases)
    ):
        """Get workflow status"""
        try:
            workflow = await workflow_use_cases.get_workflow_status(workflow_id)
            
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return ApiResponse(
                success=True,
                data=WorkflowResponse(
                    id=workflow.id,
                    status=workflow.status.value,
                    started_at=workflow.started_at.isoformat(),
                    completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
                    error_message=workflow.error_message,
                    config=workflow.config,
                    results=workflow.results
                ),
                message="Workflow found"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/workflows", response_model=ApiResponse)
    async def list_workflows(
        limit: int = 10,
        workflow_use_cases: WorkflowUseCasesImpl = Depends(get_workflow_use_cases)
    ):
        """List recent workflows"""
        try:
            workflows = await workflow_use_cases.list_workflows(limit)
            
            workflow_responses = [
                WorkflowResponse(
                    id=workflow.id,
                    status=workflow.status.value,
                    started_at=workflow.started_at.isoformat(),
                    completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
                    error_message=workflow.error_message,
                    config=workflow.config,
                    results=workflow.results
                )
                for workflow in workflows
            ]
            
            return ApiResponse(
                success=True,
                data={
                    "workflows": workflow_responses,
                    "total": len(workflow_responses)
                },
                message=f"Found {len(workflow_responses)} workflows"
            )
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.delete("/workflows/{workflow_id}", response_model=ApiResponse)
    async def cancel_workflow(
        workflow_id: str,
        workflow_use_cases: WorkflowUseCasesImpl = Depends(get_workflow_use_cases)
    ):
        """Cancel workflow"""
        try:
            success = await workflow_use_cases.cancel_workflow(workflow_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Workflow not found or cannot be cancelled")
            
            return ApiResponse(
                success=True,
                message="Workflow cancelled successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # === ARTICLES ===
    
    @app.get("/articles", response_model=ApiResponse)
    async def get_articles(
        workflow_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ):
        """Get articles"""
        try:
            container = get_container()
            
            if workflow_id:
                articles = await container.repositories.article_repository.find_by_workflow(workflow_id)
            elif category:
                articles = await container.repositories.article_repository.find_by_category(category)
            else:
                articles = await container.repositories.article_repository.find_recent(limit)
            
            article_responses = [
                {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    "url": article.url,
                    "source_id": article.source_id,
                    "category": article.category,
                    "author": article.author,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "created_at": article.created_at.isoformat(),
                    "quality_score": article.quality_score,
                    "metadata": article.metadata
                }
                for article in articles[:limit]
            ]
            
            return ApiResponse(
                success=True,
                data={
                    "articles": article_responses,
                    "total": len(article_responses)
                },
                message=f"Found {len(article_responses)} articles"
            )
        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return app


# Create app instance
app = create_clean_app()