#!/usr/bin/env python3
"""
Test script for the enhanced crawler implementation.
Tests the fixed crawler agent and premium sources.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from agents.enhanced_workflow import EnhancedAIContentWorkflow
from agents.base_agent import AgentState


async def test_enhanced_crawler():
    """Test the enhanced crawler with premium sources"""
    print("🧪 Testing Enhanced Crawler with Premium AI Sources")
    print("=" * 60)
    
    # Initialize the enhanced workflow
    workflow = EnhancedAIContentWorkflow()
    
    # Create initial state
    initial_state = AgentState()
    
    try:
        # Run just the crawler part for testing
        print("🕷️  Testing premium crawler...")
        
        # Test only crawler node
        result = await workflow._premium_crawler_node(initial_state)
        
        if result.error:
            print(f"❌ Crawler test failed: {result.error}")
            return False
        
        # Check results
        crawled_content = result.data.get("crawled_content", {})
        stats = crawled_content.get("stats", {})
        
        print("\n📊 Crawler Test Results:")
        print(f"   • Total Sources: {stats.get('total_expected', 0)}")
        print(f"   • Successful Sources: {stats.get('successful_sources', 0)}")
        print(f"   • Failed Sources: {stats.get('failed_sources', 0)}")
        print(f"   • RSS Articles: {stats.get('rss_articles_count', 0)}")
        print(f"   • Web Pages: {stats.get('web_pages_count', 0)}")
        print(f"   • Total Items: {stats.get('total_actual', 0)}")
        
        # Check source details
        sources_detail = result.progress.get("sources_detail", [])
        if sources_detail:
            print("\n📋 Source Details:")
            for source in sources_detail:
                status_icon = "✅" if source["status"] == "success" else "❌" if source["status"] == "error" else "⚠️"
                print(f"   {status_icon} {source['name']}: {source['status']}")
                if source["status"] == "success":
                    count_key = "articles_count" if source.get("type") == "rss" else "pages_count"
                    if count_key in source:
                        print(f"      Items: {source[count_key]}")
                elif source["status"] == "error" and "error" in source:
                    print(f"      Error: {source['error']}")
        
        # Show sample content
        rss_content = crawled_content.get("rss_content", [])
        web_content = crawled_content.get("web_content", [])
        
        if rss_content:
            print(f"\n📰 Sample RSS Articles ({len(rss_content)} total):")
            for i, article in enumerate(rss_content[:3]):
                print(f"   {i+1}. {article.get('title', 'No title')[:60]}...")
                print(f"      Source: {article.get('source', 'Unknown')}")
        
        if web_content:
            print(f"\n🌐 Sample Web Pages ({len(web_content)} total):")
            for i, page in enumerate(web_content[:3]):
                print(f"   {i+1}. {page.get('title', 'No title')[:60]}...")
                print(f"      Source: {page.get('source', 'Unknown')}")
        
        success_rate = stats.get('successful_sources', 0) / max(stats.get('total_expected', 1), 1)
        print(f"\n📈 Success Rate: {success_rate:.1%}")
        
        return success_rate > 0.3  # Consider successful if > 30% of sources work
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


async def test_source_config():
    """Test the premium sources configuration"""
    print("\n🔧 Testing Premium Sources Configuration")
    print("=" * 60)
    
    try:
        from agents.fixed_crawler_agent import FixedCrawlerAgent
        
        crawler = FixedCrawlerAgent()
        sources = crawler.premium_sources
        
        rss_sources = sources.get("sources", {}).get("rss_feeds", [])
        web_sources = sources.get("sources", {}).get("websites", [])
        
        print(f"📡 RSS Sources: {len(rss_sources)}")
        for source in rss_sources:
            priority_icon = "🔥" if source.get("priority") == "high" else "📄"
            print(f"   {priority_icon} {source['name']} ({source.get('category', 'unknown')})")
        
        print(f"\n🌐 Website Sources: {len(web_sources)}")
        for source in web_sources:
            priority_icon = "🔥" if source.get("priority") == "high" else "📄"
            print(f"   {priority_icon} {source['name']} ({source.get('category', 'unknown')})")
        
        print(f"\n✅ Configuration loaded successfully!")
        print(f"   Total Sources: {len(rss_sources) + len(web_sources)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Enhanced Crawler Test Suite")
    print("Testing improvements to fix crawling issues")
    print("=" * 60)
    
    # Test 1: Source configuration
    config_ok = await test_source_config()
    
    # Test 2: Enhanced crawler
    if config_ok:
        crawler_ok = await test_enhanced_crawler()
    else:
        crawler_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   • Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   • Enhanced Crawler: {'✅ PASS' if crawler_ok else '❌ FAIL'}")
    
    if config_ok and crawler_ok:
        print("\n🎉 All tests passed! Enhanced crawler is ready.")
        print("\n📝 Key improvements implemented:")
        print("   • Fixed ConfigSection serialization issues")
        print("   • Added premium AI news sources")
        print("   • Implemented proper retry mechanisms")
        print("   • Added user agent rotation")
        print("   • Enhanced error handling")
        print("   • Improved content extraction")
    else:
        print("\n⚠️  Some tests failed. Review the errors above.")
    
    return config_ok and crawler_ok


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)