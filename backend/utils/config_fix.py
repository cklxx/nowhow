"""
Configuration fix utilities to handle ConfigSection serialization issues.
"""

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def safe_dict_convert(obj: Any) -> Dict[str, Any]:
    """
    Safely convert ConfigSection objects to dictionaries.
    Handles the serialization error: "Cannot serialize non-str key".
    """
    if obj is None:
        return {}
    
    # If already a regular dict, return as-is
    if isinstance(obj, dict):
        return obj
    
    # Handle ConfigSection objects
    if hasattr(obj, 'to_dict'):
        try:
            return obj.to_dict()
        except Exception as e:
            logger.warning(f"Failed to use to_dict() method: {e}")
    
    # Fallback: extract attributes manually
    if hasattr(obj, '__dict__'):
        try:
            result = {}
            for key, value in obj.__dict__.items():
                # Skip private attributes and methods
                if key.startswith('_'):
                    continue
                    
                # Only include serializable types
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    result[key] = value
                elif hasattr(value, '__dict__'):
                    # Recursively handle nested objects
                    result[key] = safe_dict_convert(value)
                else:
                    # Convert to string as fallback
                    try:
                        result[key] = str(value)
                    except Exception:
                        logger.warning(f"Skipping non-serializable attribute: {key}")
                        continue
            
            return result
        except Exception as e:
            logger.error(f"Failed to convert object to dict: {e}")
            return {}
    
    # Final fallback: try to convert directly
    try:
        return dict(obj)
    except Exception as e:
        logger.error(f"Unable to convert object to dict: {e}")
        return {}


def safe_headers_extract(config_obj: Any) -> Dict[str, str]:
    """
    Safely extract headers from configuration object.
    Returns a valid headers dictionary for HTTP requests.
    """
    headers = safe_dict_convert(config_obj)
    
    # Ensure all header values are strings
    string_headers = {}
    for key, value in headers.items():
        if isinstance(key, str) and value is not None:
            string_headers[key] = str(value)
    
    # Set default User-Agent if not present
    if 'User-Agent' not in string_headers:
        string_headers['User-Agent'] = 'Mozilla/5.0 (compatible; AI-Content-Aggregator/1.0)'
    
    return string_headers


def fix_config_serialization(config_section: Any) -> Dict[str, Any]:
    """
    Fix ConfigSection serialization for JSON encoding.
    This addresses the core issue causing crawl failures.
    """
    if config_section is None:
        return {}
    
    return safe_dict_convert(config_section)