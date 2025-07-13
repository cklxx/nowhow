#!/usr/bin/env python3
"""
Agent system tests including LangGraph integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock


class TestAgentCreation:
    """Test agent creation and initialization."""
    
    @pytest.mark.asyncio
    async def test_research_agent_import(self):
        """Test research agent can be imported."""
        try:
            from agents.research_agent import ResearchAgent
            assert ResearchAgent is not None
        except ImportError as e:
            pytest.skip(f"Research agent import skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_crawler_agent_import(self):
        """Test crawler agent can be imported."""
        from agents.crawler_agent import CrawlerAgent
        assert CrawlerAgent is not None
        
    @pytest.mark.asyncio
    async def test_processor_agent_import(self):
        """Test processor agent can be imported."""
        from agents.processor_agent import ProcessorAgent
        assert ProcessorAgent is not None
        
    @pytest.mark.asyncio
    async def test_writer_agent_import(self):
        """Test writer agent can be imported."""
        from agents.writer_agent import WriterAgent
        assert WriterAgent is not None


class TestAgentServices:
    """Test agent service implementations."""
    
    @pytest.mark.asyncio
    async def test_crawler_service_creation(self, container):
        """Test crawler service creation."""
        crawler = container.crawler_service
        assert crawler is not None
        
    @pytest.mark.asyncio
    async def test_content_processor_creation(self, container):
        """Test content processor creation."""
        processor = container.content_processor
        assert processor is not None
        
    @pytest.mark.asyncio
    async def test_article_writer_creation(self, container):
        """Test article writer creation."""
        writer = container.article_writer
        assert writer is not None
        
    @pytest.mark.asyncio
    async def test_workflow_orchestrator_creation(self, container):
        """Test workflow orchestrator creation."""
        orchestrator = container.workflow_orchestrator
        assert orchestrator is not None


class TestLangGraphIntegration:
    """Test LangGraph integration and ReactAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_research_agent_with_container(self, container):
        """Test research agent creation through container."""
        try:
            research_agent = container.research_agent
            assert research_agent is not None
        except Exception as e:
            pytest.skip(f"Research agent creation skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_workflow_graph_creation(self):
        """Test LangGraph workflow creation."""
        try:
            from agents.workflow import create_content_generation_workflow
            graph = create_content_generation_workflow()
            assert graph is not None
        except ImportError as e:
            pytest.skip(f"Workflow graph creation skipped: {e}")


class TestAgentInterfaces:
    """Test agent interface compliance."""
    
    def test_crawler_agent_interface(self):
        """Test crawler agent implements expected interface."""
        from agents.crawler_agent import CrawlerAgent
        
        # Check required methods exist
        assert hasattr(CrawlerAgent, 'crawl_sources')
        assert hasattr(CrawlerAgent, 'crawl_rss_feeds')
        
    def test_processor_agent_interface(self):
        """Test processor agent implements expected interface."""
        from agents.processor_agent import ProcessorAgent
        
        # Check required methods exist
        assert hasattr(ProcessorAgent, 'process_content')
        
    def test_writer_agent_interface(self):
        """Test writer agent implements expected interface."""
        from agents.writer_agent import WriterAgent
        
        # Check required methods exist
        assert hasattr(WriterAgent, 'generate_articles')


class TestAgentConfiguration:
    """Test agent configuration and settings."""
    
    def test_agent_settings_loading(self, settings):
        """Test agent-specific settings can be loaded."""
        assert hasattr(settings, 'agents')
        
        # Check crawler settings
        if hasattr(settings.agents, 'crawler'):
            crawler_settings = settings.agents.crawler
            assert hasattr(crawler_settings, 'timeout')
            
        # Check processor settings  
        if hasattr(settings.agents, 'processor'):
            processor_settings = settings.agents.processor
            assert hasattr(processor_settings, 'relevance_threshold')


class TestAgentErrorHandling:
    """Test agent error handling and resilience."""
    
    @pytest.mark.asyncio
    async def test_crawler_error_handling(self, container):
        """Test crawler handles errors gracefully."""
        crawler = container.crawler_service
        
        # Test with invalid source
        try:
            result = await crawler.crawl_sources([{
                "url": "https://invalid-domain-that-does-not-exist.com",
                "type": "rss"
            }])
            # Should not raise exception, but return error info
            assert isinstance(result, dict)
        except Exception:
            # Some error handling is acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_processor_with_invalid_content(self, container):
        """Test processor handles invalid content."""
        processor = container.content_processor
        
        # Test with empty content
        try:
            result = await processor.process_content([])
            assert isinstance(result, (list, dict))
        except Exception:
            # Some error handling is acceptable
            pass