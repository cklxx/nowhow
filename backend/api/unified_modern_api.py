"""
Unified Modern API using cutting-edge 2024 tools.
Replaces legacy workflow with modern crawler stack.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import unified modern workflow
from agents.unified_modern_workflow import run_unified_modern_workflow, UnifiedModernWorkflow
from utils.file_storage import FileStorage
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Pydantic models
class WorkflowStartRequest(BaseModel):
    openai_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

class ToolStatusResponse(BaseModel):
    tool_name: str
    available: bool
    description: str
    setup_instructions: Optional[str] = None

# Global workflow tracking
active_workflows: Dict[str, Dict[str, Any]] = {}
workflow_results: Dict[str, Dict[str, Any]] = {}


def create_unified_modern_app() -> FastAPI:
    """Create unified modern FastAPI app"""
    app = FastAPI(
        title="AI Content Aggregator - Modern Edition",
        version="2.0.0",
        description="Modern AI content aggregation using Firecrawl, Crawl4AI, and Playwright"
    )
    
    # Load settings
    settings = get_settings()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins if hasattr(settings, 'cors') else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Initialize file storage
    file_storage = FileStorage()
    
    @app.get("/health")
    async def health_check():
        """Enhanced health check with tool status"""
        try:
            # Check tool availability
            tools_status = await get_tools_status()
            available_tools = [tool["tool_name"] for tool in tools_status if tool["available"]]
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0 - Modern Edition",
                "available_tools": available_tools,
                "tools_count": len(available_tools),
                "api_keys": {
                    "openai": bool(os.getenv('OPENAI_API_KEY') or os.getenv('ARK_API_KEY')),
                    "firecrawl": bool(os.getenv('FIRECRAWL_API_KEY'))
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "degraded",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @app.get("/tools/status", response_model=List[ToolStatusResponse])
    async def get_tools_status():
        """Get status of all modern tools"""
        tools_status = []
        
        # Check Firecrawl
        try:
            from firecrawl import FirecrawlApp
            firecrawl_available = True
            firecrawl_setup = None
        except ImportError:
            firecrawl_available = False
            firecrawl_setup = "pip install firecrawl-py"
        
        tools_status.append(ToolStatusResponse(
            tool_name="Firecrawl",
            available=firecrawl_available and bool(os.getenv('FIRECRAWL_API_KEY')),
            description="Premium AI-ready content extraction with API",
            setup_instructions=firecrawl_setup or "Set FIRECRAWL_API_KEY environment variable"
        ))
        
        # Check Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            crawl4ai_available = True
            crawl4ai_setup = None
        except ImportError:
            crawl4ai_available = False
            crawl4ai_setup = "pip install crawl4ai"
        
        tools_status.append(ToolStatusResponse(
            tool_name="Crawl4AI",
            available=crawl4ai_available,
            description="Open source LLM-friendly web crawler",
            setup_instructions=crawl4ai_setup
        ))
        
        # Check Playwright
        try:
            from playwright.async_api import async_playwright
            playwright_available = True
            playwright_setup = None
        except ImportError:
            playwright_available = False
            playwright_setup = "pip install playwright && playwright install"
        
        tools_status.append(ToolStatusResponse(
            tool_name="Playwright",
            available=playwright_available,
            description="Modern browser automation for dynamic content",
            setup_instructions=playwright_setup
        ))
        
        # Basic tools (always available)
        tools_status.append(ToolStatusResponse(
            tool_name="HTTP + BeautifulSoup",
            available=True,
            description="Fallback HTTP crawler with HTML parsing",
            setup_instructions=None
        ))
        
        return tools_status
    
    @app.post("/workflow/start", response_model=WorkflowResponse)
    async def start_modern_workflow(
        request: WorkflowStartRequest,
        background_tasks: BackgroundTasks
    ):
        """Start unified modern workflow"""
        try:
            workflow_id = str(uuid4())
            
            # Get API keys from request or environment
            openai_key = request.openai_api_key or os.getenv('OPENAI_API_KEY') or os.getenv('ARK_API_KEY')
            firecrawl_key = request.firecrawl_api_key or os.getenv('FIRECRAWL_API_KEY')
            
            # Validate at least one API key for AI processing
            if not openai_key:
                raise HTTPException(
                    status_code=400,
                    detail="OpenAI/ARK API key required for content processing and generation"
                )
            
            # Initialize workflow tracking
            active_workflows[workflow_id] = {
                "status": "starting",
                "started_at": datetime.now().isoformat(),
                "progress": {"current_step": "initializing"},
                "config": {
                    "openai_enabled": bool(openai_key),
                    "firecrawl_enabled": bool(firecrawl_key)
                }
            }
            
            # Start workflow in background
            background_tasks.add_task(
                run_workflow_background,
                workflow_id,
                openai_key,
                firecrawl_key
            )
            
            return WorkflowResponse(
                workflow_id=workflow_id,
                status="started",
                message="Modern workflow started successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/workflow/status/{workflow_id}")
    async def get_workflow_status(workflow_id: str):
        """Get modern workflow status"""
        try:
            # Check if workflow exists
            if workflow_id not in active_workflows and workflow_id not in workflow_results:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Return completed results if available
            if workflow_id in workflow_results:
                return workflow_results[workflow_id]
            
            # Return active workflow status
            if workflow_id in active_workflows:
                return active_workflows[workflow_id]
            
            raise HTTPException(status_code=404, detail="Workflow not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/workflow/list")
    async def list_workflows(limit: int = 10):
        """List recent workflows"""
        try:
            all_workflows = []
            
            # Add completed workflows
            for wf_id, result in workflow_results.items():
                all_workflows.append({
                    "workflow_id": wf_id,
                    "status": result.get("status", "completed"),
                    "started_at": result.get("started_at"),
                    "completed_at": result.get("completed_at"),
                    "success": result.get("success", False),
                    "articles_count": len(result.get("articles", []))
                })
            
            # Add active workflows
            for wf_id, status in active_workflows.items():
                all_workflows.append({
                    "workflow_id": wf_id,
                    "status": status.get("status", "running"),
                    "started_at": status.get("started_at"),
                    "current_step": status.get("progress", {}).get("current_step"),
                    "success": None
                })
            
            # Sort by start time (newest first)
            all_workflows.sort(key=lambda x: x.get("started_at", ""), reverse=True)
            
            return {
                "workflows": all_workflows[:limit],
                "total": len(all_workflows),
                "active_count": len(active_workflows),
                "completed_count": len(workflow_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/articles")
    async def get_articles(
        workflow_id: Optional[str] = None,
        limit: int = 20,
        category: Optional[str] = None
    ):
        """Get generated articles"""
        try:
            if workflow_id:
                # Get articles from specific workflow
                if workflow_id in workflow_results:
                    articles = workflow_results[workflow_id].get("articles", [])
                else:
                    # Try to load from file
                    try:
                        articles_data = file_storage.load_generated_articles(workflow_id)
                        articles = articles_data.get("articles", [])
                    except:
                        articles = []
            else:
                # Get articles from all workflows
                articles = []
                
                # Collect from completed workflows
                for result in workflow_results.values():
                    articles.extend(result.get("articles", []))
                
                # Try to load from recent files
                try:
                    import glob
                    article_files = glob.glob("generated_articles/articles_*.json")
                    article_files.sort(key=os.path.getmtime, reverse=True)
                    
                    for file_path in article_files[:5]:  # Load from 5 most recent files
                        try:
                            with open(file_path, 'r') as f:
                                import json
                                data = json.load(f)
                                articles.extend(data.get("articles", []))
                        except:
                            continue
                except:
                    pass
            
            # Filter by category if specified
            if category:
                articles = [a for a in articles if a.get("category", "").lower() == category.lower()]
            
            # Sort by quality score and date
            articles.sort(key=lambda x: (
                x.get("validation_score", x.get("quality_score", 0.5)),
                x.get("generated_at", x.get("timestamp", ""))
            ), reverse=True)
            
            # Apply limit
            articles = articles[:limit]
            
            # Calculate statistics
            total_articles = len(articles)
            avg_quality = sum(a.get("validation_score", a.get("quality_score", 0.5)) for a in articles) / max(total_articles, 1)
            categories = list(set(a.get("category", "unknown") for a in articles))
            
            return {
                "articles": articles,
                "total": total_articles,
                "average_quality": avg_quality,
                "categories": categories,
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/articles/statistics")
    async def get_article_statistics():
        """Get comprehensive article statistics"""
        try:
            stats = {
                "total_workflows": len(workflow_results),
                "total_articles": 0,
                "average_quality": 0.0,
                "quality_distribution": {"high": 0, "medium": 0, "low": 0},
                "tools_usage": {},
                "categories": {},
                "recent_activity": []
            }
            
            all_articles = []
            tools_count = {}
            categories_count = {}
            
            # Collect data from all completed workflows
            for wf_id, result in workflow_results.items():
                articles = result.get("articles", [])
                all_articles.extend(articles)
                
                # Count tool usage
                tools_used = result.get("crawling", {}).get("tools_used", [])
                for tool in tools_used:
                    tools_count[tool] = tools_count.get(tool, 0) + 1
                
                # Count categories
                for article in articles:
                    category = article.get("category", "unknown")
                    categories_count[category] = categories_count.get(category, 0) + 1
                
                # Add to recent activity
                stats["recent_activity"].append({
                    "workflow_id": wf_id,
                    "articles_count": len(articles),
                    "completed_at": result.get("completed_at"),
                    "success": result.get("success", False)
                })
            
            # Calculate statistics
            stats["total_articles"] = len(all_articles)
            
            if all_articles:
                # Quality statistics
                quality_scores = [a.get("validation_score", a.get("quality_score", 0.5)) for a in all_articles]
                stats["average_quality"] = sum(quality_scores) / len(quality_scores)
                
                # Quality distribution
                for score in quality_scores:
                    if score >= 0.8:
                        stats["quality_distribution"]["high"] += 1
                    elif score >= 0.6:
                        stats["quality_distribution"]["medium"] += 1
                    else:
                        stats["quality_distribution"]["low"] += 1
            
            stats["tools_usage"] = tools_count
            stats["categories"] = categories_count
            
            # Sort recent activity by completion date
            stats["recent_activity"].sort(key=lambda x: x.get("completed_at", ""), reverse=True)
            stats["recent_activity"] = stats["recent_activity"][:10]  # Keep last 10
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get article statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/workflow/{workflow_id}")
    async def delete_workflow(workflow_id: str):
        """Delete workflow and its data"""
        try:
            deleted = False
            
            # Remove from active workflows
            if workflow_id in active_workflows:
                del active_workflows[workflow_id]
                deleted = True
            
            # Remove from completed workflows
            if workflow_id in workflow_results:
                del workflow_results[workflow_id]
                deleted = True
            
            if not deleted:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return {"message": "Workflow deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


async def run_workflow_background(
    workflow_id: str,
    openai_api_key: str,
    firecrawl_api_key: Optional[str]
):
    """Run unified modern workflow in background"""
    try:
        # Update status
        active_workflows[workflow_id]["status"] = "running"
        active_workflows[workflow_id]["progress"]["current_step"] = "modern_crawling"
        
        # Run unified modern workflow
        result = await run_unified_modern_workflow(
            openai_api_key=openai_api_key,
            firecrawl_api_key=firecrawl_api_key
        )
        
        # Add completion timestamp
        result["completed_at"] = datetime.now().isoformat()
        result["started_at"] = active_workflows[workflow_id]["started_at"]
        
        # Move to completed workflows
        workflow_results[workflow_id] = result
        
        # Remove from active workflows
        if workflow_id in active_workflows:
            del active_workflows[workflow_id]
        
        logger.info(f"Workflow {workflow_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        
        # Update with error status
        error_result = {
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id,
            "completed_at": datetime.now().isoformat(),
            "started_at": active_workflows.get(workflow_id, {}).get("started_at")
        }
        
        workflow_results[workflow_id] = error_result
        
        # Remove from active workflows
        if workflow_id in active_workflows:
            del active_workflows[workflow_id]


# Create the app instance
app = create_unified_modern_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)