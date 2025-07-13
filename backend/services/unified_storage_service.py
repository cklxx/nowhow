"""
Unified storage service that bridges old FileStorage and new StorageService architecture.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
import logging
import uuid

from core.interfaces import IStorageService
from core.exceptions import StorageError
from utils.file_storage import FileStorage
from .cache_service import CacheService, ArticleDeduplicator

logger = logging.getLogger(__name__)


class UnifiedStorageService(IStorageService):
    """
    Unified storage service that combines old FileStorage with new architecture.
    Provides backward compatibility while using modern async patterns.
    """
    
    def __init__(self, base_path: Optional[str] = None, enable_cache: bool = True, enable_dedup: bool = True):
        # Initialize old FileStorage for compatibility
        self.file_storage = FileStorage(base_path)
        
        # Set up modern storage paths
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Use project root like FileStorage does
            current_dir = Path(__file__).parent.parent.parent
            self.base_path = current_dir
        
        # Create modern storage directories
        self.modern_data_path = self.base_path / "backend" / "data"
        self.modern_data_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        subdirs = ['articles', 'workflows', 'content', 'metadata']
        for subdir in subdirs:
            (self.modern_data_path / subdir).mkdir(exist_ok=True)
        
        # Initialize cache and deduplication services
        self.cache_enabled = enable_cache
        self.dedup_enabled = enable_dedup
        
        if self.cache_enabled:
            cache_dir = self.modern_data_path / "cache"
            self.cache_service = CacheService(str(cache_dir))
        
        if self.dedup_enabled:
            self.deduplicator = ArticleDeduplicator()
    
    async def save_json(
        self,
        data: Union[Dict, List],
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save data as JSON file with modern async approach."""
        try:
            # Generate proper filename if it's a pattern
            if not filename.endswith('.json'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                workflow_id = workflow_id or str(uuid.uuid4())[:8]
                filename = f"{filename}_{timestamp}_{workflow_id}.json"
            
            filepath = self._get_modern_file_path(filename)
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata if dict
            if isinstance(data, dict):
                data = {
                    **data,
                    "_metadata": {
                        "created_at": datetime.now().isoformat(),
                        "workflow_id": workflow_id,
                        "file_type": "json",
                        "storage_version": "unified"
                    }
                }
            
            # Write file atomically
            temp_filepath = filepath.with_suffix('.tmp')
            
            def write_file():
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                temp_filepath.rename(filepath)
            
            await asyncio.get_event_loop().run_in_executor(None, write_file)
            
            logger.info(f"Saved JSON data to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save JSON data: {e}")
            raise StorageError(f"Failed to save JSON data: {str(e)}")
    
    async def load_json(self, filepath: Union[str, Path]) -> Union[Dict, List]:
        """Load data from JSON file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found: {filepath}")
            
            def read_file():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            data = await asyncio.get_event_loop().run_in_executor(None, read_file)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {filepath}: {e}")
            raise StorageError(f"Invalid JSON in file {filepath}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load JSON data: {e}")
            raise StorageError(f"Failed to load JSON data: {str(e)}")
    
    async def save_text(
        self,
        content: str,
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save content as text file."""
        try:
            if not filename.endswith(('.txt', '.md')):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                workflow_id = workflow_id or str(uuid.uuid4())[:8]
                filename = f"{filename}_{timestamp}_{workflow_id}.txt"
            
            filepath = self._get_modern_file_path(filename)
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata header
            metadata_header = f"""---
created_at: {datetime.now().isoformat()}
workflow_id: {workflow_id}
file_type: text
storage_version: unified
---

"""
            
            full_content = metadata_header + content
            
            def write_file():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)
            
            await asyncio.get_event_loop().run_in_executor(None, write_file)
            
            logger.info(f"Saved text content to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save text content: {e}")
            raise StorageError(f"Failed to save text content: {str(e)}")
    
    async def load_text(self, filepath: Union[str, Path]) -> str:
        """Load content from text file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found: {filepath}")
            
            def read_file():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            
            content = await asyncio.get_event_loop().run_in_executor(None, read_file)
            
            # Remove metadata header if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to load text content: {e}")
            raise StorageError(f"Failed to load text content: {str(e)}")
    
    async def list_files(
        self,
        pattern: Optional[str] = None,
        directory: Optional[str] = None
    ) -> List[Path]:
        """List files matching pattern, searching both old and new locations."""
        try:
            files = []
            
            # Search modern data directory
            search_dirs = [self.modern_data_path]
            if directory:
                search_dirs.append(self.modern_data_path / directory)
            
            # Also search old locations for backward compatibility
            search_dirs.extend([
                self.file_storage.articles_path,
                self.file_storage.docs_path
            ])
            
            def search_files():
                found_files = []
                for search_dir in search_dirs:
                    if not search_dir.exists():
                        continue
                    
                    if pattern:
                        found_files.extend(search_dir.glob(pattern))
                    else:
                        found_files.extend(search_dir.iterdir())
                
                # Remove duplicates and filter to files only
                unique_files = {}
                for f in found_files:
                    if f.is_file():
                        unique_files[f.name] = f
                
                return list(unique_files.values())
            
            files = await asyncio.get_event_loop().run_in_executor(None, search_files)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise StorageError(f"Failed to list files: {str(e)}")
    
    async def delete_file(self, filepath: Union[str, Path]) -> bool:
        """Delete a file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return False
            
            def delete_file():
                filepath.unlink()
                return True
            
            return await asyncio.get_event_loop().run_in_executor(None, delete_file)
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise StorageError(f"Failed to delete file: {str(e)}")
    
    # Legacy FileStorage compatibility methods
    async def save_generated_articles(
        self,
        articles: List[Dict[str, Any]],
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save generated articles using modern async approach."""
        try:
            # Use the sync method from FileStorage for compatibility
            def save_sync():
                return self.file_storage.save_generated_articles(articles, workflow_id)
            
            result_path = await asyncio.get_event_loop().run_in_executor(None, save_sync)
            
            # Also save to modern location
            modern_path = await self.save_json(
                {"articles": articles}, 
                "articles",
                workflow_id
            )
            
            logger.info(f"Saved articles to both legacy ({result_path}) and modern ({modern_path}) locations")
            return Path(result_path)
            
        except Exception as e:
            logger.error(f"Failed to save generated articles: {e}")
            raise StorageError(f"Failed to save generated articles: {str(e)}")
    
    async def load_generated_articles(
        self,
        workflow_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load generated articles from both old and new locations with caching."""
        try:
            # Generate cache key
            cache_key = f"articles_{workflow_id or 'all'}"
            
            # Try cache first
            if self.cache_enabled:
                cached_articles = await self.cache_service.get(cache_key, "articles")
                if cached_articles is not None:
                    logger.debug(f"Loaded articles from cache: {cache_key}")
                    return cached_articles
            
            # Load from storage
            articles = []
            
            # First try modern location
            files = await self.list_files("articles_*.json", "articles")
            
            if workflow_id:
                files = [f for f in files if workflow_id in f.name]
            
            if files:
                # Get the most recent file
                latest_file = files[0]  # Already sorted by modification time
                data = await self.load_json(latest_file)
                
                if isinstance(data, dict):
                    articles = data.get("articles", [])
                elif isinstance(data, list):
                    articles = data
            
            # Fall back to legacy method if no articles found
            if not articles:
                def load_legacy():
                    return self.file_storage.load_generated_articles(workflow_id) or []
                
                articles = await asyncio.get_event_loop().run_in_executor(None, load_legacy)
            
            # Apply deduplication if enabled
            if self.dedup_enabled and articles:
                articles = await self.deduplicator.deduplicate_articles(articles)
            
            # Cache the results
            if self.cache_enabled and articles:
                await self.cache_service.set(cache_key, articles, "articles")
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to load generated articles: {e}")
            return []
    
    def _get_modern_file_path(self, filename: str) -> Path:
        """Get file path in modern storage structure."""
        # Determine subdirectory based on filename
        if 'article' in filename.lower():
            return self.modern_data_path / "articles" / filename
        elif 'content' in filename.lower():
            return self.modern_data_path / "content" / filename
        elif 'workflow' in filename.lower():
            return self.modern_data_path / "workflows" / filename
        else:
            return self.modern_data_path / filename
    
    # Additional utility methods for article management
    async def get_latest_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent articles across all workflows."""
        try:
            articles = await self.load_generated_articles()
            
            # Sort by creation date if available
            def get_sort_key(article):
                # Try different date fields
                for field in ['created_at', 'timestamp', 'date']:
                    if field in article:
                        try:
                            return datetime.fromisoformat(article[field].replace('Z', '+00:00'))
                        except:
                            continue
                return datetime.min
            
            articles.sort(key=get_sort_key, reverse=True)
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get latest articles: {e}")
            return []
    
    async def get_articles_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get articles filtered by category."""
        try:
            articles = await self.load_generated_articles()
            return [
                article for article in articles 
                if article.get('category', '').lower() == category.lower()
            ]
            
        except Exception as e:
            logger.error(f"Failed to get articles by category: {e}")
            return []
    
    async def get_article_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored articles."""
        try:
            articles = await self.load_generated_articles()
            
            if not articles:
                return {
                    "total_articles": 0,
                    "categories": {},
                    "total_words": 0,
                    "average_words": 0
                }
            
            categories = {}
            total_words = 0
            
            for article in articles:
                category = article.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
                total_words += article.get('word_count', 0)
            
            return {
                "total_articles": len(articles),
                "categories": categories,
                "total_words": total_words,
                "average_words": total_words // len(articles) if articles else 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get article statistics: {e}")
            return {"error": str(e)}