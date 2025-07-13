"""
Configuration management module for the AI Content Aggregator.

This module provides centralized configuration management with support for:
- YAML configuration files
- Environment variable substitution
- Validation and type checking
- Configuration hot-reloading
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]