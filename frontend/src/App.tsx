import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface Article {
  title: string
  content: string
  summary: string
  word_count: number
  sources: string[]
  tags: string[]
  category: string
}

interface WorkflowStatus {
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

function App() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(false)
  const [currentWorkflow, setCurrentWorkflow] = useState<string | null>(null)
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null)
  const [apiKey, setApiKey] = useState('')

  const startWorkflow = async () => {
    if (!apiKey.trim()) {
      alert('请输入OpenAI API Key')
      return
    }

    setLoading(true)
    try {
      const response = await axios.post('/api/workflow/start', {
        openai_api_key: apiKey
      })
      
      setCurrentWorkflow(response.data.workflow_id)
      pollWorkflowStatus(response.data.workflow_id)
    } catch (error) {
      console.error('启动工作流失败:', error)
      alert('启动工作流失败')
      setLoading(false)
    }
  }

  const pollWorkflowStatus = async (workflowId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/workflow/status/${workflowId}`)
        const status: WorkflowStatus = response.data
        
        setWorkflowStatus(status)
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          setLoading(false)
          if (status.results?.articles) {
            setArticles(status.results.articles)
          }
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          setLoading(false)
          alert(`工作流失败: ${status.error}`)
        }
      } catch (error) {
        console.error('获取工作流状态失败:', error)
      }
    }, 2000)
  }

  const loadLatestArticles = async () => {
    try {
      const response = await axios.get('/api/articles')
      setArticles(response.data.articles)
    } catch (error) {
      console.error('加载文章失败:', error)
    }
  }

  useEffect(() => {
    loadLatestArticles()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI内容聚合器
          </h1>
          <p className="text-lg text-gray-600">
            基于LangGraph的多Agent系统，自动抓取、处理和生成AI相关内容
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          {/* 控制面板 */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">控制面板</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="输入你的OpenAI API Key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={startWorkflow}
                disabled={loading}
                className={`px-6 py-2 rounded-md text-white font-medium ${
                  loading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {loading ? '运行中...' : '开始生成内容'}
              </button>
              
              <button
                onClick={loadLatestArticles}
                className="px-6 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                加载最新文章
              </button>
            </div>

            {/* 工作流状态 */}
            {workflowStatus && (
              <div className="mt-4 p-4 bg-gray-50 rounded-md">
                <h3 className="font-medium text-gray-900">工作流状态</h3>
                <p className="text-sm text-gray-600">
                  ID: {workflowStatus.workflow_id}
                </p>
                <p className="text-sm text-gray-600">
                  状态: <span className={`font-medium ${
                    workflowStatus.status === 'completed' ? 'text-green-600' :
                    workflowStatus.status === 'failed' ? 'text-red-600' :
                    'text-yellow-600'
                  }`}>{workflowStatus.status}</span>
                </p>
                {workflowStatus.results && (
                  <div className="text-sm text-gray-600 mt-2">
                    <p>抓取项目: {workflowStatus.results.crawled_items}</p>
                    <p>处理项目: {workflowStatus.results.processed_items}</p>
                    <p>生成文章: {workflowStatus.results.articles_generated}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 文章列表 */}
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-900">
              生成的文章 ({articles.length})
            </h2>
            
            {articles.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">暂无文章，请先运行内容生成流程</p>
              </div>
            ) : (
              articles.map((article, index) => (
                <article key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900 flex-1">
                      {article.title}
                    </h3>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full ml-4">
                      {article.category}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 mb-4">{article.summary}</p>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    {article.tags.map((tag, tagIndex) => (
                      <span 
                        key={tagIndex}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  
                  <div className="text-sm text-gray-500 mb-4">
                    字数: {article.word_count} | 来源: {article.sources.length} 个
                  </div>
                  
                  <details className="cursor-pointer">
                    <summary className="text-blue-600 hover:text-blue-800 font-medium">
                      查看完整内容
                    </summary>
                    <div className="mt-4 prose max-w-none">
                      <div 
                        className="text-gray-700 whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{ __html: article.content.replace(/\n/g, '<br>') }}
                      />
                    </div>
                  </details>
                </article>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App