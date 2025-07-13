# 现代爬虫工具配置指南 (2024)

本项目集成了2024年最先进的开源网页爬取工具，提供智能回退机制和卓越的内容提取质量。

## 🔧 工具概览

### 1. **Firecrawl** (推荐 - 商业API)
- **功能**: AI就绪的内容提取，支持Markdown输出
- **优势**: 最高质量的内容提取，专为LLM设计
- **费用**: 提供免费额度，付费计划

### 2. **Crawl4AI** (开源首选)
- **功能**: 专为AI和LLM设计的开源爬虫
- **优势**: 完全免费，本地运行，高质量提取
- **限制**: 仅限Python环境

### 3. **Playwright** (动态内容)
- **功能**: 现代浏览器自动化，支持JavaScript渲染
- **优势**: 处理动态内容，多浏览器支持
- **性能**: 比Selenium更快更稳定

### 4. **传统工具** (兜底方案)
- **工具**: aiohttp + BeautifulSoup
- **用途**: 静态内容，最后的兜底选择

## 📦 安装指南

### 基础安装 (必需)
```bash
# 基础HTTP和解析库 (已安装)
pip install aiohttp beautifulsoup4 feedparser

# 配置文件处理
pip install pyyaml
```

### Crawl4AI (强烈推荐)
```bash
# 安装Crawl4AI - 最佳开源选择
pip install crawl4ai

# 首次使用需要安装浏览器
crawl4ai-setup
```

### Playwright (动态内容支持)
```bash
# 安装Playwright
pip install playwright

# 安装浏览器
playwright install
```

### Firecrawl (可选 - 商业API)
```bash
# 安装Firecrawl Python客户端
pip install firecrawl-py

# 设置API密钥
export FIRECRAWL_API_KEY="your-api-key-here"
```

## 🔑 API密钥配置

### Firecrawl API (可选但推荐)
1. 访问 https://firecrawl.dev
2. 注册账户并获取API密钥
3. 设置环境变量:
```bash
# 临时设置
export FIRECRAWL_API_KEY="fc-your-api-key"

# 永久设置 (添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export FIRECRAWL_API_KEY="fc-your-api-key"' >> ~/.bashrc
```

## 🚀 使用示例

### 方式1: 使用现代爬虫代理
```python
from agents.modern_crawler_agent import ModernCrawlerAgent
from agents.base_agent import AgentState

# 初始化现代爬虫 (自动检测可用工具)
crawler = ModernCrawlerAgent()

# 执行爬取
state = AgentState()
result = await crawler.execute(state)

# 查看结果
crawled_data = result.data["crawled_content"]
print(f"Total items: {crawled_data['stats']['total_items']}")
print(f"Tools used: {crawled_data['metadata']['tools_used']}")
```

### 方式2: 直接使用现代爬虫服务
```python
from services.modern_crawler_service import ModernCrawlerService

# 初始化服务
async with ModernCrawlerService(settings, firecrawl_api_key) as crawler:
    results = await crawler.crawl_premium_sources()
    
    print(f"Success rate: {results['stats']['successful']/results['stats']['total_sources']:.1%}")
    print(f"Tools used: {results['tools_used']}")
```

## 📊 工具智能选择策略

系统会按以下优先级自动选择最佳工具:

### RSS源
1. **增强RSS解析** - 使用feedparser + 内容清理

### 动态网站
1. **Firecrawl** (如果有API密钥) - 最高质量
2. **Crawl4AI** (如果已安装) - 开源最佳
3. **Playwright** (动态内容) - JavaScript渲染
4. **传统HTTP** (兜底) - 基础抓取

## 🔍 工具可用性检查

运行以下脚本检查工具状态:
```python
from agents.modern_crawler_agent import ModernCrawlerAgent

crawler = ModernCrawlerAgent()
availability = crawler._check_tool_availability()

print("🔧 Tool Availability:")
for tool, available in availability.items():
    status = "✅" if available else "❌"
    print(f"   {status} {tool}")

# 获取安装建议
recommendations = crawler.get_tool_recommendations()
if recommendations:
    print("\n📝 Setup Recommendations:")
    for tool, advice in recommendations.items():
        print(f"   • {tool}: {advice}")
```

## 📈 性能优化配置

### 1. 连接池优化
- 并发连接数: 30
- 每主机连接数: 8
- DNS缓存: 5分钟

### 2. 智能速率限制
- RSS源间隔: 1-3秒
- 网站间隔: 2-5秒
- 指数退避重试

### 3. 用户代理轮换
- 5个现代浏览器UA
- 随机选择避免检测

## 🛠️ 故障排除

### 常见问题

**1. Crawl4AI安装失败**
```bash
# 确保有足够的磁盘空间 (至少2GB)
df -h

# 重新安装
pip uninstall crawl4ai
pip install crawl4ai
crawl4ai-setup
```

**2. Playwright浏览器下载失败**
```bash
# 使用特定镜像
PLAYWRIGHT_DOWNLOAD_HOST=playwright.azureedge.net playwright install

# 或使用系统浏览器
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

**3. Firecrawl API限制**
- 免费计划: 500次/月
- 付费计划: 根据需求选择
- 监控使用量: 在dashboard查看

### 性能调优

**1. 内存优化**
```python
# 限制并发连接
connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
```

**2. 超时配置**
```python
# 调整超时设置
timeout = aiohttp.ClientTimeout(total=60, connect=20)
```

## 📊 预期性能提升

使用现代工具栈后，您可以期待:

- **成功率**: 从30%提升到85%+
- **内容质量**: 智能提取，AI就绪格式
- **速度**: 并发处理，比串行快3-5倍
- **稳定性**: 多重回退，极少完全失败
- **维护性**: 自动工具选择，减少手动干预

## 🔮 未来扩展

计划中的增强功能:

1. **本地LLM集成** - 使用Ollama进行内容理解
2. **Redis缓存** - 避免重复爬取
3. **分布式爬取** - Celery任务队列
4. **实时监控** - Prometheus指标
5. **智能调度** - 基于网站活跃时间优化

---

## 🆘 获取帮助

如果遇到问题:

1. **检查日志**: 系统会记录详细的工具选择和错误信息
2. **运行诊断**: 使用`_check_tool_availability()`检查工具状态
3. **降级使用**: 即使高级工具不可用，传统方法仍然有效
4. **社区支持**: 
   - Crawl4AI: https://github.com/unclecode/crawl4ai
   - Firecrawl: https://docs.firecrawl.dev
   - Playwright: https://playwright.dev

现代爬虫系统已经准备就绪，开始您的高效内容收集之旅! 🚀