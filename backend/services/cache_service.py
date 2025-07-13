"""
Cache service for articles and content.
"""

import json
import hashlib
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service for articles and API responses.
    Provides both in-memory and persistent caching.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, cache_ttl: int = 3600):
        # In-memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache configuration
        self.cache_ttl = cache_ttl  # Time to live in seconds
        
        # Persistent cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / "cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / "articles").mkdir(exist_ok=True)
        (self.cache_dir / "api").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
    
    def _generate_cache_key(self, data: Union[str, Dict, List]) -> str:
        """Generate cache key from data."""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True, default=str)
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - timestamp < self.cache_ttl
    
    async def get_from_memory(self, key: str) -> Optional[Any]:
        """Get item from memory cache."""
        try:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if self._is_cache_valid(entry['timestamp']):
                    logger.debug(f"Cache hit (memory): {key}")
                    return entry['data']
                else:
                    # Remove expired entry
                    del self._memory_cache[key]
                    logger.debug(f"Cache expired (memory): {key}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get from memory cache: {e}")
            return None
    
    async def set_in_memory(self, key: str, data: Any) -> bool:
        """Set item in memory cache."""
        try:
            self._memory_cache[key] = {
                'data': data,
                'timestamp': time.time()
            }
            logger.debug(f"Cache set (memory): {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set in memory cache: {e}")
            return False
    
    async def get_from_disk(self, key: str, category: str = "articles") -> Optional[Any]:
        """Get item from disk cache."""
        try:
            cache_file = self.cache_dir / category / f"{key}.json"
            
            if not cache_file.exists():
                return None
            
            def read_cache():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            cache_data = await asyncio.get_event_loop().run_in_executor(None, read_cache)
            
            if self._is_cache_valid(cache_data['timestamp']):
                logger.debug(f"Cache hit (disk): {key}")
                return cache_data['data']
            else:
                # Remove expired file
                cache_file.unlink()
                logger.debug(f"Cache expired (disk): {key}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get from disk cache: {e}")
            return None
    
    async def set_on_disk(self, key: str, data: Any, category: str = "articles") -> bool:
        """Set item in disk cache."""
        try:
            cache_file = self.cache_dir / category / f"{key}.json"
            
            cache_data = {
                'data': data,
                'timestamp': time.time(),
                'created_at': datetime.now().isoformat()
            }
            
            def write_cache():
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, default=str)
            
            await asyncio.get_event_loop().run_in_executor(None, write_cache)
            
            logger.debug(f"Cache set (disk): {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set on disk cache: {e}")
            return False
    
    async def get(self, key: str, category: str = "articles") -> Optional[Any]:
        """Get item from cache (memory first, then disk)."""
        # Try memory cache first
        data = await self.get_from_memory(key)
        if data is not None:
            return data
        
        # Try disk cache
        data = await self.get_from_disk(key, category)
        if data is not None:
            # Store in memory for faster access
            await self.set_in_memory(key, data)
            return data
        
        return None
    
    async def set(self, key: str, data: Any, category: str = "articles") -> bool:
        """Set item in both memory and disk cache."""
        try:
            # Set in memory
            await self.set_in_memory(key, data)
            
            # Set on disk
            await self.set_on_disk(key, data, category)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    async def invalidate(self, key: str, category: str = "articles") -> bool:
        """Invalidate cache entry."""
        try:
            # Remove from memory
            if key in self._memory_cache:
                del self._memory_cache[key]
            
            # Remove from disk
            cache_file = self.cache_dir / category / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            
            logger.debug(f"Cache invalidated: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    async def clear_category(self, category: str = "articles") -> bool:
        """Clear all cache entries in a category."""
        try:
            # Clear memory cache entries for this category
            keys_to_remove = []
            for key in self._memory_cache:
                if key.startswith(f"{category}_"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._memory_cache[key]
            
            # Clear disk cache
            category_dir = self.cache_dir / category
            if category_dir.exists():
                def clear_files():
                    for file in category_dir.iterdir():
                        if file.is_file():
                            file.unlink()
                
                await asyncio.get_event_loop().run_in_executor(None, clear_files)
            
            logger.info(f"Cleared cache category: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache category: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            memory_count = len(self._memory_cache)
            
            disk_stats = {}
            for category_dir in self.cache_dir.iterdir():
                if category_dir.is_dir():
                    files = list(category_dir.iterdir())
                    disk_stats[category_dir.name] = len(files)
            
            return {
                "memory_entries": memory_count,
                "disk_entries": disk_stats,
                "cache_ttl": self.cache_ttl,
                "cache_dir": str(self.cache_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


class ArticleDeduplicator:
    """
    Article deduplication service.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        import re
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        try:
            # Simple word-based similarity
            words1 = set(self._normalize_text(text1).split())
            words2 = set(self._normalize_text(text2).split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _is_duplicate(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> bool:
        """Check if two articles are duplicates."""
        try:
            # Check title similarity
            title1 = article1.get('title', '')
            title2 = article2.get('title', '')
            title_similarity = self._calculate_similarity(title1, title2)
            
            # Check content similarity
            content1 = article1.get('content', '')
            content2 = article2.get('content', '')
            content_similarity = self._calculate_similarity(content1, content2)
            
            # Consider as duplicate if either title or content is very similar
            return (title_similarity > self.similarity_threshold or 
                   content_similarity > self.similarity_threshold)
            
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}")
            return False
    
    async def deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles from a list."""
        if not articles:
            return articles
        
        try:
            unique_articles = []
            removed_count = 0
            
            for article in articles:
                is_duplicate = False
                
                for existing_article in unique_articles:
                    if self._is_duplicate(article, existing_article):
                        is_duplicate = True
                        removed_count += 1
                        logger.debug(f"Removed duplicate article: {article.get('title', 'Unknown')}")
                        break
                
                if not is_duplicate:
                    unique_articles.append(article)
            
            logger.info(f"Deduplication complete: {len(articles)} -> {len(unique_articles)} articles (removed {removed_count} duplicates)")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Failed to deduplicate articles: {e}")
            return articles
    
    async def find_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find and return duplicate articles."""
        if not articles:
            return []
        
        try:
            duplicates = []
            
            for i, article1 in enumerate(articles):
                for j, article2 in enumerate(articles[i+1:], i+1):
                    if self._is_duplicate(article1, article2):
                        duplicates.append({
                            'article1_index': i,
                            'article2_index': j,
                            'article1_title': article1.get('title', 'Unknown'),
                            'article2_title': article2.get('title', 'Unknown'),
                            'similarity': self._calculate_similarity(
                                article1.get('content', ''),
                                article2.get('content', '')
                            )
                        })
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            return []