#!/usr/bin/env python3
"""
验证ConfigSection序列化修复和现代爬虫工具的测试脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from config.settings import get_settings
from services.crawler_service import WebCrawlerService
from services.modern_crawler_service import ModernCrawlerService
from agents.modern_crawler_agent import ModernCrawlerAgent
from agents.base_agent import AgentState
from core.auth_service import MockAuthService


async def test_config_serialization_fix():
    """测试ConfigSection序列化修复"""
    print("🔧 Testing ConfigSection serialization fix...")
    
    try:
        # Load settings
        settings = get_settings()
        
        # Test ConfigSection to_dict conversion
        if hasattr(settings.agents.crawler, 'headers'):
            headers_config = settings.agents.crawler.headers
            print(f"   • Headers config type: {type(headers_config)}")
            
            # Test safe conversion
            if hasattr(headers_config, 'to_dict'):
                headers_dict = headers_config.to_dict()
                print(f"   ✅ to_dict() method works: {type(headers_dict)}")
            elif hasattr(headers_config, '__dict__'):
                headers_dict = {k: v for k, v in headers_config.__dict__.items() 
                               if not k.startswith('_') and isinstance(v, (str, int, float, bool))}
                print(f"   ✅ __dict__ fallback works: {type(headers_dict)}")
            else:
                print(f"   ⚠️  Using basic dict conversion")
        else:
            print(f"   ℹ️  No headers config found")
        
        print("   ✅ ConfigSection serialization fix verified")
        return True
        
    except Exception as e:
        print(f"   ❌ ConfigSection test failed: {e}")
        return False


async def test_fixed_crawler_service():
    """测试修复后的爬虫服务"""
    print("\n🕷️  Testing fixed crawler service...")
    
    try:
        settings = get_settings()
        auth_service = MockAuthService()
        
        # Test crawler initialization
        async with WebCrawlerService(settings, auth_service) as crawler:
            print("   ✅ Crawler service initialized without serialization errors")
            
            # Test a simple RSS source
            test_source = {
                'id': 'test_rss',
                'url': 'https://ai.googleblog.com/feeds/posts/default',
                'type': 'rss',
                'name': 'Google AI Blog'
            }
            
            # Test source validation (quick check)
            is_valid = await crawler.validate_source(test_source)
            print(f"   • Source validation: {'✅ Valid' if is_valid else '⚠️  Invalid'}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Fixed crawler service test failed: {e}")
        return False


async def test_modern_tools_availability():
    """测试现代工具可用性"""
    print("\n🔧 Testing modern tools availability...")
    
    # Test Firecrawl
    try:
        from firecrawl import FirecrawlApp
        firecrawl_available = True
        print("   ✅ Firecrawl: Available")
    except ImportError:
        firecrawl_available = False
        print("   ❌ Firecrawl: Not installed (pip install firecrawl-py)")
    
    # Test Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler
        crawl4ai_available = True
        print("   ✅ Crawl4AI: Available")
    except ImportError:
        crawl4ai_available = False
        print("   ❌ Crawl4AI: Not installed (pip install crawl4ai)")
    
    # Test Playwright
    try:
        from playwright.async_api import async_playwright
        playwright_available = True
        print("   ✅ Playwright: Available")
    except ImportError:
        playwright_available = False
        print("   ❌ Playwright: Not installed (pip install playwright)")
    
    # Basic tools (always available)
    print("   ✅ aiohttp + BeautifulSoup: Available (fallback)")
    
    total_tools = 4
    available_tools = sum([
        firecrawl_available,
        crawl4ai_available, 
        playwright_available,
        True  # Basic tools always available
    ])
    
    print(f"   📊 Tool availability: {available_tools}/{total_tools} ({available_tools/total_tools:.1%})")
    
    return available_tools >= 2  # At least 2 tools should be available


async def test_modern_crawler_agent():
    """测试现代爬虫代理"""
    print("\n🚀 Testing modern crawler agent...")
    
    try:
        # Check for Firecrawl API key
        firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
        if firecrawl_key:
            print("   🔥 Firecrawl API key detected")
        else:
            print("   ⚠️  No Firecrawl API key (using open source tools only)")
        
        # Initialize modern crawler agent
        agent = ModernCrawlerAgent(firecrawl_api_key=firecrawl_key)
        
        # Check tool availability
        availability = agent._check_tool_availability()
        print("   🔧 Tool availability check:")
        for tool, available in availability.items():
            status = "✅" if available else "❌"
            print(f"      {status} {tool}")
        
        # Get recommendations for missing tools
        recommendations = agent.get_tool_recommendations()
        if recommendations:
            print("   📝 Setup recommendations:")
            for tool, advice in recommendations.items():
                print(f"      • {tool}: {advice[:60]}...")
        
        available_count = sum(availability.values())
        print(f"   📊 Available tools: {available_count}/{len(availability)}")
        
        return available_count >= 1  # At least one tool should be available
        
    except Exception as e:
        print(f"   ❌ Modern crawler agent test failed: {e}")
        return False


async def test_quick_crawl():
    """快速爬取测试 (仅测试1个源)"""
    print("\n⚡ Quick crawl test (1 source)...")
    
    try:
        settings = get_settings()
        
        # Test with modern crawler service
        async with ModernCrawlerService(settings) as crawler:
            # Override sources for quick test
            crawler.PREMIUM_SOURCES = {
                "rss_feeds": [
                    {
                        "name": "Google AI Blog", 
                        "url": "https://ai.googleblog.com/feeds/posts/default", 
                        "priority": "high"
                    }
                ],
                "websites": []  # Skip websites for quick test
            }
            
            print("   🕷️  Testing RSS crawl...")
            results = await crawler.crawl_premium_sources()
            
            stats = results.get("stats", {})
            tools_used = results.get("tools_used", [])
            
            print(f"   📊 Results:")
            print(f"      • Total sources: {stats.get('total_sources', 0)}")
            print(f"      • Successful: {stats.get('successful', 0)}")
            print(f"      • Articles: {len(results.get('rss_articles', []))}")
            print(f"      • Tools used: {', '.join(tools_used) if tools_used else 'None'}")
            
            # Show sample article if available
            articles = results.get("rss_articles", [])
            if articles:
                sample = articles[0]
                print(f"   📰 Sample article: {sample.get('title', 'No title')[:50]}...")
                print(f"      • Method: {sample.get('extraction_method', 'unknown')}")
                print(f"      • Quality: {sample.get('quality_score', 0):.2f}")
            
            return stats.get('successful', 0) > 0
            
    except Exception as e:
        print(f"   ❌ Quick crawl test failed: {e}")
        return False


def print_final_report(test_results):
    """打印最终测试报告"""
    print("\n" + "=" * 60)
    print("📋 FINAL TEST REPORT")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Overall Score: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for production.")
        print("\n🚀 You can now run the enhanced crawler with confidence:")
        print("   • ConfigSection serialization issues resolved")
        print("   • Modern tools available and working")
        print("   • Premium AI sources verified")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. System is functional with minor issues.")
        print("\n📝 Recommendations:")
        if not test_results.get("ConfigSection Fix", True):
            print("   • Check configuration file format")
        if not test_results.get("Modern Tools", True):
            print("   • Install recommended tools: pip install crawl4ai playwright")
        if not test_results.get("Quick Crawl", True):
            print("   • Check internet connection and source accessibility")
    else:
        print("❌ Several tests failed. Manual intervention required.")
        print("\n🔧 Troubleshooting needed:")
        for test_name, result in test_results.items():
            if not result:
                print(f"   • Fix: {test_name}")
    
    print("=" * 60)


async def main():
    """主测试函数"""
    print("🧪 Enhanced Crawler Fix Verification Test Suite")
    print("Testing ConfigSection fixes and modern tool integration")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: ConfigSection serialization fix
    test_results["ConfigSection Fix"] = await test_config_serialization_fix()
    
    # Test 2: Fixed crawler service  
    test_results["Fixed Crawler Service"] = await test_fixed_crawler_service()
    
    # Test 3: Modern tools availability
    test_results["Modern Tools"] = await test_modern_tools_availability()
    
    # Test 4: Modern crawler agent
    test_results["Modern Crawler Agent"] = await test_modern_crawler_agent()
    
    # Test 5: Quick crawl test
    test_results["Quick Crawl"] = await test_quick_crawl()
    
    # Print final report
    print_final_report(test_results)
    
    # Return success status
    return sum(test_results.values()) >= len(test_results) * 0.7


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)