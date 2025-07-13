# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a sophisticated multi-agent AI content aggregation system built with modern enterprise-grade architecture patterns. The system automatically crawls, processes, and generates AI-related articles using a combination of LangGraph orchestration, dependency injection, and microservices design principles.

### Core Components
- **Backend**: Python FastAPI application with LangGraph multi-agent orchestration
- **Frontend**: Next.js 15 application with React 19, TypeScript, and Turbopack
- **Architecture**: Multi-layer enterprise architecture with dependency injection container
- **AI Integration**: ARK API for advanced AI processing and content generation
- **Storage**: Enhanced file-based storage system with caching and deduplication

## Development Commands

### Modern Unified System (Recommended)
```bash
# Start modern backend with cutting-edge tools
cd backend
python start_modern.py         # Start modern API server (port 8000)

# Test modern system integration
python test_unified_modern.py  # Comprehensive test suite

# Traditional startup (still available)
./start.sh -d                  # Start both backend and frontend
```

### Backend (Python with uv)
```bash
cd backend
uv run python main.py          # Start unified modern API (port 8000)
uv add <package>               # Add new dependencies
uv sync                        # Sync dependencies

# Health check with tool status
curl http://localhost:8000/health

# Modern API Documentation
curl http://localhost:8000/docs
```

### Frontend (Next.js + Turbopack)
```bash
cd frontend
npm run dev                    # Start development server with Turbopack (port 3000)
npm run build                  # Build for production
npm run start                  # Start production server
npm run lint                   # Run ESLint
npm run type-check             # TypeScript type checking
```

## Core Architecture

### 1. Multi-Layer Enterprise Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                     │
│  Next.js 15 + React 19 + TypeScript + Tailwind CSS v4    │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                     │
│     FastAPI + CORS + Request/Response Validation          │
└─────────────────────────────────────────────────────────────┘
                              │ Dependency Injection
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                    │
│         LangGraph Multi-Agent Orchestration               │
└─────────────────────────────────────────────────────────────┘
                              │ Interface Abstraction
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                         │
│    AI • Storage • Crawler • Content Processing Services   │
└─────────────────────────────────────────────────────────────┘
                              │ Repository Pattern
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                       │
│      Repository Pattern + Enhanced Storage Service        │
└─────────────────────────────────────────────────────────────┘
                              │ Storage Abstraction
┌─────────────────────────────────────────────────────────────┐
│                    Persistence Layer                       │
│     File System + JSON + YAML Configuration Storage       │
└─────────────────────────────────────────────────────────────┘
```

### 2. Dependency Injection Container System

The project uses a sophisticated dependency injection container (`backend/core/container.py`) that manages:

- **Interface Abstraction**: All services implement defined interfaces (`backend/core/interfaces.py`)
- **Singleton Management**: Automatic lifecycle management of service instances
- **Dependency Resolution**: Automatic dependency injection and circular dependency detection
- **Factory Pattern**: Dynamic service instantiation with complex dependencies

### 3. Multi-Agent System (LangGraph)

#### Agent Workflow Pipeline
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Crawler   │───▶│  Processor  │───▶│  Research   │───▶│   Writer    │
│    Agent    │    │    Agent    │    │    Agent    │    │    Agent    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Core Agents

1. **CrawlerAgent** (`backend/agents/crawler_agent.py`)
   - Multi-source content crawling (RSS, HTML, API)
   - Concurrent processing with rate limiting
   - Authentication support and error recovery
   - Enhanced crawler with advanced features

2. **ProcessorAgent** (`backend/agents/processor_agent.py`)
   - AI-powered content analysis using ARK API
   - Content categorization and relevance scoring
   - Quality filtering (≥0.6 relevance threshold)
   - Key information extraction

3. **ResearchAgent** (`backend/agents/research_agent.py`)
   - Deep research and fact verification
   - Topic analysis and insight generation
   - ReactAgent pattern with tool integration
   - Enhanced content understanding

4. **WriterAgent** (`backend/agents/writer_agent.py`)
   - Comprehensive article generation (800-1200 words)
   - Content grouping by category
   - Professional article structure
   - Quality control and optimization

### 4. Enhanced Storage System

#### Features
- **Auto-merging**: Intelligent consolidation of multiple data files
- **Deduplication**: Advanced content deduplication algorithms
- **Caching**: Multi-level caching for performance optimization
- **Time-series Analysis**: Temporal data organization and retrieval
- **Workflow Persistence**: Complete workflow state management

#### Storage Patterns
```
/data/
├── articles/           # Generated articles by workflow
├── content/           # Processed content storage
├── sources/          # Source configuration files
├── workflows/        # Workflow state persistence
└── logs/            # System logs and debugging
```

### 5. Service Layer Architecture

#### Core Services

- **ARKModelService**: Unified AI model API integration
- **EnhancedStorageService**: Advanced file storage with caching
- **WebCrawlerService**: Multi-source web crawling service
- **AIContentProcessor**: Intelligent content processing
- **AIArticleWriter**: AI-powered article generation
- **JsonSourceRepository**: Source configuration management
- **MockAuthService**: Authentication simulation service

#### Service Communication
All services use async/await patterns and communicate through well-defined interfaces.

## API Architecture

### Core Endpoints

#### Workflow Management
- `POST /workflow/start` - Start content generation workflow
- `GET /workflow/status/{id}` - Real-time workflow progress
- `POST /workflow/cancel/{id}` - Cancel running workflow

#### Article Management  
- `GET /articles` - Get generated articles with filtering
- `GET /articles/{workflow_id}` - Get workflow-specific articles
- `GET /articles/categories` - Get article categories
- `GET /articles/statistics` - Get article statistics
- `GET /articles/latest` - Get most recent articles

#### Source Management
- `GET /sources` - List configured sources
- `POST /sources/add` - Add new source configuration  
- `PUT /sources/{id}` - Update source configuration
- `DELETE /sources/{id}` - Remove source
- `GET /sources/statistics` - Get source statistics

#### System Management
- `GET /health` - System health check
- `POST /articles/cache/clear` - Clear article cache
- `POST /articles/deduplicate` - Manual deduplication

### API Features

- **Async Processing**: All long-running operations use background tasks
- **Real-time Status**: Live progress tracking for workflows
- **Error Handling**: Comprehensive error responses with debugging info
- **Pagination**: Built-in pagination support for large datasets
- **Filtering**: Advanced filtering by category, date, and relevance

## Frontend Architecture

### Component Structure
```
frontend/src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Main dashboard
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── SourceManager.tsx # Source configuration interface
│   ├── CrawlingProgress.tsx # Real-time workflow progress
│   ├── ControlPanel.tsx  # Workflow controls
│   └── ArticleList.tsx   # Generated article display
├── lib/                  # Utilities and API client
│   └── api.ts           # Centralized API client
└── types/               # TypeScript definitions
    └── index.ts         # Shared type definitions
```

### Frontend Features

- **App Router**: Modern Next.js routing with server/client components
- **Turbopack**: Lightning-fast development builds
- **Real-time Updates**: Live status polling every 2 seconds  
- **Type Safety**: End-to-end TypeScript type checking
- **Responsive Design**: Mobile-first responsive layout
- **Error Boundaries**: Graceful error handling

## Configuration Management

### Hierarchical Configuration (`backend/conf.yml`)

```yaml
# Application Configuration
app:
  name: "AI Content Aggregator"
  version: "1.0.0"

# AI Model Configuration  
models:
  ark:
    api_key: "${ARK_API_KEY}"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    model: "ep-20250617155129-hfzl9"

# Agent Configuration
agents:
  crawler:
    max_sources: 50
    timeout: 30
  processor:
    relevance_threshold: 0.6
  writer:
    min_word_count: 800
    max_word_count: 1200

# Service Configuration
services:
  storage:
    base_path: "./data"
  analyzer:
    model_config: "ark"

# CORS Configuration
cors:
  allow_origins: ["http://localhost:3000"]
  allow_methods: ["GET", "POST", "PUT", "DELETE"]
```

### Environment Variables
- `ARK_API_KEY` - **Required** for AI processing and article generation

## File Structure

```
/
├── backend/                    # Python FastAPI backend
│   ├── agents/                # LangGraph multi-agent system
│   │   ├── crawler_agent.py   # Content crawling agent
│   │   ├── processor_agent.py # Content processing agent
│   │   ├── research_agent.py  # Research and verification agent
│   │   └── writer_agent.py    # Article writing agent
│   ├── api/                   # FastAPI application and endpoints
│   │   └── main.py           # Main API application with all endpoints
│   ├── core/                 # Core architecture components
│   │   ├── container.py      # Dependency injection container
│   │   ├── interfaces.py     # Service interface definitions
│   │   └── exceptions.py     # Custom exception classes
│   ├── services/             # Business logic services
│   │   ├── model_service.py  # AI model integration
│   │   ├── enhanced_storage_service.py # Advanced storage
│   │   ├── crawler_service.py # Web crawling service
│   │   ├── content_processor.py # Content processing
│   │   └── workflow_orchestrator.py # LangGraph orchestration
│   ├── repositories/         # Data access layer
│   │   └── source_repository.py # Source configuration repository
│   ├── models/               # Data models and schemas
│   │   └── source_config.py  # Source configuration models
│   ├── config/               # Configuration management
│   │   └── settings.py       # Configuration loader
│   ├── utils/                # Utility functions
│   │   └── file_storage.py   # File system utilities
│   ├── conf.yml              # Main configuration file
│   └── main.py               # Application entry point
├── frontend/                 # Next.js React frontend
│   ├── src/app/              # Next.js App Router
│   ├── src/components/       # React components
│   ├── src/lib/              # API client and utilities
│   ├── src/types/            # TypeScript definitions
│   └── package.json          # Frontend dependencies
├── start.sh                  # Enhanced startup script with live logs
└── CLAUDE.md                # This documentation file
```

## Development Workflow

### 1. Enhanced Startup Script
The `start.sh` script provides:
- **Live Log Monitoring**: Real-time backend and frontend logs with color coding
- **Health Checks**: Automatic validation of service startup
- **Process Management**: Proper cleanup on exit
- **Error Reporting**: Detailed error messages for debugging

### 2. Development Features
- **Hot Reload**: Both backend and frontend support hot reloading
- **Type Safety**: End-to-end TypeScript type checking
- **Error Boundaries**: Graceful error handling in React components
- **API Documentation**: Auto-generated FastAPI docs at `/docs`
- **Health Monitoring**: System health checks and status reporting

### 3. Quality Assurance
- **Content Filtering**: AI-powered relevance scoring (≥0.6 threshold)
- **Deduplication**: Automatic content deduplication
- **Error Recovery**: Comprehensive error handling and recovery
- **Performance Monitoring**: Built-in performance tracking
- **Data Validation**: Strict input/output validation

## Key Design Principles

### 1. Scalability
- **Microservices Architecture**: Loosely coupled service design
- **Async Processing**: Non-blocking operations for high throughput
- **Caching Strategy**: Multi-level caching for performance
- **Resource Management**: Efficient resource utilization

### 2. Maintainability  
- **Clean Architecture**: Clear separation of concerns
- **Interface Abstraction**: Easy to extend and modify
- **Dependency Injection**: Testable and modular design
- **Configuration-Driven**: Behavior modification without code changes

### 3. Reliability
- **Error Handling**: Comprehensive exception management
- **Data Persistence**: Automatic workflow state saving
- **Recovery Mechanisms**: Graceful degradation and recovery
- **Monitoring**: Detailed logging and health checks

### 4. Developer Experience
- **Type Safety**: Full TypeScript coverage
- **Hot Reload**: Fast development cycles
- **Clear Documentation**: Comprehensive API documentation
- **Debugging Tools**: Rich logging and error reporting

## Technology Stack

### Backend Technologies
- **Core Framework**: FastAPI + LangGraph + LangChain
- **AI Integration**: ARK API (ByteDance model service)
- **Package Management**: uv (modern Python package manager)
- **Data Processing**: BeautifulSoup4, feedparser, Pydantic
- **Configuration**: YAML + environment variable substitution
- **Storage**: Enhanced file-based storage with JSON/Markdown

### Frontend Technologies  
- **Core Framework**: Next.js 15 + React 19 + TypeScript
- **Build Tool**: Turbopack (next-generation bundler)
- **Styling**: Tailwind CSS v4 (modern utility-first CSS)
- **HTTP Client**: Axios with TypeScript integration
- **State Management**: React Hooks + Context API

### Development Tools
- **Startup Management**: Enhanced bash script with log monitoring
- **Process Management**: Automatic cleanup and error handling
- **Log Aggregation**: Centralized logging with color coding
- **Health Monitoring**: Real-time system health checks

This architecture represents a modern, enterprise-grade approach to AI content aggregation, combining cutting-edge technologies with proven architectural patterns to deliver a robust, scalable, and maintainable system.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.