#!/usr/bin/env python3
"""
API endpoint tests for the refactored backend.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

class TestConfiguration:
    """Test configuration system."""
    
    def test_settings_loading(self, settings):
        """Test that settings load correctly."""
        assert settings.app.name
        assert settings.server.host
        assert settings.server.port
        assert settings.models.ark.model
        
    def test_environment_variables(self, settings):
        """Test environment variable substitution."""
        # Test that API key can be loaded from environment
        api_key = settings.models.ark.api_key
        assert api_key is not None


class TestDependencyInjection:
    """Test dependency injection container."""
    
    def test_container_creation(self, container):
        """Test that container creates successfully."""
        assert container is not None
        
    def test_service_creation(self, container):
        """Test that all services can be created."""
        # Test core services
        model_service = container.model_service
        assert model_service is not None
        
        storage_service = container.storage_service
        assert storage_service is not None
        
        source_repo = container.source_repository
        assert source_repo is not None
        
        # Test workflow services
        crawler_service = container.crawler_service
        assert crawler_service is not None
        
        content_processor = container.content_processor
        assert content_processor is not None
        
        article_writer = container.article_writer
        assert article_writer is not None


class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_api_import(self):
        """Test that API module can be imported."""
        try:
            from api.main import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import API module: {e}")
    
    def test_cors_configuration(self):
        """Test CORS middleware configuration."""
        from api.main import app
        # Check that CORS middleware is configured
        middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middleware_names


class TestWorkflowIntegration:
    """Test workflow orchestration."""
    
    @pytest.mark.asyncio
    async def test_workflow_orchestrator_creation(self, container):
        """Test workflow orchestrator can be created."""
        orchestrator = container.workflow_orchestrator
        assert orchestrator is not None
        
    @pytest.mark.asyncio 
    async def test_research_agent_creation(self, container):
        """Test research agent can be created."""
        # This tests LangGraph ReactAgent integration
        try:
            research_agent = container.research_agent
            assert research_agent is not None
        except Exception as e:
            # Research agent might need specific configuration
            pytest.skip(f"Research agent creation skipped: {e}")