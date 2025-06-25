export interface Article {
  title: string
  content: string
  summary: string
  word_count: number
  sources: string[]
  tags: string[]
  category: string
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
  error?: string
  created_at: string
  completed_at?: string
}