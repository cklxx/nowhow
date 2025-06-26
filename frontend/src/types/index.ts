export interface Article {
  title: string
  content: string
  summary: string
  word_count: number
  sources: string[]
  tags: string[]
  category: string
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
  workflow_id: string
  status: string
  results?: {
    articles: Article[]
    crawled_items: number
    processed_items: number
    articles_generated: number
  }
  progress?: CrawlingProgress
  error?: string
  created_at: string
  completed_at?: string
}