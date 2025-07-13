import sys
sys.path.append('.')

try:
    from services.enhanced_crawler_service import EnhancedCrawlerService, RateLimiter
    print("Enhanced crawler service imports successfully")
    
    limiter = RateLimiter()
    print("RateLimiter initialized successfully")
    
    # Test domain-specific delays
    arxiv_delay = limiter._get_domain_base_delay('arxiv.org')
    github_delay = limiter._get_domain_base_delay('github.com')
    
    print(f"Domain delays: arxiv.org={arxiv_delay}s, github.com={github_delay}s")
    
    print("All enhanced crawler optimizations loaded correctly\!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
