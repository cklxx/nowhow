'use client'

import React, { useState, useEffect } from 'react'
import { Article, WorkflowStatus } from '@/types'
import { startWorkflow, getWorkflowStatus, getLatestArticles } from '@/lib/api'
import TopicInput from '@/components/TopicInput'
import ArticleList from '@/components/ArticleList'
import ArticleDetail from '@/components/ArticleDetail'
import SourceManager from '@/components/SourceManager'
import ErrorBoundary from '@/components/ErrorBoundary'
import { ToastContainer } from '@/components/Toast'
import { useToast } from '@/hooks/useToast'

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(false)
  const [, setCurrentWorkflow] = useState<string | null>(null)
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [currentTopic, setCurrentTopic] = useState<string>('')
  const [showSourceManager, setShowSourceManager] = useState(false)
  
  const toast = useToast()

  const handleStartTopicWorkflow = async (topic: string) => {
    setLoading(true)
    setCurrentTopic(topic)
    setSelectedArticle(null) // 清除当前文章详情
    setWorkflowStatus(null)   // 清除旧的工作流状态
    
    try {
      toast.info(`正在探索"${topic}"相关内容...`, '系统正在自动发现信源并抓取内容')
      
      // 传递主题参数给工作流
      const response = await startWorkflow({ topic })
      setCurrentWorkflow(response.id)
      toast.success('内容生成已启动', `正在为"${topic}"生成相关文章`)
      pollWorkflowStatus(response.id)
    } catch (error) {
      console.error('启动主题工作流失败:', error)
      toast.error('启动失败', error instanceof Error ? error.message : '未知错误')
      setLoading(false)
    }
  }

  const pollWorkflowStatus = async (workflowId: string) => {
    let pollInterval: number
    let pollCount = 0
    const maxPolls = 150 // Maximum 5 minutes of polling
    
    const poll = async () => {
      try {
        const status = await getWorkflowStatus(workflowId)
        setWorkflowStatus(status)
        pollCount++
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          setLoading(false)
          const articles = status.results?.articles as Article[] || []
          const articleCount = articles.length
          toast.success(`"${currentTopic}"内容生成完成`, `成功生成了 ${articleCount} 篇相关文章`)
          if (articles.length > 0) {
            setArticles(articles)
          }
          return
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          setLoading(false)
          toast.error('内容生成失败', status.error_message || '未知错误')
          // Load previous articles when workflow fails
          loadLatestArticles()
          return
        }
        
        // Stop polling after maximum attempts
        if (pollCount >= maxPolls) {
          clearInterval(pollInterval)
          setLoading(false)
          toast.warning('工作流超时', '轮询已停止，工作流可能仍在后台运行')
          loadLatestArticles()
          return
        }
        
        // Adjust polling frequency based on status and duration
        let nextInterval = 2000 // Default 2 seconds
        
        if (status.status === 'running') {
          // If running for a while, reduce frequency
          if (pollCount > 10) {
            nextInterval = 5000 // 5 seconds after 20 seconds
          }
          if (pollCount > 30) {
            nextInterval = 10000 // 10 seconds after 1 minute
          }
        } else if (status.status === 'pending') {
          // Faster polling for pending status
          nextInterval = 1000 // 1 second
        }
        
        // Set next poll with adjusted interval
        if (nextInterval !== 2000) {
          clearInterval(pollInterval)
          pollInterval = window.setTimeout(poll, nextInterval)
        }
        
      } catch (error) {
        console.error('获取工作流状态失败:', error)
        // Don't show toast for every polling error, just log it
        if (pollCount < 5) { // Only show error for first few attempts
          toast.warning('连接问题', '获取工作流状态时遇到问题，正在重试...')
        }
        // Reduce frequency on errors
        clearInterval(pollInterval)
        pollInterval = window.setTimeout(poll, 5000) // 5 seconds on error
      }
    }
    
    // Start initial polling
    pollInterval = window.setInterval(poll, 2000)
  }

  const loadLatestArticles = async () => {
    try {
      const response = await getLatestArticles()
      console.log(response);
      setArticles(response.articles || [])
      
      // 静默加载，不显示成功消息除非用户明确要求
      if (response.source === 'none' && articles.length === 0) {
        // 只在真正没有文章时显示提示
      }
    } catch (error) {
      console.error('加载文章失败:', error)
      toast.error('加载文章失败', error instanceof Error ? error.message : '网络连接问题')
    }
  }

  const handleArticleClick = (article: Article) => {
    setSelectedArticle(article)
  }

  const handleBackToList = () => {
    setSelectedArticle(null)
  }

  useEffect(() => {
    loadLatestArticles()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <header className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              智能内容发现
            </h1>
            <p className="text-lg text-gray-600">
              输入任何主题，AI自动为你发现、总结相关内容
            </p>
          </header>

          <div className="max-w-6xl mx-auto">
            {/* 显示文章详情页 */}
            {selectedArticle ? (
              <ArticleDetail 
                article={selectedArticle} 
                onBack={handleBackToList}
              />
            ) : (
              <>
                {/* 主题输入界面 */}
                <TopicInput
                  onStartTopicWorkflow={handleStartTopicWorkflow}
                  loading={loading}
                  workflowStatus={workflowStatus}
                />
                
                {/* 文章列表 */}
                <ArticleList 
                  articles={articles} 
                  onArticleClick={handleArticleClick}
                />

                {/* 高级选项 */}
                {!loading && (
                  <div className="mt-12 pt-8 border-t border-gray-200">
                    <div className="flex items-center justify-center space-x-6 text-sm">
                      <button
                        onClick={() => setShowSourceManager(!showSourceManager)}
                        className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
                      >
                        {showSourceManager ? '隐藏信源管理' : '管理信源'}
                      </button>
                      
                      <button
                        onClick={loadLatestArticles}
                        className="text-gray-600 hover:text-gray-800 font-medium transition-colors"
                      >
                        刷新文章
                      </button>
                    </div>

                    {/* 信源管理折叠面板 */}
                    {showSourceManager && (
                      <div className="mt-8">
                        <SourceManager onSourcesChange={loadLatestArticles} />
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        
        {/* Toast notifications */}
        <ToastContainer messages={toast.messages} onRemove={toast.removeToast} />
      </div>
    </ErrorBoundary>
  )
}
