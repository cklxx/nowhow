"""
Authentication service implementation for finding and managing auth configurations.
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
from urllib.parse import urlparse

from config import Settings
from core.interfaces import IAuthService
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class MockAuthService(IAuthService):
    """Mock authentication service for development and testing."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.services.auth
        
        # Mock auth configurations for development
        self._mock_auths = {
            "reddit.com": {
                "type": "bearer_token",
                "token": "mock_reddit_token",
                "description": "Reddit API access"
            },
            "github.com": {
                "type": "bearer_token", 
                "token": "mock_github_token",
                "description": "GitHub API access"
            },
            "newsapi.org": {
                "type": "api_key",
                "key": "mock_newsapi_key",
                "header": "X-API-Key",
                "description": "News API access"
            },
            "example-premium.com": {
                "type": "basic",
                "username": "mock_user",
                "password": "mock_pass",
                "description": "Basic auth example"
            }
        }
    
    async def find_auth_for_source(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Find authentication configuration for source."""
        try:
            if not self.config.mock_enabled:
                return None
            
            # Parse URL to get domain
            parsed_url = urlparse(source_url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Look for exact domain match first
            if domain in self._mock_auths:
                auth_config = self._mock_auths[domain].copy()
                logger.info(f"Found auth config for {domain}: {auth_config['type']}")
                return auth_config
            
            # Look for subdomain matches
            for auth_domain, auth_config in self._mock_auths.items():
                if domain.endswith(auth_domain):
                    logger.info(f"Found auth config for {domain} via {auth_domain}: {auth_config['type']}")
                    return auth_config.copy()
            
            logger.debug(f"No auth configuration found for {domain}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding auth for {source_url}: {e}")
            return None
    
    async def validate_auth(self, auth_config: Dict[str, Any]) -> bool:
        """Validate authentication configuration."""
        try:
            auth_type = auth_config.get('type', '')
            
            if auth_type not in self.config.supported_methods:
                logger.error(f"Unsupported auth type: {auth_type}")
                return False
            
            # Validate required fields based on auth type
            if auth_type == 'bearer_token':
                return 'token' in auth_config and auth_config['token']
            elif auth_type == 'api_key':
                return 'key' in auth_config and auth_config['key']
            elif auth_type == 'basic':
                return ('username' in auth_config and 
                       'password' in auth_config and
                       auth_config['username'] and 
                       auth_config['password'])
            
            return False
            
        except Exception as e:
            logger.error(f"Auth validation failed: {e}")
            return False
    
    async def add_auth_config(
        self,
        domain: str,
        auth_config: Dict[str, Any]
    ) -> bool:
        """Add new auth configuration."""
        try:
            if not await self.validate_auth(auth_config):
                raise AuthenticationError("Invalid auth configuration")
            
            self._mock_auths[domain.lower()] = auth_config
            logger.info(f"Added auth config for {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add auth config: {e}")
            return False
    
    async def remove_auth_config(self, domain: str) -> bool:
        """Remove auth configuration."""
        try:
            domain = domain.lower()
            if domain in self._mock_auths:
                del self._mock_auths[domain]
                logger.info(f"Removed auth config for {domain}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove auth config: {e}")
            return False
    
    async def list_auth_configs(self) -> List[Dict[str, Any]]:
        """List all auth configurations."""
        try:
            configs = []
            for domain, config in self._mock_auths.items():
                # Return safe version without credentials
                safe_config = {
                    "domain": domain,
                    "type": config.get('type', ''),
                    "description": config.get('description', ''),
                    "has_credentials": bool(
                        config.get('token') or 
                        config.get('key') or 
                        (config.get('username') and config.get('password'))
                    )
                }
                configs.append(safe_config)
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to list auth configs: {e}")
            return []
    
    async def test_auth_config(
        self,
        domain: str,
        test_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test auth configuration."""
        try:
            auth_config = await self.find_auth_for_source(f"https://{domain}")
            
            if not auth_config:
                return {
                    "success": False,
                    "message": f"No auth config found for {domain}"
                }
            
            if not await self.validate_auth(auth_config):
                return {
                    "success": False,
                    "message": "Auth config validation failed"
                }
            
            # For mock service, simulate success
            return {
                "success": True,
                "message": f"Mock auth test passed for {domain}",
                "auth_type": auth_config.get('type', ''),
                "tested_at": "mock_timestamp"
            }
            
        except Exception as e:
            logger.error(f"Auth test failed: {e}")
            return {
                "success": False,
                "message": f"Auth test error: {str(e)}"
            }