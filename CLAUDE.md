# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent AI content aggregation system built with LangGraph that automatically crawls, processes, and generates AI-related articles. The system consists of:

- **Backend**: Python-based API using FastAPI with LangGraph for orchestrating multiple agents
- **Frontend**: React TypeScript application with Vite and Tailwindcss
- **Multi-Agent Architecture**: Three specialized agents working in sequence

## Development Commands

### Backend (Python with uv)
```bash
cd backend
uv run python main.py          # Start API server (port 8000)
uv add <package>               # Add new dependencies
uv sync                        # Sync dependencies
```

### Frontend (Next.js + Turbopack)
```bash
cd frontend
npm run dev                    # Start development server with Turbopack (port 3000)
npm run build                  # Build for production
npm run start                  # Start production server
npm run lint                   # Run ESLint
```

## Architecture

### Agent Workflow (LangGraph)
The system uses a sequential LangGraph workflow with three main agents:

1. **CrawlerAgent** (`backend/agents/crawler_agent.py`)
   - Crawls RSS feeds and websites for AI content
   - Sources: OpenAI blog, Google AI blog, arXiv, Papers with Code, etc.
   - Outputs raw content for processing

2. **ProcessorAgent** (`backend/agents/processor_agent.py`)
   - Uses OpenAI GPT to structure and analyze content
   - Extracts key points, categorizes content, scores relevance
   - Filters content by relevance score (≥0.6)

3. **WriterAgent** (`backend/agents/writer_agent.py`)
   - Generates comprehensive articles using GPT-4
   - Groups content by category before article generation
   - Creates 800-1200 word articles with proper structure

### API Structure
- **Main API**: `backend/api/main.py` (FastAPI application)
- **Workflow Management**: Async background tasks for long-running workflows
- **CORS Enabled**: For frontend development
- **In-memory Storage**: For demo purposes (extend with database for production)

### Frontend Structure
- **Next.js 15** with React 19 and TypeScript
- **Turbopack** (Rust-based bundler) for fast development builds
- **Tailwind CSS v4** for styling
- **Axios** for API communication
- **App Router** with server and client components
- **Responsive Design** with article management interface

## Key Endpoints

- `POST /workflow/start` - Start content generation workflow
- `GET /workflow/status/{id}` - Check workflow progress
- `GET /articles` - Get latest generated articles
- `GET /articles/{workflow_id}` - Get articles from specific workflow

## Configuration

### Environment Variables
- `ARK_API_KEY` - Required for content processing and article generation using ARK API
- ARK API Base URL: `https://ark.cn-beijing.volces.com/api/v3`
- Model: `ep-20250617155129-hfzl9`

### Dependencies
- **Backend**: LangGraph, LangChain, FastAPI, BeautifulSoup4, feedparser
- **Frontend**: Next.js, React, TypeScript, Turbopack, Tailwind CSS, Axios

## Development Notes

- The workflow runs asynchronously in background tasks
- Frontend polls backend every 2 seconds for workflow status
- Content is filtered by relevance score to ensure quality
- Articles are grouped by category before generation
- System handles failures gracefully with error reporting
- Next.js uses Turbopack for faster development builds
- API routes are proxied in development mode via next.config.ts rewrites