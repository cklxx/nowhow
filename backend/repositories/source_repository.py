"""
Source repository implementation for managing content sources.
"""

import uuid
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from config import Settings
from core.interfaces import ISourceRepository, IStorageService
from core.exceptions import SourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class JsonSourceRepository(ISourceRepository):
    """JSON file-based source repository implementation."""
    
    def __init__(self, settings: Settings, storage_service: IStorageService):
        self.settings = settings
        self.storage = storage_service
        self.config = settings.services.sources
        self._sources_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes
    
    async def _load_sources(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load sources from storage with caching."""
        try:
            # Check cache validity
            if (not force_reload and 
                self._sources_cache is not None and 
                self._cache_timestamp is not None and
                (datetime.now() - self._cache_timestamp).seconds < self._cache_ttl):
                return self._sources_cache
            
            # Try to load from file
            try:
                sources = await self.storage.load_json(self.config.config_file)
                if not isinstance(sources, list):
                    sources = []
            except Exception as e:
                logger.warning(f"Could not load sources file: {e}")
                sources = []
            
            # Validate and update cache
            self._sources_cache = sources
            self._cache_timestamp = datetime.now()
            
            return sources
            
        except Exception as e:
            logger.error(f"Failed to load sources: {e}")
            return []
    
    async def _save_sources(self, sources: List[Dict[str, Any]]) -> None:
        """Save sources to storage."""
        try:
            # Create backup if enabled
            if self.config.auto_backup:
                try:
                    await self.storage.backup_file(self.config.config_file)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            # Save sources
            await self.storage.save_json(sources, self.config.config_file)
            
            # Update cache
            self._sources_cache = sources
            self._cache_timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to save sources: {e}")
            raise
    
    def _validate_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate source data."""
        if not self.config.validation:
            return source_data
        
        required_fields = ['name', 'url', 'type']
        for field in required_fields:
            if field not in source_data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate URL format
        url = source_data['url']
        if not url.startswith(('http://', 'https://')):
            raise ValidationError(f"Invalid URL format: {url}")
        
        # Validate type
        valid_types = ['rss', 'html', 'api', 'json']
        source_type = source_data['type']
        if source_type not in valid_types:
            raise ValidationError(f"Invalid source type: {source_type}. Must be one of: {valid_types}")
        
        # Validate category if provided
        if 'category' in source_data:
            category = source_data['category']
            if self.config.categories and category not in self.config.categories:
                logger.warning(f"Category '{category}' not in configured categories")
        
        return source_data
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all sources."""
        return await self._load_sources()
    
    async def get_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source by ID."""
        sources = await self._load_sources()
        
        for source in sources:
            if source.get('id') == source_id:
                return source
        
        return None
    
    async def create(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new source."""
        try:
            # Validate source data
            validated_data = self._validate_source(source_data)
            
            # Generate ID if not provided
            if 'id' not in validated_data:
                validated_data['id'] = str(uuid.uuid4())
            
            # Add metadata
            validated_data.update({
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': 'active'
            })
            
            # Load current sources and add new one
            sources = await self._load_sources()
            
            # Check for duplicate ID
            if any(s.get('id') == validated_data['id'] for s in sources):
                raise ValidationError(f"Source with ID {validated_data['id']} already exists")
            
            sources.append(validated_data)
            
            # Save updated sources
            await self._save_sources(sources)
            
            logger.info(f"Created new source: {validated_data['id']}")
            return validated_data
            
        except Exception as e:
            logger.error(f"Failed to create source: {e}")
            raise
    
    async def update(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing source."""
        try:
            sources = await self._load_sources()
            
            # Find source to update
            source_index = None
            for i, source in enumerate(sources):
                if source.get('id') == source_id:
                    source_index = i
                    break
            
            if source_index is None:
                raise SourceNotFoundError(f"Source not found: {source_id}")
            
            # Preserve ID and creation time
            existing_source = sources[source_index]
            updated_data = {
                **source_data,
                'id': source_id,
                'created_at': existing_source.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            # Validate updated data
            validated_data = self._validate_source(updated_data)
            
            # Update source
            sources[source_index] = validated_data
            
            # Save updated sources
            await self._save_sources(sources)
            
            logger.info(f"Updated source: {source_id}")
            return validated_data
            
        except Exception as e:
            logger.error(f"Failed to update source: {e}")
            raise
    
    async def delete(self, source_id: str) -> bool:
        """Delete source."""
        try:
            sources = await self._load_sources()
            
            # Find and remove source
            original_count = len(sources)
            sources = [s for s in sources if s.get('id') != source_id]
            
            if len(sources) == original_count:
                raise SourceNotFoundError(f"Source not found: {source_id}")
            
            # Save updated sources
            await self._save_sources(sources)
            
            logger.info(f"Deleted source: {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete source: {e}")
            raise
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get sources by category."""
        sources = await self._load_sources()
        
        return [
            source for source in sources
            if source.get('category') == category
        ]
    
    async def get_by_type(self, source_type: str) -> List[Dict[str, Any]]:
        """Get sources by type."""
        sources = await self._load_sources()
        
        return [
            source for source in sources
            if source.get('type') == source_type
        ]
    
    async def get_active_sources(self) -> List[Dict[str, Any]]:
        """Get only active sources."""
        sources = await self._load_sources()
        
        return [
            source for source in sources
            if source.get('status', 'active') == 'active'
        ]
    
    async def search_sources(self, query: str) -> List[Dict[str, Any]]:
        """Search sources by name, URL, or description."""
        sources = await self._load_sources()
        query = query.lower()
        
        matching_sources = []
        for source in sources:
            # Search in name, URL, and description
            searchable_text = ' '.join([
                source.get('name', ''),
                source.get('url', ''),
                source.get('description', ''),
                source.get('category', ''),
                source.get('type', '')
            ]).lower()
            
            if query in searchable_text:
                matching_sources.append(source)
        
        return matching_sources
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories from sources."""
        sources = await self._load_sources()
        
        categories = set()
        for source in sources:
            if 'category' in source and source['category']:
                categories.add(source['category'])
        
        return sorted(list(categories))
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        sources = await self._load_sources()
        
        stats = {
            'total_sources': len(sources),
            'active_sources': len([s for s in sources if s.get('status') == 'active']),
            'inactive_sources': len([s for s in sources if s.get('status') != 'active']),
            'by_type': {},
            'by_category': {},
            'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }
        
        # Count by type
        for source in sources:
            source_type = source.get('type', 'unknown')
            stats['by_type'][source_type] = stats['by_type'].get(source_type, 0) + 1
        
        # Count by category
        for source in sources:
            category = source.get('category', 'uncategorized')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats