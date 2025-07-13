#!/usr/bin/env python3
"""
固定的API启动脚本，避免模块导入问题
"""

import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动API服务器...")
    print(f"📁 Backend目录: {backend_dir}")
    
    # 直接导入app进行验证
    try:
        from api.main import app
        print("✅ API应用加载成功")
        
        # 检查路由
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        articles_routes = [r for r in routes if 'articles' in r]
        print(f"✅ 找到 {len(articles_routes)} 个articles路由: {articles_routes}")
        
    except Exception as e:
        print(f"❌ API应用加载失败: {e}")
        sys.exit(1)
    
    # 启动uvicorn
    try:
        uvicorn.run(
            "api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,  # 禁用reload避免问题
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Uvicorn启动失败: {e}")
        sys.exit(1)