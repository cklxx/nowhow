'use client'

import React from 'react'
import { Article } from '@/types'

interface ArticleListProps {
  articles: Article[]
}

export default function ArticleList({ articles }: ArticleListProps) {
  return (
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
  )
}