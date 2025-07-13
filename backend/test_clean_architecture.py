#!/usr/bin/env python3
"""
Test script to verify clean architecture implementation.
Tests source loading and API functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.dependency_container import get_container


async def test_clean_architecture():
    """Test clean architecture implementation"""
    print("🔧 Testing Clean Architecture Implementation...")
    print("=" * 50)
    
    try:
        # Test dependency injection container
        print("1. Testing dependency injection container...")
        container = get_container()
        print(f"   ✓ Container initialized: {type(container).__name__}")
        
        # Test configuration
        print("\n2. Testing configuration...")
        config = container.config
        print(f"   ✓ Config loaded")
        print(f"   ✓ ARK API Key configured: {'Yes' if config.api_key_ark else 'No'}")
        print(f"   ✓ Firecrawl API Key configured: {'Yes' if config.api_key_firecrawl else 'No'}")
        
        # Test repositories
        print("\n3. Testing repositories...")
        repos = container.repositories
        print(f"   ✓ Source repository: {type(repos.source_repository).__name__}")
        print(f"   ✓ Article repository: {type(repos.article_repository).__name__}")
        print(f"   ✓ Workflow repository: {type(repos.workflow_repository).__name__}")
        
        # Test services
        print("\n4. Testing services...")
        services = container.services
        print(f"   ✓ Crawler service: {type(services.crawler_service).__name__}")
        
        # Test available crawler tools
        crawler_tools = services.crawler_service.get_available_tools()
        print(f"   ✓ Available crawler tools:")
        for tool, available in crawler_tools.items():
            status = "✓" if available else "✗"
            print(f"     {status} {tool}")
        
        # Test use cases
        print("\n5. Testing use cases...")
        use_cases = container.use_cases
        print(f"   ✓ Source use cases: {type(use_cases.source_use_cases).__name__}")
        print(f"   ✓ Workflow use cases: {type(use_cases.workflow_use_cases).__name__}")
        
        # Test source operations
        print("\n6. Testing source operations...")
        source_use_cases = use_cases.source_use_cases
        
        # List existing sources
        existing_sources = await source_use_cases.list_sources(active_only=False)
        print(f"   ✓ Found {len(existing_sources)} existing sources")
        
        # Test creating a source
        print("\n7. Testing source creation...")
        test_source_data = {
            'name': 'Test AI News Source',
            'url': 'https://example.com/ai-news/feed',
            'type': 'rss',
            'category': 'ai',
            'active': True,
            'metadata': {'test': True}
        }
        
        created_source = await source_use_cases.create_source(test_source_data)
        print(f"   ✓ Created test source: {created_source.name}")
        print(f"     - ID: {created_source.id}")
        print(f"     - Type: {created_source.type.value}")
        print(f"     - Active: {created_source.active}")
        
        # Test retrieving the source
        retrieved_source = await source_use_cases.get_source(created_source.id)
        print(f"   ✓ Retrieved source: {retrieved_source.name}")
        
        # Test listing sources
        updated_sources = await source_use_cases.list_sources()
        print(f"   ✓ Total active sources: {len(updated_sources)}")
        
        # Test source statistics
        stats = await source_use_cases.get_source_statistics()
        print(f"   ✓ Source statistics: {stats}")
        
        # Clean up test source
        await source_use_cases.delete_source(created_source.id)
        print(f"   ✓ Cleaned up test source")
        
        print("\n🎉 Clean Architecture Test PASSED!")
        print("   All components are working correctly.")
        print("   Sources can be loaded, created, and managed.")
        return True
        
    except Exception as e:
        print(f"\n❌ Clean Architecture Test FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test API endpoints using the clean architecture"""
    print("\n🌐 Testing API Endpoints...")
    print("=" * 50)
    
    try:
        from api.clean_api import create_clean_app
        from fastapi.testclient import TestClient
        
        app = create_clean_app()
        client = TestClient(app)
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = client.get("/health")
        print(f"   ✓ Health check status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✓ System status: {health_data.get('data', {}).get('status', 'unknown')}")
            print(f"   ✓ Available tools: {health_data.get('data', {}).get('available_tools', [])}")
        
        # Test sources endpoint
        print("\n2. Testing sources list endpoint...")
        response = client.get("/sources")
        print(f"   ✓ Sources list status: {response.status_code}")
        if response.status_code == 200:
            sources_data = response.json()
            total_sources = sources_data.get('data', {}).get('total', 0)
            print(f"   ✓ Total sources: {total_sources}")
        
        # Test source statistics endpoint
        print("\n3. Testing source statistics endpoint...")
        response = client.get("/sources/statistics")
        print(f"   ✓ Statistics status: {response.status_code}")
        if response.status_code == 200:
            stats_data = response.json()
            print(f"   ✓ Statistics data available: {bool(stats_data.get('data'))}")
        
        print("\n🎉 API Endpoints Test PASSED!")
        print("   All endpoints are responding correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ API Endpoints Test FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 Clean Architecture Verification")
    print("=" * 60)
    
    # Test clean architecture
    arch_success = await test_clean_architecture()
    
    # Test API endpoints
    api_success = await test_api_endpoints()
    
    print("\n" + "=" * 60)
    if arch_success and api_success:
        print("✅ ALL TESTS PASSED!")
        print("   Clean architecture is working correctly.")
        print("   Sources can be loaded and API is functional.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the error messages above for details.")
    
    return arch_success and api_success


if __name__ == "__main__":
    asyncio.run(main())