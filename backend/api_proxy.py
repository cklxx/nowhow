#!/usr/bin/env python3
"""
API代理服务器，使用TestClient绕过uvicorn问题
"""

import sys
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

# 导入FastAPI应用
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 使用TestClient调用FastAPI应用
            response = client.get(self.path)
            
            # 设置响应头
            self.send_response(response.status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # 发送响应内容
            self.wfile.write(response.content)
            
        except Exception as e:
            print(f"Error handling request {self.path}: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_POST(self):
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # 使用TestClient调用FastAPI应用
            response = client.post(self.path, content=post_data, 
                                 headers={'Content-Type': self.headers.get('Content-Type', 'application/json')})
            
            # 设置响应头
            self.send_response(response.status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # 发送响应内容
            self.wfile.write(response.content)
            
        except Exception as e:
            print(f"Error handling POST request {self.path}: {e}")
            self.send_response(500)
            self.end_headers()

if __name__ == "__main__":
    try:
        # 验证API应用可以加载
        test_response = client.get("/articles")
        print(f"✅ API应用验证成功，状态码: {test_response.status_code}")
        print(f"✅ 测试响应长度: {len(test_response.text)} 字符")
        
        # 启动代理服务器
        server = HTTPServer(('127.0.0.1', 8000), ProxyHandler)
        print("🚀 API代理服务器启动在 http://127.0.0.1:8000")
        print("📡 前端现在可以正常访问 /articles 端点")
        print("🔄 使用TestClient绕过uvicorn绑定问题")
        server.serve_forever()
        
    except Exception as e:
        print(f"❌ 代理服务器启动失败: {e}")
        import traceback
        traceback.print_exc()