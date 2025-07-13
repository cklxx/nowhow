"""
Enhanced storage service with automatic file merging capabilities.
"""

import json
import asyncio
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional, Any, Tuple
import logging
from collections import defaultdict

from config import Settings
from core.interfaces import IStorageService
from core.exceptions import StorageError
from services.storage_service import FileStorageService

logger = logging.getLogger(__name__)


class EnhancedStorageService(FileStorageService):
    """Enhanced storage service with automatic file merging capabilities."""
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.merge_strategies = {
            "articles": self._merge_articles,
            "crawled": self._merge_crawled_content,
            "processed": self._merge_processed_content,
            "workflow_results": self._merge_workflow_results
        }
    
    async def load_and_merge_files(
        self,
        pattern: str,
        content_type: str,
        limit: Optional[int] = None,
        sort_by: str = "timestamp",
        merge_strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        Load and automatically merge multiple files matching a pattern.
        
        Args:
            pattern: File pattern to match (e.g., "articles_*.json")
            content_type: Type of content for merge strategy
            limit: Maximum number of files to load
            sort_by: Sort files by 'timestamp', 'size', or 'modified'
            merge_strategy: Merge strategy ('auto', 'articles', 'crawled', etc.)
            
        Returns:
            Merged data with metadata about source files
        """
        try:
            logger.info(f"Loading and merging files with pattern: {pattern}")
            
            # Find matching files
            files = await self._find_matching_files(pattern, sort_by, limit)
            
            if not files:
                logger.warning(f"No files found matching pattern: {pattern}")
                return {
                    "merged_data": [],
                    "metadata": {
                        "total_files": 0,
                        "merge_timestamp": datetime.now().isoformat(),
                        "content_type": content_type,
                        "source_files": []
                    }
                }
            
            # Load all files
            file_data = await self._load_multiple_files(files)
            
            # Determine merge strategy
            if merge_strategy == "auto":
                merge_strategy = self._detect_merge_strategy(content_type)
            
            # Merge data
            merged_result = await self._merge_data(file_data, merge_strategy, content_type)
            
            # Add comprehensive metadata
            merged_result["metadata"].update({
                "total_files": len(files),
                "merge_timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "merge_strategy": merge_strategy,
                "source_files": [
                    {
                        "path": str(f["path"]),
                        "size": f["size"],
                        "modified": f["modified"],
                        "records_count": len(f["data"]) if isinstance(f["data"], list) 
                                        else f["data"].get("articles", f["data"].get("content", []))
                    }
                    for f in file_data
                ]
            })
            
            logger.info(f"Successfully merged {len(files)} files into {len(merged_result.get('merged_data', []))} records")
            return merged_result
            
        except Exception as e:
            logger.error(f"Failed to load and merge files: {e}")
            raise StorageError(f"Failed to load and merge files: {str(e)}")
    
    async def load_latest_by_type(
        self,
        content_type: str,
        workflow_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Load latest files of a specific type with automatic merging."""
        try:
            # Build pattern based on content type
            if workflow_id:
                pattern = f"{content_type}_*_{workflow_id}.json"
            else:
                pattern = f"{content_type}_*.json"
            
            return await self.load_and_merge_files(
                pattern=pattern,
                content_type=content_type,
                limit=limit,
                sort_by="timestamp"
            )
            
        except Exception as e:
            logger.error(f"Failed to load latest files by type: {e}")
            raise StorageError(f"Failed to load latest files by type: {str(e)}")
    
    async def load_workflow_history(
        self,
        workflow_id: str,
        include_steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Load complete history for a specific workflow."""
        try:
            if include_steps is None:
                include_steps = ["crawled", "processed", "articles"]
            
            workflow_data = {}
            total_files = 0
            
            for step in include_steps:
                step_data = await self.load_latest_by_type(step, workflow_id, limit=50)
                workflow_data[step] = step_data
                total_files += step_data["metadata"]["total_files"]
            
            return {
                "workflow_id": workflow_id,
                "steps": workflow_data,
                "metadata": {
                    "total_files": total_files,
                    "steps_included": include_steps,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to load workflow history: {e}")
            raise StorageError(f"Failed to load workflow history: {str(e)}")
    
    async def aggregate_by_timeframe(
        self,
        content_type: str,
        timeframe: str = "daily",  # daily, weekly, monthly
        limit: int = 30
    ) -> Dict[str, Any]:
        """Aggregate content by time periods."""
        try:
            # Load all files of the type
            all_data = await self.load_latest_by_type(content_type, limit=100)
            
            # Group by timeframe
            grouped_data = defaultdict(list)
            
            for item in all_data.get("merged_data", []):
                # Extract timestamp from item
                timestamp = self._extract_timestamp(item)
                if timestamp:
                    period_key = self._get_period_key(timestamp, timeframe)
                    grouped_data[period_key].append(item)
            
            # Sort periods
            sorted_periods = sorted(grouped_data.keys())[-limit:]
            
            result = {
                "timeframe": timeframe,
                "periods": {}
            }
            
            for period in sorted_periods:
                result["periods"][period] = {
                    "items": grouped_data[period],
                    "count": len(grouped_data[period])
                }
            
            result["metadata"] = {
                "total_periods": len(sorted_periods),
                "total_items": sum(len(items) for items in grouped_data.values()),
                "generated_at": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to aggregate by timeframe: {e}")
            raise StorageError(f"Failed to aggregate by timeframe: {str(e)}")
    
    async def _find_matching_files(
        self,
        pattern: str,
        sort_by: str = "timestamp",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find files matching pattern with metadata."""
        try:
            # Use glob to find matching files
            search_pattern = str(self.base_path / pattern)
            matching_paths = glob.glob(search_pattern)
            
            if not matching_paths:
                return []
            
            # Get file metadata
            files_with_metadata = []
            for path_str in matching_paths:
                path = Path(path_str)
                if path.is_file():
                    stat = path.stat()
                    files_with_metadata.append({
                        "path": path,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "created": datetime.fromtimestamp(stat.st_ctime)
                    })
            
            # Sort files
            if sort_by == "timestamp":
                files_with_metadata.sort(key=lambda x: x["modified"], reverse=True)
            elif sort_by == "size":
                files_with_metadata.sort(key=lambda x: x["size"], reverse=True)
            elif sort_by == "created":
                files_with_metadata.sort(key=lambda x: x["created"], reverse=True)
            
            # Apply limit
            if limit:
                files_with_metadata = files_with_metadata[:limit]
            
            return files_with_metadata
            
        except Exception as e:
            logger.error(f"Error finding matching files: {e}")
            raise StorageError(f"Error finding matching files: {str(e)}")
    
    async def _load_multiple_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Load multiple files concurrently."""
        try:
            async def load_single_file(file_info):
                try:
                    data = await self.load_json(file_info["path"])
                    return {
                        **file_info,
                        "data": data,
                        "load_status": "success"
                    }
                except Exception as e:
                    logger.warning(f"Failed to load file {file_info['path']}: {e}")
                    return {
                        **file_info,
                        "data": None,
                        "load_status": "error",
                        "error": str(e)
                    }
            
            # Load files concurrently
            tasks = [load_single_file(file_info) for file_info in files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful loads
            successful_loads = [
                result for result in results 
                if not isinstance(result, Exception) and result["load_status"] == "success"
            ]
            
            return successful_loads
            
        except Exception as e:
            logger.error(f"Error loading multiple files: {e}")
            raise StorageError(f"Error loading multiple files: {str(e)}")
    
    def _detect_merge_strategy(self, content_type: str) -> str:
        """Detect appropriate merge strategy based on content type."""
        if content_type in self.merge_strategies:
            return content_type
        
        # Default strategies based on content type patterns
        if "article" in content_type.lower():
            return "articles"
        elif "crawl" in content_type.lower():
            return "crawled"
        elif "process" in content_type.lower():
            return "processed"
        else:
            return "workflow_results"
    
    async def _merge_data(
        self,
        file_data: List[Dict[str, Any]],
        strategy: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Merge data using specified strategy."""
        try:
            if strategy in self.merge_strategies:
                merge_func = self.merge_strategies[strategy]
                return await merge_func(file_data, content_type)
            else:
                # Default merge strategy
                return await self._merge_workflow_results(file_data, content_type)
                
        except Exception as e:
            logger.error(f"Error merging data with strategy {strategy}: {e}")
            raise StorageError(f"Error merging data with strategy {strategy}: {str(e)}")
    
    async def _merge_articles(self, file_data: List[Dict[str, Any]], content_type: str) -> Dict[str, Any]:
        """Merge articles from multiple files."""
        all_articles = []
        all_metadata = []
        
        for file_info in file_data:
            data = file_info["data"]
            
            if isinstance(data, dict):
                # Extract articles array
                articles = data.get("articles", [])
                all_articles.extend(articles)
                
                # Collect metadata
                if "metadata" in data:
                    all_metadata.append({
                        "source_file": str(file_info["path"]),
                        "original_metadata": data["metadata"]
                    })
            elif isinstance(data, list):
                # Direct array of articles
                all_articles.extend(data)
        
        # Remove duplicates based on title or ID
        unique_articles = self._deduplicate_articles(all_articles)
        
        # Sort by creation time or relevance
        unique_articles.sort(
            key=lambda x: x.get("created_at", x.get("timestamp", "")),
            reverse=True
        )
        
        return {
            "merged_data": unique_articles,
            "metadata": {
                "merge_type": "articles",
                "total_articles": len(unique_articles),
                "original_files_metadata": all_metadata,
                "deduplication_applied": len(all_articles) - len(unique_articles)
            }
        }
    
    async def _merge_crawled_content(self, file_data: List[Dict[str, Any]], content_type: str) -> Dict[str, Any]:
        """Merge crawled content from multiple files."""
        all_content = []
        source_stats = defaultdict(int)
        
        for file_info in file_data:
            data = file_info["data"]
            
            if isinstance(data, list):
                # Direct array of crawled results
                for item in data:
                    all_content.append({
                        **item,
                        "source_file": str(file_info["path"]),
                        "file_timestamp": file_info["modified"].isoformat()
                    })
                    
                    # Track source statistics
                    source_name = item.get("source", "unknown")
                    source_stats[source_name] += 1
            
            elif isinstance(data, dict):
                # Check for various content structures
                content_items = (
                    data.get("content", []) or 
                    data.get("crawled_content", []) or
                    data.get("results", [])
                )
                
                for item in content_items:
                    all_content.append({
                        **item,
                        "source_file": str(file_info["path"]),
                        "file_timestamp": file_info["modified"].isoformat()
                    })
                    
                    source_name = item.get("source", "unknown")
                    source_stats[source_name] += 1
        
        # Remove duplicates based on URL or ID
        unique_content = self._deduplicate_content(all_content)
        
        return {
            "merged_data": unique_content,
            "metadata": {
                "merge_type": "crawled_content",
                "total_items": len(unique_content),
                "sources_stats": dict(source_stats),
                "deduplication_applied": len(all_content) - len(unique_content)
            }
        }
    
    async def _merge_processed_content(self, file_data: List[Dict[str, Any]], content_type: str) -> Dict[str, Any]:
        """Merge processed content from multiple files."""
        all_content = []
        category_stats = defaultdict(int)
        relevance_scores = []
        
        for file_info in file_data:
            data = file_info["data"]
            
            content_items = []
            if isinstance(data, list):
                content_items = data
            elif isinstance(data, dict):
                content_items = (
                    data.get("processed_content", []) or
                    data.get("content", []) or
                    data.get("results", [])
                )
            
            for item in content_items:
                processed_item = {
                    **item,
                    "source_file": str(file_info["path"]),
                    "file_timestamp": file_info["modified"].isoformat()
                }
                all_content.append(processed_item)
                
                # Collect statistics
                category = item.get("category", "unknown")
                category_stats[category] += 1
                
                relevance_score = item.get("relevance_score")
                if relevance_score is not None:
                    relevance_scores.append(relevance_score)
        
        # Remove duplicates
        unique_content = self._deduplicate_content(all_content)
        
        # Sort by relevance score
        unique_content.sort(
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        # Calculate statistics
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        return {
            "merged_data": unique_content,
            "metadata": {
                "merge_type": "processed_content",
                "total_items": len(unique_content),
                "category_stats": dict(category_stats),
                "avg_relevance_score": round(avg_relevance, 3),
                "deduplication_applied": len(all_content) - len(unique_content)
            }
        }
    
    async def _merge_workflow_results(self, file_data: List[Dict[str, Any]], content_type: str) -> Dict[str, Any]:
        """Default merge strategy for workflow results."""
        merged_items = []
        
        for file_info in file_data:
            data = file_info["data"]
            
            # Add file metadata to each item
            file_metadata = {
                "source_file": str(file_info["path"]),
                "file_timestamp": file_info["modified"].isoformat(),
                "file_size": file_info["size"]
            }
            
            if isinstance(data, list):
                for item in data:
                    merged_items.append({**item, **file_metadata})
            elif isinstance(data, dict):
                merged_items.append({**data, **file_metadata})
        
        return {
            "merged_data": merged_items,
            "metadata": {
                "merge_type": "workflow_results",
                "total_items": len(merged_items)
            }
        }
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title and content similarity."""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title = article.get("title", "").strip().lower()
            article_id = article.get("id", "")
            
            # Create a unique key
            unique_key = article_id if article_id else title
            
            if unique_key and unique_key not in seen_titles:
                seen_titles.add(unique_key)
                unique_articles.append(article)
        
        return unique_articles
    
    def _deduplicate_content(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate content based on URL or ID."""
        seen_urls = set()
        unique_content = []
        
        for item in content_items:
            url = item.get("url", "")
            item_id = item.get("id", "")
            
            # Create unique key
            unique_key = item_id if item_id else url
            
            if unique_key and unique_key not in seen_urls:
                seen_urls.add(unique_key)
                unique_content.append(item)
        
        return unique_content
    
    def _extract_timestamp(self, item: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from item."""
        for field in ["created_at", "timestamp", "crawled_at", "processed_at"]:
            if field in item:
                try:
                    if isinstance(item[field], str):
                        return datetime.fromisoformat(item[field].replace('Z', '+00:00'))
                    elif isinstance(item[field], datetime):
                        return item[field]
                except:
                    continue
        return None
    
    def _get_period_key(self, timestamp: datetime, timeframe: str) -> str:
        """Get period key for grouping."""
        if timeframe == "daily":
            return timestamp.strftime("%Y-%m-%d")
        elif timeframe == "weekly":
            return timestamp.strftime("%Y-W%U")
        elif timeframe == "monthly":
            return timestamp.strftime("%Y-%m")
        else:
            return timestamp.strftime("%Y-%m-%d")
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored content."""
        try:
            stats = {
                "files_by_type": {},
                "total_size": 0,
                "latest_updates": {},
                "content_counts": {}
            }
            
            # Scan all files in data directory
            for file_type in ["articles", "crawled", "processed"]:
                pattern = f"{file_type}_*.json"
                files = await self._find_matching_files(pattern)
                
                stats["files_by_type"][file_type] = {
                    "file_count": len(files),
                    "total_size": sum(f["size"] for f in files),
                    "latest_file": files[0]["modified"].isoformat() if files else None
                }
                
                stats["total_size"] += stats["files_by_type"][file_type]["total_size"]
                
                # Get content count from latest file
                if files:
                    try:
                        latest_data = await self.load_and_merge_files(
                            pattern, file_type, limit=1
                        )
                        stats["content_counts"][file_type] = len(
                            latest_data.get("merged_data", [])
                        )
                    except:
                        stats["content_counts"][file_type] = 0
            
            stats["generated_at"] = datetime.now().isoformat()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get content statistics: {e}")
            raise StorageError(f"Failed to get content statistics: {str(e)}")