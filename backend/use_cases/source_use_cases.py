"""
Source management use cases implementation.
High cohesion: All source-related business logic in one place.
Low coupling: Only depends on abstractions, not concrete implementations.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.clean_architecture import (
    Source, SourceType, SourceUseCases, SourceRepository, Result
)


class SourceUseCasesImpl(SourceUseCases):
    """Source use cases implementation following clean architecture"""
    
    def __init__(self, source_repository: SourceRepository):
        self._source_repository = source_repository
    
    async def create_source(self, source_data: Dict[str, Any]) -> Source:
        """Create a new source with validation"""
        # Validate required fields
        required_fields = ['name', 'url', 'type']
        for field in required_fields:
            if field not in source_data or not source_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate source type
        try:
            source_type = SourceType(source_data['type'])
        except ValueError:
            raise ValueError(f"Invalid source type: {source_data['type']}")
        
        # Validate URL format
        url = source_data['url'].strip()
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Create source entity
        source = Source(
            id=str(uuid.uuid4()),
            name=source_data['name'].strip(),
            url=url,
            type=source_type,
            category=source_data.get('category', 'general').strip(),
            active=source_data.get('active', True),
            created_at=datetime.now(),
            metadata=source_data.get('metadata', {})
        )
        
        # Save to repository
        return await self._source_repository.save(source)
    
    async def get_source(self, source_id: str) -> Optional[Source]:
        """Get source by ID"""
        if not source_id or not source_id.strip():
            raise ValueError("Source ID is required")
        
        return await self._source_repository.find_by_id(source_id.strip())
    
    async def list_sources(self, active_only: bool = True) -> List[Source]:
        """List all sources"""
        return await self._source_repository.find_all(active_only)
    
    async def update_source(self, source_id: str, updates: Dict[str, Any]) -> Source:
        """Update existing source"""
        if not source_id or not source_id.strip():
            raise ValueError("Source ID is required")
        
        # Get existing source
        source = await self._source_repository.find_by_id(source_id.strip())
        if not source:
            raise ValueError(f"Source not found: {source_id}")
        
        # Apply updates with validation
        if 'name' in updates and updates['name']:
            source.name = updates['name'].strip()
        
        if 'url' in updates and updates['url']:
            url = updates['url'].strip()
            if not url.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")
            source.url = url
        
        if 'type' in updates:
            try:
                source.type = SourceType(updates['type'])
            except ValueError:
                raise ValueError(f"Invalid source type: {updates['type']}")
        
        if 'category' in updates:
            source.category = updates['category'].strip() if updates['category'] else 'general'
        
        if 'active' in updates:
            source.active = bool(updates['active'])
        
        if 'metadata' in updates and isinstance(updates['metadata'], dict):
            source.metadata.update(updates['metadata'])
        
        # Save updated source
        return await self._source_repository.update(source)
    
    async def delete_source(self, source_id: str) -> bool:
        """Delete source"""
        if not source_id or not source_id.strip():
            raise ValueError("Source ID is required")
        
        return await self._source_repository.delete(source_id.strip())
    
    async def get_sources_by_category(self, category: str) -> List[Source]:
        """Get sources by category"""
        if not category or not category.strip():
            raise ValueError("Category is required")
        
        return await self._source_repository.find_by_category(category.strip())
    
    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get source statistics"""
        all_sources = await self._source_repository.find_all(active_only=False)
        active_sources = [s for s in all_sources if s.active]
        
        # Count by category
        categories = {}
        for source in active_sources:
            category = source.category or 'general'
            categories[category] = categories.get(category, 0) + 1
        
        # Count by type
        types = {}
        for source in active_sources:
            source_type = source.type.value
            types[source_type] = types.get(source_type, 0) + 1
        
        return {
            'total_sources': len(all_sources),
            'active_sources': len(active_sources),
            'inactive_sources': len(all_sources) - len(active_sources),
            'categories': categories,
            'types': types,
            'last_updated': datetime.now().isoformat()
        }
    
    async def validate_source_data(self, source_data: Dict[str, Any]) -> Result:
        """Validate source data without creating"""
        try:
            # Check required fields
            required_fields = ['name', 'url', 'type']
            for field in required_fields:
                if field not in source_data or not source_data[field]:
                    return Result.error(f"Missing required field: {field}")
            
            # Validate source type
            try:
                SourceType(source_data['type'])
            except ValueError:
                return Result.error(f"Invalid source type: {source_data['type']}")
            
            # Validate URL format
            url = source_data['url'].strip()
            if not url.startswith(('http://', 'https://')):
                return Result.error("URL must start with http:// or https://")
            
            return Result.ok({"valid": True})
            
        except Exception as e:
            return Result.error(str(e))