import { CrawlingProgress } from '@/types';

interface CrawlingProgressProps {
  progress: CrawlingProgress;
}

export default function CrawlingProgressComponent({ progress }: CrawlingProgressProps) {
  const {
    status,
    total_expected,
    total_rss_feeds,
    total_websites,
    rss_feeds_completed,
    websites_completed,
    articles_found,
    current_source,
    sources_detail,
    total_actual,
    rss_articles_count,
    web_pages_count
  } = progress;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'starting': return '🎯';
      case 'crawling_rss': return '📡';
      case 'crawling_websites': return '🌐';
      case 'completed': return '✅';
      default: return '⏳';
    }
  };

  const getSourceStatusIcon = (sourceStatus: string) => {
    switch (sourceStatus) {
      case 'processing': return '⏳';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'starting': return '开始抓取内容';
      case 'crawling_rss': return '抓取RSS源';
      case 'crawling_websites': return '抓取网站';
      case 'completed': return '抓取完成';
      default: return '处理中';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      <div className="flex items-center space-x-2">
        <span className="text-2xl">{getStatusIcon(status)}</span>
        <h3 className="text-lg font-semibold text-gray-800">
          {getStatusText(status)}
        </h3>
      </div>

      {/* Overall Progress */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{total_expected || 0}</div>
            <div className="text-gray-600">预计抓取</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{articles_found || 0}</div>
            <div className="text-gray-600">已获取文章</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{rss_feeds_completed || 0}/{total_rss_feeds || 0}</div>
            <div className="text-gray-600">RSS源</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{websites_completed || 0}/{total_websites || 0}</div>
            <div className="text-gray-600">网站</div>
          </div>
        </div>
      </div>

      {/* Current Source */}
      {current_source && status !== 'completed' && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="text-sm text-blue-800">
            <strong>当前抓取:</strong> {current_source}
          </div>
        </div>
      )}

      {/* Sources Detail */}
      {sources_detail && sources_detail.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-800">抓取详情</h4>
          <div className="max-h-60 overflow-y-auto space-y-2">
            {sources_detail.map((source, index) => (
              <div
                key={index}
                className={`border rounded-lg p-3 ${
                  source.status === 'completed' ? 'bg-green-50 border-green-200' :
                  source.status === 'error' ? 'bg-red-50 border-red-200' :
                  'bg-yellow-50 border-yellow-200'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <span className="text-lg">
                    {getSourceStatusIcon(source.status)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        source.type === 'rss' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                      }`}>
                        {source.type === 'rss' ? 'RSS' : '网站'}
                      </span>
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {source.title || source.url}
                      </span>
                    </div>
                    
                    <div className="text-xs text-gray-600 mt-1 break-all">
                      {source.url}
                    </div>
                    
                    {source.description && (
                      <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {source.description}
                      </div>
                    )}
                    
                    {source.status === 'completed' && (
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-600">
                        {source.articles_count !== undefined && (
                          <span>📄 {source.articles_count} 篇文章</span>
                        )}
                        {source.content_length !== undefined && (
                          <span>📝 {source.content_length} 字符</span>
                        )}
                      </div>
                    )}
                    
                    {source.status === 'error' && source.error && (
                      <div className="text-xs text-red-600 mt-1">
                        错误: {source.error}
                      </div>
                    )}
                    
                    {/* Show article titles for RSS sources */}
                    {source.articles && source.articles.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <div className="text-xs font-medium text-gray-700">文章列表:</div>
                        {source.articles.slice(0, 3).map((article, articleIndex) => (
                          <div key={articleIndex} className="text-xs text-gray-600 pl-2 border-l-2 border-gray-200">
                            📄 {article.title.length > 50 ? article.title.substring(0, 50) + '...' : article.title}
                          </div>
                        ))}
                        {source.articles.length > 3 && (
                          <div className="text-xs text-gray-500 pl-2">
                            ... 还有 {source.articles.length - 3} 篇文章
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Final Summary */}
      {status === 'completed' && total_actual !== undefined && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">🎉</span>
            <span className="font-medium text-green-800">抓取完成!</span>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{rss_articles_count || 0}</div>
              <div className="text-gray-600">RSS文章</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{web_pages_count || 0}</div>
              <div className="text-gray-600">网页</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{total_actual}</div>
              <div className="text-gray-600">总计</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}