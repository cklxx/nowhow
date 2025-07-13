'use client'

import React, { useState } from 'react'
import { WorkflowStatus } from '@/types'

interface TopicInputProps {
  onStartTopicWorkflow: (topic: string) => void
  loading: boolean
  workflowStatus: WorkflowStatus | null
}

export default function TopicInput({ 
  onStartTopicWorkflow, 
  loading, 
  workflowStatus 
}: TopicInputProps) {
  const [topic, setTopic] = useState('')
  const [suggestions] = useState([
    '人工智能', '机器学习', '深度学习', '自然语言处理',
    '计算机视觉', '区块链技术', '量子计算', '边缘计算',
    '云计算', 'AI伦理', '自动驾驶', '智能制造'
  ])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (topic.trim() && !loading) {
      onStartTopicWorkflow(topic.trim())
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setTopic(suggestion)
    onStartTopicWorkflow(suggestion)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-8 mb-8">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          探索你感兴趣的主题
        </h2>
        <p className="text-lg text-gray-600">
          输入任何主题，AI将自动为你发现、抓取并总结相关内容
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="例如：人工智能最新发展、机器学习算法..."
              className="w-full px-6 py-4 border-2 border-gray-300 rounded-lg text-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !topic.trim()}
            className={`px-8 py-4 rounded-lg text-lg font-medium transition-all ${
              loading || !topic.trim()
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg transform hover:scale-105'
            }`}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                生成中...
              </div>
            ) : (
              '开始探索'
            )}
          </button>
        </div>
      </form>

      {/* 主题建议 */}
      <div className="max-w-4xl mx-auto mt-8">
        <p className="text-sm text-gray-500 mb-4 text-center">热门主题推荐：</p>
        <div className="flex flex-wrap justify-center gap-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={loading}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                loading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-700 hover:shadow-md transform hover:scale-105'
              }`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* 工作流状态 */}
      {workflowStatus && (
        <div className="max-w-2xl mx-auto mt-8 p-6 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">生成进度</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              workflowStatus.status === 'completed' ? 'bg-green-100 text-green-700' :
              workflowStatus.status === 'failed' ? 'bg-red-100 text-red-700' :
              workflowStatus.status === 'running' ? 'bg-blue-100 text-blue-700' :
              'bg-yellow-100 text-yellow-700'
            }`}>
              {workflowStatus.status === 'completed' ? '已完成' :
               workflowStatus.status === 'failed' ? '失败' :
               workflowStatus.status === 'running' ? '运行中' : '等待中'}
            </span>
          </div>

          {workflowStatus.progress && (
            <div className="space-y-3">
              <div className="flex justify-between text-sm text-gray-600">
                <span>当前步骤: {workflowStatus.progress.current_step || '准备中'}</span>
                <span>{(workflowStatus.progress.rss_feeds_completed || 0) + (workflowStatus.progress.websites_completed || 0)} / {(workflowStatus.progress.total_rss_feeds || 0) + (workflowStatus.progress.total_websites || 0)}</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${((workflowStatus.progress.total_rss_feeds || 0) + (workflowStatus.progress.total_websites || 0)) > 0 ? 
                      (((workflowStatus.progress.rss_feeds_completed || 0) + (workflowStatus.progress.websites_completed || 0)) / 
                       ((workflowStatus.progress.total_rss_feeds || 0) + (workflowStatus.progress.total_websites || 0))) * 100 : 0}%` 
                  }}
                ></div>
              </div>

              {workflowStatus.progress.sources_detail && workflowStatus.progress.sources_detail.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">处理信源:</p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {workflowStatus.progress.sources_detail.slice(-3).map((source, index) => (
                      <li key={index} className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          source.status === 'completed' ? 'bg-green-500' :
                          source.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                        }`}></div>
                        {source.title}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {workflowStatus.results && (
            <div className="mt-4 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>抓取内容: {Number((workflowStatus.results as Record<string, unknown>).crawled_items) || 0} 项</span>
                <span>处理内容: {Number((workflowStatus.results as Record<string, unknown>).processed_items) || 0} 项</span>
                <span>生成文章: {Number((workflowStatus.results as Record<string, unknown>).articles_generated) || 0} 篇</span>
              </div>
            </div>
          )}

          {workflowStatus.error_message && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700">
                <strong>错误:</strong> {workflowStatus.error_message}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}