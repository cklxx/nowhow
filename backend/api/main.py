from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from agents import run_content_generation_workflow
from utils.file_storage import FileStorage

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")

app = FastAPI(
    title="AI Content Aggregator API",
    description="Multi-agent system for crawling, processing, and generating AI-related content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (use database in production)
workflow_results = {}
workflow_status = {}

# File storage instance
file_storage = FileStorage()

class WorkflowRequest(BaseModel):
    pass

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

class WorkflowResult(BaseModel):
    workflow_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Content Aggregator API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Start the AI content generation workflow"""
    
    # Generate workflow ID
    workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(workflow_results)}"
    
    # Initialize workflow status
    workflow_status[workflow_id] = "running"
    workflow_results[workflow_id] = WorkflowResult(
        workflow_id=workflow_id,
        status="running",
        created_at=datetime.now()
    )
    
    # Start workflow in background
    background_tasks.add_task(
        run_workflow_background,
        workflow_id
    )
    
    return WorkflowResponse(
        workflow_id=workflow_id,
        status="started",
        message="Workflow started successfully. Use /workflow/status/{workflow_id} to check progress."
    )

async def run_workflow_background(workflow_id: str):
    """Run workflow in background"""
    try:
        # Get API key from environment
        api_key = os.getenv("ARK_API_KEY")
        print(f"🔑 Using API key: {'***' + api_key[-4:] if api_key else 'None'}")
        
        if not api_key:
            raise ValueError("ARK_API_KEY environment variable not set")
        
        # Run the workflow
        result = await run_content_generation_workflow(openai_api_key=api_key)
        
        # Update results
        workflow_status[workflow_id] = "completed"
        workflow_results[workflow_id].status = "completed"
        workflow_results[workflow_id].results = result
        workflow_results[workflow_id].progress = result.get("progress", {})
        workflow_results[workflow_id].completed_at = datetime.now()
        
        if "error" in result:
            workflow_status[workflow_id] = "failed"
            workflow_results[workflow_id].status = "failed"
            workflow_results[workflow_id].error = result["error"]
            workflow_results[workflow_id].progress = result.get("progress", {})
            
    except Exception as e:
        workflow_status[workflow_id] = "failed"
        workflow_results[workflow_id].status = "failed"
        workflow_results[workflow_id].error = str(e)
        workflow_results[workflow_id].completed_at = datetime.now()

@app.get("/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow status and results"""
    
    if workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_results[workflow_id]

@app.get("/workflow/list")
async def list_workflows():
    """List all workflows"""
    return {
        "workflows": [
            {
                "workflow_id": wf.workflow_id,
                "status": wf.status,
                "created_at": wf.created_at,
                "completed_at": wf.completed_at
            }
            for wf in workflow_results.values()
        ]
    }

@app.get("/articles")
async def get_articles(limit: int = 10):
    """Get generated articles from latest completed workflow or from file storage"""
    
    # First try to find latest completed workflow in memory
    completed_workflows = [
        wf for wf in workflow_results.values() 
        if wf.status == "completed" and wf.results
    ]
    
    if completed_workflows:
        # Sort by completion time
        latest_workflow = max(completed_workflows, key=lambda x: x.completed_at or datetime.min)
        articles = latest_workflow.results.get("articles", [])
        
        return {
            "articles": articles[:limit],
            "total": len(articles),
            "workflow_id": latest_workflow.workflow_id,
            "generated_at": latest_workflow.completed_at,
            "source": "memory"
        }
    
    # If no workflows in memory, try to load from file storage
    try:
        articles = file_storage.load_generated_articles()
        if articles:
            metadata = file_storage.get_latest_articles_metadata()
            return {
                "articles": articles[:limit],
                "total": len(articles),
                "workflow_id": metadata.get("workflow_id", "unknown") if metadata else "unknown",
                "generated_at": metadata.get("created_at") if metadata else None,
                "source": "file_storage",
                "message": "Loaded from file storage"
            }
    except Exception as e:
        print(f"Error loading articles from file storage: {e}")
    
    # If no articles found anywhere
    return {
        "articles": [], 
        "message": "No articles found. Please run a workflow to generate articles.",
        "source": "none"
    }

@app.get("/articles/{workflow_id}")
async def get_articles_by_workflow(workflow_id: str, limit: int = 10):
    """Get articles from specific workflow (memory or file storage)"""
    
    # First check memory
    if workflow_id in workflow_results:
        workflow = workflow_results[workflow_id]
        
        if workflow.status == "completed" and workflow.results:
            articles = workflow.results.get("articles", [])
            return {
                "articles": articles[:limit],
                "total": len(articles),
                "workflow_id": workflow_id,
                "generated_at": workflow.completed_at,
                "source": "memory"
            }
        else:
            raise HTTPException(status_code=400, detail="Workflow not completed or no results available")
    
    # If not in memory, try file storage
    try:
        articles = file_storage.load_generated_articles(workflow_id)
        if articles:
            return {
                "articles": articles[:limit],
                "total": len(articles),
                "workflow_id": workflow_id,
                "generated_at": None,  # We don't have this info from file storage easily
                "source": "file_storage",
                "message": "Loaded from file storage"
            }
    except Exception as e:
        print(f"Error loading articles for workflow {workflow_id} from file storage: {e}")
    
    # If not found anywhere
    raise HTTPException(status_code=404, detail="Workflow not found in memory or file storage")

@app.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow and its results"""
    
    if workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflow_results[workflow_id]
    if workflow_id in workflow_status:
        del workflow_status[workflow_id]
    
    return {"message": f"Workflow {workflow_id} deleted successfully"}

@app.get("/files/workflows")
async def list_stored_workflows():
    """List all stored workflow files"""
    stored_workflows = file_storage.list_stored_workflows()
    return {
        "stored_workflows": stored_workflows,
        "total": len(stored_workflows)
    }

@app.get("/files/content/{workflow_id}")
async def get_stored_content(workflow_id: str):
    """Get stored content for a specific workflow"""
    try:
        crawled_content = file_storage.load_crawled_content(workflow_id)
        processed_content = file_storage.load_processed_content(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "crawled_content": crawled_content,
            "processed_content": processed_content
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Content not found for workflow {workflow_id}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)