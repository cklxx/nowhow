"""
Enhanced storage API endpoints with file merging capabilities.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from datetime import datetime

from core.container import get_container
from core.interfaces import IStorageService
from core.exceptions import StorageError

router = APIRouter(prefix="/storage", tags=["Enhanced Storage"])

def get_storage_service() -> IStorageService:
    """Get storage service from container."""
    container = get_container()
    return container.storage_service

@router.get("/articles/merged")
async def get_merged_articles(
    limit: int = Query(10, description="Maximum number of files to merge"),
    workflow_id: Optional[str] = Query(None, description="Filter by specific workflow ID"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Get merged articles from multiple files."""
    try:
        result = await storage.load_latest_by_type(
            content_type="articles",
            workflow_id=workflow_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": result["merged_data"],
            "metadata": result["metadata"],
            "total_articles": len(result["merged_data"])
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/content/merged")
async def get_merged_content(
    content_type: str = Query(..., description="Type of content (articles, crawled, processed)"),
    limit: int = Query(10, description="Maximum number of files to merge"),
    sort_by: str = Query("timestamp", description="Sort files by (timestamp, size, modified)"),
    merge_strategy: str = Query("auto", description="Merge strategy (auto, articles, crawled, processed)"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Get merged content of specified type."""
    try:
        pattern = f"{content_type}_*.json"
        
        result = await storage.load_and_merge_files(
            pattern=pattern,
            content_type=content_type,
            limit=limit,
            sort_by=sort_by,
            merge_strategy=merge_strategy
        )
        
        return {
            "success": True,
            "content_type": content_type,
            "data": result["merged_data"],
            "metadata": result["metadata"],
            "total_items": len(result["merged_data"])
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/workflow/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: str,
    include_steps: Optional[List[str]] = Query(None, description="Steps to include (crawled, processed, articles)"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Get complete history for a specific workflow."""
    try:
        result = await storage.load_workflow_history(
            workflow_id=workflow_id,
            include_steps=include_steps
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "history": result,
            "steps_count": len(result.get("steps", {}))
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/analytics/timeframe")
async def get_timeframe_analytics(
    content_type: str = Query(..., description="Type of content to analyze"),
    timeframe: str = Query("daily", description="Timeframe (daily, weekly, monthly)"),
    limit: int = Query(30, description="Number of time periods to include"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Get content analytics aggregated by timeframe."""
    try:
        result = await storage.aggregate_by_timeframe(
            content_type=content_type,
            timeframe=timeframe,
            limit=limit
        )
        
        return {
            "success": True,
            "content_type": content_type,
            "timeframe": timeframe,
            "analytics": result,
            "periods_count": len(result.get("periods", {}))
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/statistics")
async def get_storage_statistics(
    storage: IStorageService = Depends(get_storage_service)
):
    """Get comprehensive storage statistics."""
    try:
        stats = await storage.get_content_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/articles/latest")
async def get_latest_articles(
    limit: int = Query(5, description="Number of latest articles"),
    category: Optional[str] = Query(None, description="Filter by category"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Get latest articles with optional category filtering."""
    try:
        result = await storage.load_latest_by_type(
            content_type="articles",
            limit=limit
        )
        
        articles = result["merged_data"]
        
        # Filter by category if specified
        if category:
            articles = [
                article for article in articles 
                if article.get("category", "").lower() == category.lower()
            ]
        
        return {
            "success": True,
            "articles": articles,
            "total_count": len(articles),
            "category_filter": category,
            "metadata": {
                "source_files": len(result["metadata"]["source_files"]),
                "merge_timestamp": result["metadata"]["merge_timestamp"]
            }
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/content/search")
async def search_content(
    query: str = Query(..., description="Search query"),
    content_type: str = Query("articles", description="Type of content to search"),
    limit: int = Query(20, description="Maximum results"),
    storage: IStorageService = Depends(get_storage_service)
):
    """Search content across merged files."""
    try:
        # Load and merge content
        result = await storage.load_latest_by_type(
            content_type=content_type,
            limit=10
        )
        
        # Simple text search
        query_lower = query.lower()
        matching_items = []
        
        for item in result["merged_data"]:
            # Search in title and content
            title = item.get("title", "").lower()
            content = item.get("content", "").lower()
            
            if query_lower in title or query_lower in content:
                # Add relevance score based on matches
                title_matches = title.count(query_lower)
                content_matches = content.count(query_lower)
                
                item["search_relevance"] = title_matches * 2 + content_matches
                matching_items.append(item)
        
        # Sort by relevance
        matching_items.sort(key=lambda x: x.get("search_relevance", 0), reverse=True)
        
        # Apply limit
        matching_items = matching_items[:limit]
        
        return {
            "success": True,
            "query": query,
            "content_type": content_type,
            "results": matching_items,
            "total_matches": len(matching_items),
            "searched_files": result["metadata"]["total_files"]
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/files/list")
async def list_storage_files(
    pattern: str = Query("*.json", description="File pattern to match"),
    limit: int = Query(20, description="Maximum files to list"),
    storage: IStorageService = Depends(get_storage_service)
):
    """List files in storage with metadata."""
    try:
        files = await storage.list_files(pattern=pattern)
        
        # Get file info for each file
        file_details = []
        for file_path in files[:limit]:
            try:
                file_info = await storage.get_file_info(file_path)
                file_details.append(file_info)
            except Exception as e:
                # Skip files that can't be read
                continue
        
        # Sort by modification time (newest first)
        file_details.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "success": True,
            "pattern": pattern,
            "files": file_details,
            "total_files": len(file_details),
            "total_size": sum(f["size"] for f in file_details)
        }
        
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/health")
async def storage_health_check(
    storage: IStorageService = Depends(get_storage_service)
):
    """Health check for storage service."""
    try:
        # Test basic storage operations
        stats = await storage.get_content_statistics()
        
        return {
            "status": "healthy",
            "storage_service": "enhanced",
            "total_files": sum(
                stats["files_by_type"][ft]["file_count"] 
                for ft in stats["files_by_type"]
            ),
            "total_size": stats["total_size"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage health check failed: {str(e)}")