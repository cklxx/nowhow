#!/usr/bin/env python3
"""
简单的测试服务器，验证基本网络功能
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/articles':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"articles": [], "total": 0, "message": "Test server working"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('127.0.0.1', 8000), TestHandler)
    print("🧪 简单测试服务器启动在 http://127.0.0.1:8000")
    print("📡 测试访问: http://127.0.0.1:8000/articles")
    server.serve_forever()