import axios from 'axios'
import { Article, WorkflowStatus } from '@/types'

const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000'
})

export const startWorkflow = async () => {
  const response = await api.post('/workflow/start', {})
  return response.data
}

export const getWorkflowStatus = async (workflowId: string): Promise<WorkflowStatus> => {
  const response = await api.get(`/workflow/status/${workflowId}`)
  return response.data
}

export const getLatestArticles = async (): Promise<{ 
  articles: Article[];
  total?: number;
  workflow_id?: string;
  generated_at?: string;
  source?: string;
  message?: string;
}> => {
  const response = await api.get('/articles')
  return response.data
}

export const getArticlesByWorkflow = async (workflowId: string): Promise<{ articles: Article[] }> => {
  const response = await api.get(`/articles/${workflowId}`)
  return response.data
}