#!/usr/bin/env python3
"""
Test configuration and fixtures for backend tests.
"""

import sys
import os
import pytest
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

@pytest.fixture
def settings():
    """Get test settings configuration."""
    from config import get_settings
    return get_settings()

@pytest.fixture 
def container():
    """Get dependency injection container."""
    from core import get_container
    return get_container()

@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return os.getenv('ARK_API_KEY', 'test_api_key')

@pytest.fixture
def test_data_dir():
    """Test data directory path."""
    return backend_dir / "data"