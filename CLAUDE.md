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

### Frontend (React + Vite)
```bash
cd frontend
npm run dev                    # Start development server (port 3000)
npm run build                  # Build for production
npm run preview                # Preview production build
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
- **React 19** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Axios** for API communication
- **Responsive Design** with article management interface

## Key Endpoints

- `POST /workflow/start` - Start content generation workflow
- `GET /workflow/status/{id}` - Check workflow progress
- `GET /articles` - Get latest generated articles
- `GET /articles/{workflow_id}` - Get articles from specific workflow

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for content processing and article generation
- API key can also be provided via frontend interface

### Dependencies
- **Backend**: LangGraph, LangChain, FastAPI, BeautifulSoup4, feedparser
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Axios

## Development Notes

- The workflow runs asynchronously in background tasks
- Frontend polls backend every 2 seconds for workflow status
- Content is filtered by relevance score to ensure quality
- Articles are grouped by category before generation
- System handles failures gracefully with error reporting