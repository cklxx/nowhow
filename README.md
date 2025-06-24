# AI内容聚合器 (AI Content Aggregator)

基于LangGraph的多Agent系统，自动抓取全网AI相关内容并结构化生成高质量文章。

## 功能特性

- 🕷️ **智能抓取**: 自动从RSS订阅源和网站抓取AI相关内容
- ⚙️ **内容处理**: 使用GPT模型结构化分析和分类内容
- ✍️ **文章生成**: 基于处理后的内容自动生成800-1200字的高质量文章
- 🌐 **Web界面**: 现代化的React前端界面，支持实时监控工作流进度
- 🔄 **异步处理**: 后台异步处理工作流，支持多个并发任务

## 技术栈

### 后端
- **Python 3.12** + **uv** 包管理
- **LangGraph** - 多Agent工作流编排
- **LangChain** + **OpenAI** - AI内容处理
- **FastAPI** - 高性能API框架
- **BeautifulSoup4** + **feedparser** - 网页和RSS解析

### 前端
- **React 19** + **TypeScript**
- **Vite** - 现代化构建工具
- **Tailwind CSS** - 实用优先的CSS框架
- **Axios** - HTTP客户端

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd nowhow
```

### 2. 启动后端
```bash
cd backend
uv sync                    # 安装依赖
export OPENAI_API_KEY=your_api_key  # 设置API密钥
uv run python main.py      # 启动API服务器 (端口 8000)
```

### 3. 启动前端
```bash
cd frontend
npm install               # 安装依赖
npm run dev              # 启动开发服务器 (端口 3000)
```

### 4. 访问应用
打开浏览器访问 `http://localhost:3000`

## 使用说明

1. **设置API密钥**: 在前端界面输入你的OpenAI API Key
2. **启动工作流**: 点击"开始生成内容"按钮
3. **监控进度**: 系统会自动显示工作流状态和进度
4. **查看结果**: 工作流完成后可查看生成的文章

## 项目结构

```
├── backend/                 # Python后端
│   ├── agents/             # LangGraph Agents
│   │   ├── base_agent.py   # Agent基类
│   │   ├── crawler_agent.py # 内容抓取Agent
│   │   ├── processor_agent.py # 内容处理Agent
│   │   ├── writer_agent.py  # 文章生成Agent
│   │   └── workflow.py     # LangGraph工作流
│   ├── api/                # FastAPI接口
│   └── main.py             # 应用入口
├── frontend/               # React前端
│   ├── src/
│   │   ├── App.tsx         # 主应用组件
│   │   └── main.tsx        # 入口文件
│   └── public/
└── README.md
```

## API接口

### 工作流管理
- `POST /workflow/start` - 启动内容生成工作流
- `GET /workflow/status/{id}` - 查询工作流状态
- `GET /workflow/list` - 列出所有工作流

### 文章管理
- `GET /articles` - 获取最新生成的文章
- `GET /articles/{workflow_id}` - 获取特定工作流的文章

## 配置说明

### 内容来源
系统默认配置了以下内容源：
- OpenAI Blog
- Google AI Blog  
- DeepMind Blog
- arXiv CS.AI
- Papers with Code
- O'Reilly Radar

### 环境变量
- `OPENAI_API_KEY` - OpenAI API密钥（必需）

## 扩展开发

### 添加新的内容源
编辑 `backend/agents/crawler_agent.py`，在 `sources` 配置中添加新的RSS源或网站。

### 自定义处理逻辑
修改 `backend/agents/processor_agent.py` 中的处理提示词和过滤逻辑。

### 调整文章生成
在 `backend/agents/writer_agent.py` 中修改文章生成的提示词和格式。

## 许可证

MIT License
