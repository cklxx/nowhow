#!/usr/bin/env python3
"""
Start script for unified modern AI content aggregator.
Uses 2024's best web scraping tools: Firecrawl + Crawl4AI + Playwright.
"""

import os
import sys
from pathlib import Path
import uvicorn

# Add project root to Python path
backend_dir = Path(__file__).parent.absolute()
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

def check_environment():
    """Check environment setup and provide recommendations"""
    print("🔧 Checking Modern Tools Environment...")
    
    # Check API keys
    api_keys = {
        "OpenAI/ARK": os.getenv('OPENAI_API_KEY') or os.getenv('ARK_API_KEY'),
        "Firecrawl": os.getenv('FIRECRAWL_API_KEY')
    }
    
    print("\n🔑 API Keys Status:")
    for service, key in api_keys.items():
        status = "✅ Configured" if key else "❌ Missing"
        print(f"   {status} {service}")
    
    # Check tool availability
    print("\n🛠️  Modern Tools Status:")
    
    # Check Firecrawl
    try:
        from firecrawl import FirecrawlApp
        print("   ✅ Firecrawl: Available")
    except ImportError:
        print("   ❌ Firecrawl: Not installed (pip install firecrawl-py)")
    
    # Check Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler
        print("   ✅ Crawl4AI: Available")
    except ImportError:
        print("   ❌ Crawl4AI: Not installed (pip install crawl4ai)")
    
    # Check Playwright
    try:
        from playwright.async_api import async_playwright
        print("   ✅ Playwright: Available")
    except ImportError:
        print("   ❌ Playwright: Not installed (pip install playwright)")
    
    # Basic tools (always available)
    print("   ✅ HTTP + BeautifulSoup: Available (fallback)")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not api_keys["OpenAI/ARK"]:
        print("   • Set OPENAI_API_KEY or ARK_API_KEY for AI processing")
    if not api_keys["Firecrawl"]:
        print("   • Get Firecrawl API key from https://firecrawl.dev for premium extraction")
    
    print("\n📚 Quick Setup:")
    print("   pip install crawl4ai playwright firecrawl-py")
    print("   playwright install")
    print("   export FIRECRAWL_API_KEY=your-key")
    print("   export OPENAI_API_KEY=your-key")


def main():
    """Start the modern API server"""
    print("🚀 Starting AI Content Aggregator - Modern Edition")
    print("=" * 60)
    print("🔧 Using: Firecrawl + Crawl4AI + Playwright + Premium Sources")
    print("📡 API: FastAPI with async workflows")
    print("🎯 Version: 2.0.0 - Unified Modern")
    print("=" * 60)
    
    # Check environment
    check_environment()
    
    # Change to backend directory for proper module resolution
    os.chdir(backend_dir)
    
    print(f"\n🌐 Starting server...")
    print(f"   • Backend: http://127.0.0.1:8000")
    print(f"   • API Docs: http://127.0.0.1:8000/docs")
    print(f"   • Health Check: http://127.0.0.1:8000/health")
    print("=" * 60)
    
    # Start server
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=None,
        access_log=True
    )


if __name__ == "__main__":
    main()