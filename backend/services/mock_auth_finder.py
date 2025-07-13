import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from datetime import datetime, timedelta
import re

from .models.source_config import MockAuthRequest, MockAuthResult, AuthConfig, AuthType

class MockAuthFinder:
    """Mock认证信息查找器"""
    
    def __init__(self):
        self.github_sources = [
            "https://api.github.com/search/repositories?q=cookies+{domain}",
            "https://api.github.com/search/code?q=cookies+{domain}+extension:json",
            "https://api.github.com/search/code?q=headers+{domain}+extension:py",
        ]
        
        # 常见的mock数据源
        self.mock_sources = {
            "httpbin": "https://httpbin.org/headers",
            "postman_echo": "https://postman-echo.com/headers",
            "reqres": "https://reqres.in/api/unknown",
        }
        
        # 常见网站的已知headers配置
        self.known_configs = {
            "reddit.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                },
                "cookies": {
                    "over18": "1",
                    "reddit_session": "placeholder"
                }
            },
            "twitter.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Authorization": "Bearer placeholder_token",
                    "X-Twitter-Client-Language": "en",
                    "X-Csrf-Token": "placeholder"
                }
            },
            "linkedin.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/vnd.linkedin.normalized+json+2.1",
                    "X-Requested-With": "XMLHttpRequest"
                },
                "cookies": {
                    "li_at": "placeholder_session_token",
                    "JSESSIONID": "placeholder"
                }
            },
            "medium.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                "cookies": {
                    "uid": "placeholder",
                    "sid": "placeholder"
                }
            },
            "github.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; Research Bot)",
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": "token placeholder_github_token"
                }
            },
            "arxiv.org": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; Academic Research Bot)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            },
            "scholar.google.com": {
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9"
                },
                "cookies": {
                    "GSP": "ID=placeholder:CF=4",
                    "NID": "placeholder"
                }
            }
        }
    
    async def find_mock_auth(self, request: MockAuthRequest) -> MockAuthResult:
        """查找Mock认证配置"""
        domain = request.site_domain.lower()
        
        # 1. 检查已知配置
        known_config = self._check_known_configs(domain)
        if known_config:
            return MockAuthResult(
                found=True,
                auth_config=known_config,
                sources=["内置配置"],
                confidence=0.9,
                last_updated=datetime.now(),
                usage_notes="使用内置的已知配置，请替换placeholder值"
            )
        
        # 2. 搜索GitHub
        github_results = await self._search_github(domain, request.auth_type)
        if github_results and github_results.auth_config:
            return github_results
        
        # 3. 搜索公开的mock数据
        mock_results = await self._search_mock_sources(domain)
        if mock_results and mock_results.auth_config:
            return mock_results
        
        # 4. 生成基础配置
        basic_config = self._generate_basic_config(domain, request.auth_type)
        return MockAuthResult(
            found=True,
            auth_config=basic_config,
            sources=["基础配置生成器"],
            confidence=0.5,
            usage_notes="生成的基础配置，需要手动填入真实的认证信息"
        )
    
    def _check_known_configs(self, domain: str) -> Optional[AuthConfig]:
        """检查已知配置"""
        # 检查完全匹配
        if domain in self.known_configs:
            config_data = self.known_configs[domain]
            return self._create_auth_config(config_data, "已知配置")
        
        # 检查子域名匹配
        for known_domain, config_data in self.known_configs.items():
            if domain.endswith(known_domain) or known_domain.endswith(domain):
                return self._create_auth_config(config_data, f"基于{known_domain}的配置")
        
        return None
    
    def _create_auth_config(self, config_data: Dict[str, Any], source: str) -> AuthConfig:
        """创建认证配置"""
        auth_type = AuthType.NONE
        
        if "cookies" in config_data and config_data["cookies"]:
            auth_type = AuthType.COOKIE
        elif "headers" in config_data:
            headers = config_data["headers"]
            if "Authorization" in headers:
                auth_type = AuthType.HEADER
        
        return AuthConfig(
            type=auth_type,
            cookies=config_data.get("cookies", {}),
            headers=config_data.get("headers", {}),
            mock_source=source,
            last_verified=datetime.now(),
            is_verified=False
        )
    
    async def _search_github(self, domain: str, auth_type: AuthType) -> Optional[MockAuthResult]:
        """搜索GitHub上的相关配置"""
        try:
            search_terms = [
                f"cookies {domain}",
                f"headers {domain}",
                f"{domain} spider",
                f"{domain} crawler"
            ]
            
            results = []
            for term in search_terms:
                # 模拟GitHub搜索（实际应该使用GitHub API）
                result = await self._mock_github_search(term, domain)
                if result:
                    results.append(result)
            
            if results:
                # 选择最佳结果
                best_result = max(results, key=lambda x: x.get("confidence", 0))
                auth_config = self._parse_github_result(best_result)
                
                if auth_config:
                    return MockAuthResult(
                        found=True,
                        auth_config=auth_config,
                        sources=[f"GitHub: {best_result.get('repo', 'unknown')}"],
                        confidence=best_result.get("confidence", 0.7),
                        usage_notes="来自GitHub公开仓库，请验证配置有效性"
                    )
        
        except Exception as e:
            print(f"GitHub search failed: {e}")
        
        return None
    
    async def _mock_github_search(self, term: str, domain: str) -> Optional[Dict[str, Any]]:
        """模拟GitHub搜索（实际环境中应使用真实API）"""
        # 这里模拟一些常见的搜索结果
        mock_results = {
            f"cookies {domain}": {
                "repo": f"awesome-{domain}-tools",
                "file": "config.json",
                "content": {
                    "cookies": {
                        "session_id": "placeholder_session",
                        "user_token": "placeholder_token"
                    },
                    "headers": {
                        "User-Agent": "Mozilla/5.0 Research Bot",
                        "Accept": "application/json"
                    }
                },
                "confidence": 0.8
            }
        }
        
        return mock_results.get(term)
    
    def _parse_github_result(self, result: Dict[str, Any]) -> Optional[AuthConfig]:
        """解析GitHub搜索结果"""
        try:
            content = result.get("content", {})
            
            auth_type = AuthType.NONE
            if content.get("cookies"):
                auth_type = AuthType.COOKIE
            elif content.get("headers", {}).get("Authorization"):
                auth_type = AuthType.HEADER
            
            return AuthConfig(
                type=auth_type,
                cookies=content.get("cookies", {}),
                headers=content.get("headers", {}),
                mock_source=f"GitHub: {result.get('repo', 'unknown')}",
                is_verified=False
            )
        
        except Exception as e:
            print(f"Failed to parse GitHub result: {e}")
            return None
    
    async def _search_mock_sources(self, domain: str) -> Optional[MockAuthResult]:
        """搜索公开的mock数据源"""
        try:
            # 检查是否有特定于该域的mock配置
            mock_configs = await self._fetch_domain_mock_configs(domain)
            
            if mock_configs:
                best_config = mock_configs[0]  # 选择第一个配置
                
                return MockAuthResult(
                    found=True,
                    auth_config=best_config["auth_config"],
                    sources=best_config["sources"],
                    confidence=best_config.get("confidence", 0.6),
                    usage_notes="来自公开mock数据源，建议验证后使用"
                )
        
        except Exception as e:
            print(f"Mock source search failed: {e}")
        
        return None
    
    async def _fetch_domain_mock_configs(self, domain: str) -> List[Dict[str, Any]]:
        """获取特定域名的mock配置"""
        configs = []
        
        # 基于域名特征生成配置
        if "api" in domain:
            configs.append({
                "auth_config": AuthConfig(
                    type=AuthType.HEADER,
                    headers={
                        "Authorization": "Bearer placeholder_api_token",
                        "User-Agent": "API Client/1.0",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                ),
                "sources": ["API模式生成器"],
                "confidence": 0.7
            })
        
        elif any(social in domain for social in ["twitter", "facebook", "instagram", "linkedin"]):
            configs.append({
                "auth_config": AuthConfig(
                    type=AuthType.COOKIE,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5"
                    },
                    cookies={
                        "session_token": "placeholder_session",
                        "user_id": "placeholder_user_id"
                    }
                ),
                "sources": ["社交媒体模式生成器"],
                "confidence": 0.8
            })
        
        elif any(news in domain for news in ["news", "blog", "medium", "wordpress"]):
            configs.append({
                "auth_config": AuthConfig(
                    type=AuthType.NONE,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; News Aggregator Bot)",
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9"
                    }
                ),
                "sources": ["新闻/博客模式生成器"],
                "confidence": 0.6
            })
        
        return configs
    
    def _generate_basic_config(self, domain: str, auth_type: AuthType) -> AuthConfig:
        """生成基础配置"""
        config = AuthConfig(type=auth_type)
        
        # 基础headers
        config.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # 根据认证类型添加配置
        if auth_type == AuthType.COOKIE:
            config.cookies = {
                "session_id": "placeholder_session_id",
                "user_token": "placeholder_user_token"
            }
        elif auth_type == AuthType.HEADER:
            config.headers["Authorization"] = "Bearer placeholder_token"
        elif auth_type == AuthType.TOKEN:
            config.token = "placeholder_api_token"
        
        config.mock_source = "基础配置生成器"
        config.is_verified = False
        
        return config
    
    async def verify_auth_config(self, url: str, auth_config: AuthConfig) -> Dict[str, Any]:
        """验证认证配置是否有效"""
        try:
            headers = auth_config.headers.copy()
            cookies = auth_config.cookies.copy()
            
            # 如果是placeholder值，则跳过验证
            if any("placeholder" in str(v) for v in headers.values()):
                return {
                    "valid": False,
                    "reason": "包含placeholder值，需要替换为真实认证信息",
                    "status_code": None
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    success_indicators = [
                        response.status < 400,
                        "login" not in (await response.text()).lower(),
                        "unauthorized" not in (await response.text()).lower()
                    ]
                    
                    is_valid = all(success_indicators)
                    
                    return {
                        "valid": is_valid,
                        "status_code": response.status,
                        "reason": "验证成功" if is_valid else f"HTTP {response.status} 或包含登录提示",
                        "response_size": len(await response.read())
                    }
        
        except Exception as e:
            return {
                "valid": False,
                "reason": f"验证失败: {str(e)}",
                "status_code": None
            }
    
    def get_auth_recommendations(self, domain: str) -> List[str]:
        """获取认证建议"""
        recommendations = []
        
        if any(social in domain for social in ["twitter", "facebook", "instagram"]):
            recommendations.extend([
                "社交媒体网站通常需要用户登录状态",
                "建议使用浏览器开发者工具获取真实的Cookie",
                "注意Cookie的过期时间，可能需要定期更新",
                "考虑使用官方API而非网页爬虫"
            ])
        
        elif "api" in domain:
            recommendations.extend([
                "API通常需要API Key或Bearer Token",
                "查看官方文档获取正确的认证方式",
                "注意请求限流和配额限制"
            ])
        
        elif any(news in domain for news in ["news", "blog"]):
            recommendations.extend([
                "大多数新闻/博客网站不需要认证",
                "如果遇到限制，尝试添加合适的User-Agent",
                "考虑使用RSS源代替网页抓取"
            ])
        
        else:
            recommendations.extend([
                "首先尝试不使用认证",
                "如果被阻止，检查是否需要特定的User-Agent",
                "观察网站的反爬虫机制",
                "考虑添加请求延迟避免被限制"
            ])
        
        return recommendations