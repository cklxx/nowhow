'use client'

import React, { useState, useEffect } from 'react'
import { 
  Source, CreateSourceRequest, SourceType, ContentType, 
  AnalysisResult, MockAuthResult 
} from '@/types'
import { 
  getSources, createSource, updateSource, deleteSource, 
  analyzeWebpage, findMockAuth, getSourceStats 
} from '@/lib/api'

interface SourceManagerProps {
  onSourcesChange?: () => void
}

export default function SourceManager({ onSourcesChange }: SourceManagerProps) {
  const [sources, setSources] = useState<Source[]>([])
  const [stats, setStats] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [mockAuthResult, setMockAuthResult] = useState<MockAuthResult | null>(null)

  // 新增信源表单状态
  const [newSource, setNewSource] = useState<CreateSourceRequest>({
    name: '',
    url: '',
    type: 'rss',
    category: 'general'
  })

  useEffect(() => {
    loadSources()
    loadStats()
  }, [])

  const loadSources = async () => {
    try {
      const data = await getSources(true)
      setSources(data)
    } catch (error) {
      console.error('加载信源失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await getSourceStats()
      setStats(data)
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createSource(newSource)
      setNewSource({
        name: '',
        url: '',
        type: SourceType.WEBSITE,
        content_type: ContentType.ARTICLE,
        description: ''
      })
      setShowAddForm(false)
      loadSources()
      loadStats()
      onSourcesChange?.()
      alert('信源创建成功！')
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      alert(`创建信源失败: ${errorMessage}`)
    }
  }

  const handleAnalyzeWebpage = async (url: string, contentType: ContentType) => {
    setAnalyzing(true)
    try {
      const result = await analyzeWebpage(url, contentType)
      setAnalysisResult(result)
      
      // 如果需要认证，自动查找mock配置
      if (result.requires_auth) {
        const mockResult = await findMockAuth(url)
        setMockAuthResult(mockResult)
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      alert(`AI分析失败: ${errorMessage}`)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleToggleActive = async (source: Source) => {
    try {
      await updateSource(source.id, { active: !source.active })
      loadSources()
      onSourcesChange?.()
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      alert(`更新信源失败: ${errorMessage}`)
    }
  }

  const handleDeleteSource = async (source: Source) => {
    if (source.is_built_in) {
      alert('不能删除内置信源')
      return
    }

    if (confirm(`确定要删除信源 &quot;${source.name}&quot; 吗？`)) {
      try {
        await deleteSource(source.id)
        loadSources()
        loadStats()
        onSourcesChange?.()
        alert('信源删除成功！')
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : '未知错误'
        alert(`删除信源失败: ${errorMessage}`)
      }
    }
  }

  const getSourceTypeText = (type: string) => {
    const types = {
      'rss': 'RSS源',
      'website': '网站',
      'api': 'API'
    }
    return types[type as keyof typeof types] || type
  }

  const getContentTypeText = (type: string) => {
    const types = {
      'article': '文章',
      'blog': '博客',
      'news': '新闻',
      'research': '研究',
      'documentation': '文档'
    }
    return types[type as keyof typeof types] || type
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-lg text-gray-600">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">信源管理</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          {showAddForm ? '取消' : '添加信源'}
        </button>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.total_sources || 0}</div>
          <div className="text-sm text-gray-600">总信源数</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{stats.active_sources || 0}</div>
          <div className="text-sm text-gray-600">活跃信源</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{stats.total_crawls || 0}</div>
          <div className="text-sm text-gray-600">总抓取次数</div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{stats.user_sources || 0}</div>
          <div className="text-sm text-gray-600">用户添加</div>
        </div>
      </div>

      {/* 添加信源表单 */}
      {showAddForm && (
        <form onSubmit={handleCreateSource} className="bg-gray-50 p-6 rounded-lg mb-6 space-y-4">
          <h3 className="text-lg font-medium text-gray-800">添加新信源</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                信源名称 *
              </label>
              <input
                type="text"
                value={newSource.name}
                onChange={(e) => setNewSource({...newSource, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="例如：OpenAI 官方博客"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                信源URL *
              </label>
              <input
                type="url"
                value={newSource.url}
                onChange={(e) => setNewSource({...newSource, url: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                信源类型
              </label>
              <select
                value={newSource.type}
                onChange={(e) => setNewSource({...newSource, type: e.target.value as SourceType})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={SourceType.WEBSITE}>网站</option>
                <option value={SourceType.RSS}>RSS源</option>
                <option value={SourceType.API}>API</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                内容类型
              </label>
              <select
                value={newSource.content_type}
                onChange={(e) => setNewSource({...newSource, content_type: e.target.value as ContentType})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={ContentType.ARTICLE}>文章</option>
                <option value={ContentType.BLOG}>博客</option>
                <option value={ContentType.NEWS}>新闻</option>
                <option value={ContentType.RESEARCH}>研究</option>
                <option value={ContentType.DOCUMENTATION}>文档</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              描述
            </label>
            <textarea
              value={newSource.description}
              onChange={(e) => setNewSource({...newSource, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="简要描述这个信源的内容..."
            />
          </div>

          <div className="flex items-center space-x-4">
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              创建信源
            </button>
            
            {newSource.url && newSource.type === SourceType.WEBSITE && (
              <button
                type="button"
                onClick={() => handleAnalyzeWebpage(newSource.url, (newSource.content_type as ContentType) || ContentType.ARTICLE)}
                disabled={analyzing}
                className="bg-purple-600 text-white px-6 py-2 rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {analyzing ? 'AI分析中...' : 'AI智能分析'}
              </button>
            )}
          </div>

          {/* AI分析结果 */}
          {analysisResult && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">AI分析结果</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">置信度:</span> {(analysisResult.confidence * 100).toFixed(1)}%
                </div>
                <div>
                  <span className="font-medium">内容质量:</span> {(analysisResult.estimated_quality * 100).toFixed(1)}%
                </div>
                <div>
                  <span className="font-medium">需要JavaScript:</span> {analysisResult.requires_js ? '是' : '否'}
                </div>
                <div>
                  <span className="font-medium">需要认证:</span> {analysisResult.requires_auth ? '是' : '否'}
                </div>
                {analysisResult.recommendations.length > 0 && (
                  <div>
                    <span className="font-medium">建议:</span>
                    <ul className="list-disc list-inside ml-4">
                      {analysisResult.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Mock认证结果 */}
          {mockAuthResult?.found && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">找到认证配置</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">来源:</span> {mockAuthResult.sources.join(', ')}
                </div>
                <div>
                  <span className="font-medium">可信度:</span> {(mockAuthResult.confidence * 100).toFixed(1)}%
                </div>
                {mockAuthResult.usage_notes && (
                  <div>
                    <span className="font-medium">使用说明:</span> {mockAuthResult.usage_notes}
                  </div>
                )}
                {mockAuthResult.recommendations.length > 0 && (
                  <div>
                    <span className="font-medium">建议:</span>
                    <ul className="list-disc list-inside ml-4">
                      {mockAuthResult.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </form>
      )}

      {/* 信源列表 */}
      <div className="space-y-4">
        {sources.map((source) => (
          <div
            key={source.id}
            className={`border rounded-lg p-4 ${source.active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-medium text-gray-800">{source.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    source.type === 'rss' ? 'bg-blue-100 text-blue-800' :
                    source.type === 'website' ? 'bg-purple-100 text-purple-800' :
                    'bg-orange-100 text-orange-800'
                  }`}>
                    {getSourceTypeText(source.type)}
                  </span>
                  <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {getContentTypeText(source.content_type || 'article')}
                  </span>
                  {source.is_built_in && (
                    <span className="px-2 py-1 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                      内置
                    </span>
                  )}
                  {source.ai_analyzed && (
                    <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                      AI已分析
                    </span>
                  )}
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {source.url}
                  </a>
                </div>
                
                {source.description && (
                  <div className="text-sm text-gray-600 mb-2">
                    {source.description}
                  </div>
                )}
                
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>抓取: {source.crawl_count}次</span>
                  <span>成功: {source.success_count}次</span>
                  <span>失败: {source.error_count}次</span>
                  {source.ai_confidence && (
                    <span>AI置信度: {(source.ai_confidence * 100).toFixed(1)}%</span>
                  )}
                  {source.last_crawled && (
                    <span>最后抓取: {new Date(source.last_crawled).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => handleToggleActive(source)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    source.active
                      ? 'bg-red-100 text-red-700 hover:bg-red-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {source.active ? '禁用' : '启用'}
                </button>
                
                {!source.is_built_in && (
                  <button
                    onClick={() => handleDeleteSource(source)}
                    className="px-3 py-1 rounded text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                  >
                    删除
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {sources.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          暂无信源配置，点击&ldquo;添加信源&rdquo;开始配置。
        </div>
      )}
    </div>
  )
}