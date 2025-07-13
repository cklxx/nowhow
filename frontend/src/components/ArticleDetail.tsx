'use client'

import React from 'react'
import { Article } from '@/types'

interface ArticleDetailProps {
  article: Article
  onBack: () => void
}

export default function ArticleDetail({ article, onBack }: ArticleDetailProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return '未知时间'
    try {
      return new Date(dateString).toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return '未知时间'
    }
  }

  const formatContent = (content: string) => {
    // 简单的段落分割和格式化
    return content
      .split('\n')
      .filter(line => line.trim())
      .map((paragraph, index) => (
        <p key={index} className="mb-4 text-gray-700 leading-relaxed">
          {paragraph.trim()}
        </p>
      ))
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* 返回按钮 */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <button
          onClick={onBack}
          className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回文章列表
        </button>
      </div>

      {/* 文章头部 */}
      <div className="px-6 py-8">
        <div className="mb-6">
          <div className="flex items-start justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900 leading-tight flex-1">
              {article.title || '无标题'}
            </h1>
            <span className="px-4 py-2 bg-blue-100 text-blue-800 text-sm font-medium rounded-full ml-4 whitespace-nowrap">
              {article.category || '未分类'}
            </span>
          </div>

          {/* 文章元信息 */}
          <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500 mb-6">
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {formatDate(article.created_at)}
            </div>
            
            {article.word_count && (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {article.word_count} 字
              </div>
            )}

            {article.sources && article.sources.length > 0 && (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                {article.sources.length} 个信源
              </div>
            )}

            {article.quality_score && (
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
                质量评分: {(article.quality_score * 100).toFixed(0)}%
              </div>
            )}
          </div>

          {/* 文章摘要 */}
          {article.summary && (
            <div className="bg-blue-50 p-6 rounded-lg mb-8">
              <h2 className="text-lg font-semibold text-blue-900 mb-3">文章摘要</h2>
              <p className="text-blue-800 leading-relaxed">{article.summary}</p>
            </div>
          )}

          {/* 标签 */}
          {article.tags && article.tags.length > 0 && (
            <div className="mb-8">
              <h3 className="text-sm font-medium text-gray-700 mb-3">相关标签</h3>
              <div className="flex flex-wrap gap-2">
                {article.tags.map((tag, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full hover:bg-gray-200 transition-colors"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 文章正文 */}
        <div className="prose prose-lg max-w-none">
          <div className="text-gray-800 leading-relaxed space-y-4">
            {article.content ? formatContent(article.content) : (
              <p className="text-gray-500 italic">暂无文章内容</p>
            )}
          </div>
        </div>

        {/* 信源链接 */}
        {(article.url || (article.sources && article.sources.length > 0)) && (
          <div className="mt-12 pt-8 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">参考信源</h3>
            <div className="space-y-4">
              {article.url && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-2">原文链接</h4>
                  <a 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-800 underline transition-colors"
                  >
                    {article.url}
                    <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              )}

              {article.sources && article.sources.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-3">其他参考信源</h4>
                  <ul className="space-y-2">
                    {article.sources.map((source, index) => (
                      <li key={index} className="flex items-start">
                        <span className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3"></span>
                        {typeof source === 'string' ? (
                          source.startsWith('http') ? (
                            <a 
                              href={source} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 underline break-all transition-colors"
                            >
                              {source}
                            </a>
                          ) : (
                            <span className="text-gray-700">{source}</span>
                          )
                        ) : (
                          <span className="text-gray-700">
                            {source?.title || source?.url || JSON.stringify(source)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}