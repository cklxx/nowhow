export interface Article {
  id: string
  title: string
  content: string
  url?: string
  source_id?: string
  category: string
  author?: string
  published_at?: string
  created_at: string
  quality_score?: number
  metadata: Record<string, unknown>
  summary?: string
  tags?: string[]
  word_count?: number
  sources?: (string | { title?: string; url?: string })[]
}

export interface CrawlingProgress {
  current_step: string
  total_expected: number
  total_rss_feeds: number
  total_websites: number
  expected_articles_per_feed: number
  rss_feeds_completed: number
  websites_completed: number
  articles_found: number
  current_source: string
  status: string
  sources_detail: Array<{
    url: string
    title: string
    type: 'rss' | 'website'
    status: 'processing' | 'completed' | 'error'
    description?: string
    articles?: Array<{
      title: string
      url: string
    }>
    articles_count?: number
    content_length?: number
    error?: string
  }>
  total_actual?: number
  rss_articles_count?: number
  web_pages_count?: number
}

export interface WorkflowStatus {
  id: string
  status: string
  started_at: string
  completed_at?: string
  error_message?: string
  config: Record<string, unknown>
  results: Record<string, unknown>
  progress?: CrawlingProgress
}

// 信源管理相关类型
export enum SourceType {
  RSS = 'rss',
  WEBSITE = 'website',
  API = 'api'
}

export enum ContentType {
  ARTICLE = 'article',
  BLOG = 'blog',
  NEWS = 'news',
  RESEARCH = 'research',
  DOCUMENTATION = 'documentation'
}

export enum AuthType {
  NONE = 'none',
  COOKIE = 'cookie',
  HEADER = 'header',
  TOKEN = 'token',
  BASIC_AUTH = 'basic_auth'
}

export interface Source {
  id: string
  name: string
  url: string
  type: string
  category: string
  active: boolean
  created_at: string
  metadata: Record<string, unknown>
  is_built_in?: boolean
  ai_analyzed?: boolean
  ai_confidence?: number
  crawl_count?: number
  success_count?: number
  error_count?: number
  last_crawled?: string
  content_type?: string
  description?: string
}

export interface CreateSourceRequest {
  name: string
  url: string
  type: string
  category?: string
  content_type?: string
  description?: string
  active?: boolean
  metadata?: Record<string, unknown>
}

export interface AnalysisResult {
  url: string
  confidence: number
  suggested_selectors: {
    title?: string
    content?: string
    summary?: string
    author?: string
    publish_date?: string
    tags?: string
    category?: string
    exclude_selectors: string[]
  }
  page_structure: Record<string, unknown>
  content_patterns: string[]
  recommendations: string[]
  potential_issues: string[]
  requires_auth: boolean
  requires_js: boolean
  estimated_quality: number
}

export interface MockAuthResult {
  found: boolean
  sources: string[]
  confidence: number
  usage_notes?: string
  auth_config?: {
    type: string
    headers: Record<string, string>
    cookies: Record<string, string>
    mock_source?: string
    is_verified: boolean
  }
  recommendations: string[]
}