from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import os
from datetime import datetime

from agents import run_content_generation_workflow

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

class WorkflowRequest(BaseModel):
    openai_api_key: Optional[str] = None

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
        workflow_id,
        request.openai_api_key
    )
    
    return WorkflowResponse(
        workflow_id=workflow_id,
        status="started",
        message="Workflow started successfully. Use /workflow/status/{workflow_id} to check progress."
    )

async def run_workflow_background(workflow_id: str, api_key: Optional[str]):
    """Run workflow in background"""
    try:
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        # Run the workflow
        result = await run_content_generation_workflow(openai_api_key=api_key)
        
        # Update results
        workflow_status[workflow_id] = "completed"
        workflow_results[workflow_id].status = "completed"
        workflow_results[workflow_id].results = result
        workflow_results[workflow_id].completed_at = datetime.now()
        
        if "error" in result:
            workflow_status[workflow_id] = "failed"
            workflow_results[workflow_id].status = "failed"
            workflow_results[workflow_id].error = result["error"]
            
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
    """Get generated articles from latest completed workflow"""
    
    # Find latest completed workflow
    completed_workflows = [
        wf for wf in workflow_results.values() 
        if wf.status == "completed" and wf.results
    ]
    
    if not completed_workflows:
        return {"articles": [], "message": "No completed workflows found"}
    
    # Sort by completion time
    latest_workflow = max(completed_workflows, key=lambda x: x.completed_at or datetime.min)
    
    articles = latest_workflow.results.get("articles", [])
    
    return {
        "articles": articles[:limit],
        "total": len(articles),
        "workflow_id": latest_workflow.workflow_id,
        "generated_at": latest_workflow.completed_at
    }

@app.get("/articles/{workflow_id}")
async def get_articles_by_workflow(workflow_id: str, limit: int = 10):
    """Get articles from specific workflow"""
    
    if workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflow_results[workflow_id]
    
    if workflow.status != "completed" or not workflow.results:
        raise HTTPException(status_code=400, detail="Workflow not completed or no results available")
    
    articles = workflow.results.get("articles", [])
    
    return {
        "articles": articles[:limit],
        "total": len(articles),
        "workflow_id": workflow_id,
        "generated_at": workflow.completed_at
    }

@app.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow and its results"""
    
    if workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflow_results[workflow_id]
    if workflow_id in workflow_status:
        del workflow_status[workflow_id]
    
    return {"message": f"Workflow {workflow_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)