import axios from 'axios'
import { 
  Article, WorkflowStatus, Source, CreateSourceRequest, 
  AnalysisResult, MockAuthResult, ContentType 
} from '@/types'

const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000'
})

export const startWorkflow = async (params?: { topic?: string; sourceIds?: string[] }) => {
  const requestBody = params || {}
  const response = await api.post('/workflows', requestBody)
  return response.data.data || response.data
}

export const getWorkflowStatus = async (workflowId: string): Promise<WorkflowStatus> => {
  const response = await api.get(`/workflows/${workflowId}`)
  return response.data.data || response.data
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
  return response.data.data || response.data
}

export const getArticlesByWorkflow = async (workflowId: string): Promise<{ articles: Article[] }> => {
  const response = await api.get(`/articles?workflow_id=${workflowId}`)
  return response.data.data || response.data
}

// 信源管理API
export const getSources = async (includeInactive = false): Promise<Source[]> => {
  // Convert includeInactive to active_only for new API
  const activeOnly = !includeInactive
  const response = await api.get(`/sources?active_only=${activeOnly}`)
  
  // Handle clean architecture API response format
  if (response.data && response.data.success && response.data.data && Array.isArray(response.data.data.sources)) {
    return response.data.data.sources
  } else {
    console.warn('Unexpected sources response format:', response.data)
    return []
  }
}

export const createSource = async (source: CreateSourceRequest): Promise<Source> => {
  const response = await api.post('/sources', source)
  return response.data.data || response.data
}

export const updateSource = async (id: string, updates: Partial<Source>): Promise<Source> => {
  const response = await api.put(`/sources/${id}`, updates)
  return response.data.data || response.data
}

export const deleteSource = async (id: string): Promise<void> => {
  await api.delete(`/sources/${id}`)
}

export const analyzeWebpage = async (url: string, contentType: ContentType): Promise<AnalysisResult> => {
  const response = await api.post('/sources/analyze', { url, content_type: contentType })
  return response.data
}

export const findMockAuth = async (url: string): Promise<MockAuthResult> => {
  const response = await api.post('/sources/mock-auth', { url })
  return response.data
}

export const getSourceStats = async (): Promise<Record<string, number>> => {
  const response = await api.get('/sources/statistics')
  return response.data.data || response.data
}

export const testSource = async (id: string): Promise<Record<string, unknown>> => {
  const response = await api.post(`/sources/${id}/test`)
  return response.data
}