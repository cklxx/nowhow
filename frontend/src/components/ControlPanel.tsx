'use client'

import React from 'react'
import { WorkflowStatus } from '@/types'
import CrawlingProgress from './CrawlingProgress'

interface ControlPanelProps {
  onStartWorkflow: () => void
  onLoadArticles: () => void
  loading: boolean
  workflowStatus: WorkflowStatus | null
}

export default function ControlPanel({ 
  onStartWorkflow, 
  onLoadArticles, 
  loading, 
  workflowStatus 
}: ControlPanelProps) {
  const handleStartWorkflow = () => {
    onStartWorkflow()
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-2xl font-semibold mb-4">控制面板</h2>
      
      <div className="flex gap-4">
        <button
          onClick={handleStartWorkflow}
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
          onClick={onLoadArticles}
          className="px-6 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
        >
          加载最新文章
        </button>
      </div>

      {/* 工作流状态 */}
      {workflowStatus && (
        <div className="mt-6 space-y-4">
          {/* Basic Status */}
          <div className="p-4 bg-gray-50 rounded-md">
            <h3 className="font-medium text-gray-900">工作流状态</h3>
            <p className="text-sm text-gray-600">
              ID: {workflowStatus.id}
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
                <p>抓取项目: {Number((workflowStatus.results as Record<string, unknown>).crawled_items) || 0}</p>
                <p>处理项目: {Number((workflowStatus.results as Record<string, unknown>).processed_items) || 0}</p>
                <p>生成文章: {Number((workflowStatus.results as Record<string, unknown>).articles_generated) || 0}</p>
              </div>
            )}
          </div>

          {/* Crawling Progress */}
          {workflowStatus.progress && (
            <CrawlingProgress progress={workflowStatus.progress} />
          )}
        </div>
      )}
    </div>
  )
}