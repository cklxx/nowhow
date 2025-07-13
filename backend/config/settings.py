"""
Fixed configuration management.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache

import yaml


class ConfigSection:
    """A section of configuration that supports dot notation access."""
    
    def __init__(self, data: Dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigSection(value))
            elif isinstance(value, list):
                # Convert list items to ConfigSection if they are dicts
                converted_list = []
                for item in value:
                    if isinstance(item, dict):
                        converted_list.append(ConfigSection(item))
                    else:
                        converted_list.append(item)
                setattr(self, key, converted_list)
            else:
                setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with default fallback."""
        return getattr(self, key, default)
    
    def __iter__(self):
        """Support iteration over configuration keys."""
        return iter(self.__dict__.keys())
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return hasattr(self, key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert back to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConfigSection):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                converted_list = []
                for item in value:
                    if isinstance(item, ConfigSection):
                        converted_list.append(item.to_dict())
                    else:
                        converted_list.append(item)
                result[key] = converted_list
            else:
                result[key] = value
        return result


class Settings:
    """Main settings class that loads and validates all configuration."""
    
    def __init__(self, config_data: Dict[str, Any] = None):
        """Initialize settings with configuration data."""
        self._config_data = config_data or {}
        
        # Create configuration sections
        for section_name, section_data in self._config_data.items():
            if isinstance(section_data, dict):
                setattr(self, section_name, ConfigSection(section_data))
            else:
                setattr(self, section_name, section_data)

    @classmethod
    def load_from_yaml(cls, config_path: str = "conf.yml") -> "Settings":
        """Load configuration from YAML file with environment variable substitution."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Substitute environment variables
        config_data = cls._substitute_env_vars(config_data)
        
        return cls(config_data)
    
    @staticmethod
    def _substitute_env_vars(data: Any) -> Any:
        """Recursively substitute environment variables in configuration data."""
        if isinstance(data, dict):
            return {k: Settings._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Settings._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Replace ${VAR_NAME} with environment variable value
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, data)
            for match in matches:
                env_value = os.getenv(match, "")
                data = data.replace(f"${{{match}}}", env_value)
            return data
        else:
            return data
    
    def get_model_config(self, model_name: str) -> ConfigSection:
        """Get model configuration by name."""
        models = getattr(self, 'models', ConfigSection({}))
        
        if not hasattr(models, model_name):
            raise ValueError(f"Unknown model: {model_name}")
        
        config = getattr(models, model_name)
        if config is None:
            raise ValueError(f"Model {model_name} is not configured")
        
        return config
    
    def get_active_model_config(self) -> ConfigSection:
        """Get the active model configuration based on analyzer service settings."""
        services = getattr(self, 'services', ConfigSection({}))
        analyzer = getattr(services, 'analyzer', ConfigSection({}))
        model_name = getattr(analyzer, 'model_config', 'ark')
        return self.get_model_config(model_name)


@lru_cache()
def get_settings(config_path: str = "conf.yml") -> Settings:
    """Get cached settings instance."""
    # Try to find config file in current directory or parent directories
    current_dir = Path.cwd()
    config_file = None
    
    # Look for config file in current directory and up to 3 parent directories
    for i in range(4):
        potential_path = current_dir / config_path
        if potential_path.exists():
            config_file = potential_path
            break
        current_dir = current_dir.parent
    
    if config_file is None:
        # Fallback to backend directory
        backend_dir = Path(__file__).parent.parent
        config_file = backend_dir / config_path
    
    return Settings.load_from_yaml(str(config_file))