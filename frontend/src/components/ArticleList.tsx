'use client'

import React from 'react'
import { Article } from '@/types'

interface ArticleListProps {
  articles: Article[]
  onArticleClick: (article: Article) => void
}

export default function ArticleList({ articles, onArticleClick }: ArticleListProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return '刚刚'
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffHours / 24)
      
      if (diffDays > 0) {
        return `${diffDays} 天前`
      } else if (diffHours > 0) {
        return `${diffHours} 小时前`
      } else {
        return '刚刚'
      }
    } catch {
      return '刚刚'
    }
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">
          发现的文章 ({articles.length})
        </h2>
        {articles.length > 0 && (
          <p className="text-sm text-gray-500">
            点击任意文章查看详细内容
          </p>
        )}
      </div>
      
      {articles.length === 0 ? (
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无文章</h3>
            <p className="text-gray-500">输入一个感兴趣的主题，开始探索相关内容</p>
          </div>
        </div>
      ) : (
        <div className="grid gap-6">
          {articles.map((article, index) => (
            <article 
              key={index} 
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 cursor-pointer border border-gray-200 hover:border-blue-300 group"
              onClick={() => onArticleClick(article)}
            >
              <div className="p-6">
                {/* 文章头部 */}
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-xl font-semibold text-gray-900 flex-1 group-hover:text-blue-700 transition-colors pr-4 leading-tight">
                    {article.title || '无标题'}
                  </h3>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                      {article.category || '未分类'}
                    </span>
                    {article.quality_score && article.quality_score > 0.8 && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                        高质量
                      </span>
                    )}
                  </div>
                </div>
                
                {/* 文章摘要 */}
                {article.summary && (
                  <p className="text-gray-600 mb-4 leading-relaxed">
                    {truncateText(article.summary, 200)}
                  </p>
                )}
                
                {/* 标签 */}
                {article.tags && article.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {article.tags.slice(0, 5).map((tag, tagIndex) => (
                      <span 
                        key={tagIndex}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full hover:bg-blue-50 hover:text-blue-700 transition-colors"
                      >
                        #{tag}
                      </span>
                    ))}
                    {article.tags.length > 5 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">
                        +{article.tags.length - 5}
                      </span>
                    )}
                  </div>
                )}
                
                {/* 文章元信息 */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center space-x-4">
                    {article.word_count && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {article.word_count} 字
                      </div>
                    )}
                    
                    {article.sources && article.sources.length > 0 && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        {article.sources.length} 个信源
                      </div>
                    )}

                    {article.quality_score && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                        {(article.quality_score * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatDate(article.created_at)}
                  </div>
                </div>

                {/* 阅读更多指示 */}
                <div className="flex items-center justify-end mt-4 pt-4 border-t border-gray-100">
                  <span className="text-blue-600 text-sm font-medium group-hover:text-blue-700 transition-colors flex items-center">
                    阅读全文
                    <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}