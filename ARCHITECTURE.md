# Project Architecture: AI Content Aggregator

This project is an **AI Content Aggregator** system designed to automatically crawl, process, and generate high-quality AI-related articles from various online sources. It leverages a **multi-agent system** orchestrated by LangGraph and adheres to **modern enterprise-grade architectural patterns** for scalability, maintainability, and reliability.

## 1. Core Components

### a. Backend (Python FastAPI)
- **LangGraph Multi-Agent System**: Orchestrates the content aggregation workflow through specialized agents:
    - **CrawlerAgent**: Fetches content from RSS feeds and websites.
    - **ProcessorAgent**: Analyzes and categorizes content using AI (ARK API).
    - **ResearchAgent**: Performs deep research and fact verification.
    - **WriterAgent**: Generates 800-1200 word articles.
- **FastAPI**: Provides a high-performance API gateway for frontend communication and workflow management.
- **Dependency Injection Container**: Manages service lifecycles, interface abstractions, and dependency resolution.
- **Enhanced Storage System**: Handles auto-merging, deduplication, caching, and time-series analysis for generated articles, processed content, and workflow states.
- **uv**: Modern Python package manager.

### b. Frontend (Next.js 15, React 19, TypeScript)
- **Next.js App Router**: Modern routing with server/client components.
- **React 19**: Component-based UI development.
- **TypeScript**: Ensures type safety across the application.
- **Tailwind CSS v4**: Utility-first CSS framework for responsive design.
- **Turbopack**: Fast development builds.
- **Axios**: HTTP client for API communication.
- **Real-time Updates**: Monitors workflow progress and displays generated articles.

## 2. Key Architectural Principles

- **Multi-Layer Enterprise Architecture**: Clear separation of Presentation, API Gateway, Business Logic, Service, Data Access, and Persistence layers.
- **Clean Architecture**: Promotes modularity, testability, and maintainability.
- **Scalability**: Achieved through microservices, asynchronous processing, and caching strategies.
- **Reliability**: Comprehensive error handling, data persistence, and monitoring.
- **Developer Experience**: Hot reloading, type safety, clear documentation, and robust debugging tools.

## 3. Technology Stack Highlights

- **Backend**: Python 3.12, LangGraph, LangChain, FastAPI, ARK API, BeautifulSoup4, feedparser, uv.
- **Frontend**: Next.js 15, React 19, TypeScript, Vite, Tailwind CSS, Axios.
- **Development Tools**: `start.sh` script for unified startup with live log monitoring, health checks.

## 4. Workflow Overview

The system initiates content generation workflows via the frontend. The backend agents collaboratively crawl, process, and write articles. Users can monitor the real-time status of these workflows and view the generated articles through the web interface.

This architecture ensures a robust, efficient, and extensible platform for AI-driven content aggregation.