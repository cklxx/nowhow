#!/usr/bin/env python3
"""
Storage service tests including enhanced storage functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta


class TestBasicStorage:
    """Test basic storage operations."""
    
    @pytest.mark.asyncio
    async def test_storage_service_creation(self, container):
        """Test storage service creation."""
        storage = container.storage_service
        assert storage is not None
        
    @pytest.mark.asyncio
    async def test_file_save_and_load(self, container):
        """Test basic file save and load operations."""
        storage = container.storage_service
        
        # Test data
        test_data = {
            "test": "data",
            "timestamp": datetime.now().isoformat()
        }
        
        # Save data
        filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        await storage.save_json(test_data, filename)
        
        # Load data back
        loaded_data = await storage.load_json(filename)
        assert loaded_data["test"] == test_data["test"]


class TestEnhancedStorage:
    """Test enhanced storage with merging capabilities."""
    
    @pytest.fixture
    async def storage_with_test_data(self, container):
        """Create storage service with test data."""
        storage = container.enhanced_storage_service
        
        # Create test articles files
        for i in range(3):
            timestamp = datetime.now() - timedelta(days=i)
            workflow_id = f"test_workflow_{i}"
            
            articles_data = {
                "metadata": {
                    "workflow_id": workflow_id,
                    "created_at": timestamp.isoformat(),
                    "total_articles": 2
                },
                "articles": [
                    {
                        "id": f"article_{i}_1",
                        "title": f"Test Article {i}-1: AI Developments",
                        "content": f"This is test article {i}-1 about AI developments.",
                        "category": "AI Research",
                        "created_at": timestamp.isoformat(),
                        "word_count": 50 + i * 10
                    },
                    {
                        "id": f"article_{i}_2", 
                        "title": f"Test Article {i}-2: ML Applications",
                        "content": f"This is test article {i}-2 about ML applications.",
                        "category": "Machine Learning",
                        "created_at": timestamp.isoformat(),
                        "word_count": 60 + i * 10
                    }
                ]
            }
            
            await storage.save_json(
                articles_data,
                f"articles_{timestamp.strftime('%Y%m%d_%H%M%S')}_{workflow_id}.json"
            )
        
        return storage
    
    @pytest.mark.asyncio
    async def test_enhanced_storage_creation(self, container):
        """Test enhanced storage service creation."""
        storage = container.enhanced_storage_service
        assert storage is not None
        
    @pytest.mark.asyncio
    async def test_load_and_merge_files(self, storage_with_test_data):
        """Test file merging functionality."""
        storage = await storage_with_test_data
        
        # Test merging articles
        result = await storage.load_and_merge_files(
            pattern="articles_*.json",
            content_type="articles",
            limit=5
        )
        
        assert "merged_data" in result
        assert "metadata" in result
        assert len(result["merged_data"]) > 0
        assert result["metadata"]["total_files"] > 0
        
    @pytest.mark.asyncio
    async def test_load_latest_by_type(self, storage_with_test_data):
        """Test loading latest content by type."""
        storage = await storage_with_test_data
        
        result = await storage.load_latest_by_type(
            content_type="articles",
            limit=3
        )
        
        assert "merged_data" in result
        assert "metadata" in result
        assert len(result["merged_data"]) <= 6  # 3 files * 2 articles each
        
    @pytest.mark.asyncio
    async def test_content_statistics(self, storage_with_test_data):
        """Test content statistics generation."""
        storage = await storage_with_test_data
        
        stats = await storage.get_content_statistics()
        
        assert "files_by_type" in stats
        assert "total_size" in stats
        assert "content_counts" in stats
        assert stats["total_size"] > 0
        
    @pytest.mark.asyncio
    async def test_aggregate_by_timeframe(self, storage_with_test_data):
        """Test time-based aggregation."""
        storage = await storage_with_test_data
        
        result = await storage.aggregate_by_timeframe(
            content_type="articles",
            timeframe="daily",
            limit=7
        )
        
        assert "periods" in result
        assert "metadata" in result
        assert len(result["periods"]) >= 0


class TestStorageErrorHandling:
    """Test storage error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, container):
        """Test loading a file that doesn't exist."""
        storage = container.storage_service
        
        with pytest.raises(Exception):
            await storage.load_json("nonexistent_file.json")
    
    @pytest.mark.asyncio
    async def test_invalid_pattern_merging(self, container):
        """Test merging with invalid patterns."""
        storage = container.enhanced_storage_service
        
        result = await storage.load_and_merge_files(
            pattern="invalid_pattern_*.json",
            content_type="articles",
            limit=5
        )
        
        # Should return empty result without error
        assert result["merged_data"] == []
        assert result["metadata"]["total_files"] == 0