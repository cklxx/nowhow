"""
Modern crawler agent using cutting-edge open source tools (2024).
Integrates Firecrawl, Crawl4AI, and Playwright with intelligent fallbacks.
"""

import asyncio
import os
from typing import Dict, List, Any
from datetime import datetime
from langchain_core.messages import HumanMessage

from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage
from services.modern_crawler_service import ModernCrawlerService
from config import get_settings


class ModernCrawlerAgent(BaseAgent):
    """Modern crawler agent using 2024's best open source scraping tools"""
    
    def __init__(self, firecrawl_api_key: str = None):
        super().__init__("ModernCrawlerAgent")
        self.file_storage = FileStorage()
        self.settings = get_settings()
        
        # Get Firecrawl API key from environment or parameter
        self.firecrawl_api_key = firecrawl_api_key or os.getenv('FIRECRAWL_API_KEY')
        
        if self.firecrawl_api_key:
            print("🔥 Firecrawl API key detected - premium extraction enabled")
        else:
            print("⚠️  No Firecrawl API key - using open source tools only")
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute modern crawling with intelligent tool selection"""
        try:
            state.current_step = "modern_crawling"
            
            # Initialize progress tracking
            state.progress = {
                "current_step": "modern_crawling",
                "status": "starting",
                "tools_available": self._check_tool_availability(),
                "sources_processed": 0,
                "total_sources": 0,
                "current_source": "",
                "extraction_methods": [],
                "performance_stats": {}
            }
            
            print("🚀 Starting Modern AI Content Crawling")
            print("=" * 60)
            print("🔧 Available Tools:")
            for tool, available in state.progress["tools_available"].items():
                status = "✅" if available else "❌"
                print(f"   {status} {tool}")
            print("=" * 60)
            
            start_time = datetime.now()
            
            # Use modern crawler service
            async with ModernCrawlerService(self.settings, self.firecrawl_api_key) as crawler:
                
                # Update progress
                state.progress["status"] = "crawling"
                
                # Crawl premium sources with modern tools
                crawling_results = await crawler.crawl_premium_sources()
                
                # Update progress with results
                state.progress.update({
                    "status": "completed",
                    "sources_processed": crawling_results["stats"]["total_sources"],
                    "total_sources": crawling_results["stats"]["total_sources"],
                    "extraction_methods": crawling_results["tools_used"],
                    "performance_stats": crawling_results["stats"]["by_tool"]
                })
                
                # Calculate performance metrics
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                total_items = crawling_results["stats"]["total_items"]
                success_rate = crawling_results["stats"]["successful"] / max(crawling_results["stats"]["total_sources"], 1)
                
                print("🎉 Modern Crawling Results:")
                print(f"   📊 Success Rate: {success_rate:.1%}")
                print(f"   📈 Total Items: {total_items}")
                print(f"   ⏱️  Duration: {duration:.1f}s")
                print(f"   🔧 Methods Used: {', '.join(crawling_results['tools_used'])}")
                
                # Display tool performance
                if crawling_results["stats"]["by_tool"]:
                    print("   🏆 Tool Performance:")
                    for tool, count in crawling_results["stats"]["by_tool"].items():
                        if count > 0:
                            print(f"      • {tool}: {count} uses")
                
                # Enhanced content structure
                enhanced_content = {
                    "rss_content": crawling_results["rss_articles"],
                    "web_content": crawling_results["web_pages"],
                    "crawl_timestamp": end_time.timestamp(),
                    "progress": state.progress,
                    "stats": {
                        **crawling_results["stats"],
                        "duration_seconds": duration,
                        "items_per_second": total_items / max(duration, 0.1),
                        "success_rate": success_rate
                    },
                    "metadata": {
                        "crawler_version": "modern_v1.0",
                        "tools_used": crawling_results["tools_used"],
                        "extraction_quality": self._calculate_overall_quality(crawling_results),
                        "source_details": crawling_results["source_details"]
                    }
                }
                
                state.data["crawled_content"] = enhanced_content
                
                # Save crawled content to file
                workflow_id = state.data.get("workflow_id", "default")
                saved_path = self.file_storage.save_crawled_content(enhanced_content, workflow_id)
                state.data["crawled_content_file"] = saved_path
                
                # Create success message
                success_msg = (
                    f"Modern crawling completed: {total_items} items from "
                    f"{crawling_results['stats']['successful']}/{crawling_results['stats']['total_sources']} sources "
                    f"using {', '.join(crawling_results['tools_used'])}"
                )
                
                state.messages.append(HumanMessage(content=success_msg))
                
                print("=" * 60)
                print("✅ Modern crawler agent execution completed successfully!")
                
                return state
                
        except Exception as e:
            error_msg = f"Modern crawler error: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            
            # Update progress with error
            if hasattr(state, 'progress'):
                state.progress["status"] = "failed"
                state.progress["error"] = error_msg
            
            return state
    
    def _check_tool_availability(self) -> Dict[str, bool]:
        """Check availability of modern scraping tools"""
        availability = {}
        
        # Check Firecrawl
        availability["Firecrawl"] = bool(self.firecrawl_api_key)
        
        # Check Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            availability["Crawl4AI"] = True
        except ImportError:
            availability["Crawl4AI"] = False
        
        # Check Playwright
        try:
            from playwright.async_api import async_playwright
            availability["Playwright"] = True
        except ImportError:
            availability["Playwright"] = False
        
        # Fallback is always available
        availability["Fallback (aiohttp + BeautifulSoup)"] = True
        
        return availability
    
    def _calculate_overall_quality(self, results: Dict[str, Any]) -> float:
        """Calculate overall extraction quality score"""
        total_score = 0
        total_items = 0
        
        # Calculate from RSS articles
        for article in results.get("rss_articles", []):
            quality = article.get("quality_score", 0.5)
            total_score += quality
            total_items += 1
        
        # Calculate from web pages
        for page in results.get("web_pages", []):
            quality = page.get("quality_score", 0.5)
            total_score += quality
            total_items += 1
        
        # Weight by extraction method
        method_weights = {
            "firecrawl": 1.2,
            "crawl4ai": 1.1,
            "playwright": 1.0,
            "fallback": 0.8
        }
        
        # Apply method weighting
        weighted_score = 0
        for item in results.get("rss_articles", []) + results.get("web_pages", []):
            method = item.get("extraction_method", "fallback")
            weight = method_weights.get(method, 1.0)
            quality = item.get("quality_score", 0.5)
            weighted_score += quality * weight
        
        if total_items == 0:
            return 0.0
        
        # Normalize weighted score
        max_possible_score = total_items * 1.2  # Max weight is 1.2
        normalized_score = weighted_score / max_possible_score
        
        return min(1.0, normalized_score)
    
    def get_tool_recommendations(self) -> Dict[str, str]:
        """Get recommendations for setting up missing tools"""
        recommendations = {}
        
        availability = self._check_tool_availability()
        
        if not availability.get("Firecrawl", False):
            recommendations["Firecrawl"] = (
                "Get API key from https://firecrawl.dev for premium AI-ready extraction. "
                "Set FIRECRAWL_API_KEY environment variable."
            )
        
        if not availability.get("Crawl4AI", False):
            recommendations["Crawl4AI"] = (
                "Install with: pip install crawl4ai. "
                "Excellent for LLM-ready content extraction."
            )
        
        if not availability.get("Playwright", False):
            recommendations["Playwright"] = (
                "Install with: pip install playwright && playwright install. "
                "Required for dynamic JavaScript content."
            )
        
        return recommendations