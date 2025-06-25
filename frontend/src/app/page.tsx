'use client'

import React, { useState, useEffect } from 'react'
import { Article, WorkflowStatus } from '@/types'
import { startWorkflow, getWorkflowStatus, getLatestArticles } from '@/lib/api'
import ControlPanel from '@/components/ControlPanel'
import ArticleList from '@/components/ArticleList'

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(false)
  const [, setCurrentWorkflow] = useState<string | null>(null)
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null)

  const handleStartWorkflow = async () => {
    setLoading(true)
    try {
      const response = await startWorkflow()
      setCurrentWorkflow(response.workflow_id)
      pollWorkflowStatus(response.workflow_id)
    } catch (error) {
      console.error('启动工作流失败:', error)
      alert('启动工作流失败')
      setLoading(false)
    }
  }

  const pollWorkflowStatus = async (workflowId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await getWorkflowStatus(workflowId)
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
      const response = await getLatestArticles()
      setArticles(response.articles)
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
          <ControlPanel
            onStartWorkflow={handleStartWorkflow}
            onLoadArticles={loadLatestArticles}
            loading={loading}
            workflowStatus={workflowStatus}
          />
          
          <ArticleList articles={articles} />
        </div>
      </div>
    </div>
  )
}
