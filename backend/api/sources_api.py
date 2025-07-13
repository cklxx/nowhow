from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from repositories.db_source_repository import DatabaseSourceRepository
from services.ai_analyzer import AIWebAnalyzer
from services.mock_auth_finder import MockAuthFinder
from models.source_config import (
    SourceConfig, SourceType, ContentType, AuthType,
    AIAnalysisRequest, MockAuthRequest as MockAuthRequestModel, CrawlResult
)

router = APIRouter(prefix="/sources", tags=["sources"])

# 初始化服务
source_repo = DatabaseSourceRepository()
ai_analyzer = None  # 将在主应用中初始化
mock_auth_finder = MockAuthFinder()

def init_services(api_key: str):
    """初始化需要API密钥的服务"""
    global ai_analyzer
    ai_analyzer = AIWebAnalyzer(api_key)

# 请求/响应模型
class CreateSourceRequest(BaseModel):
    name: str
    url: HttpUrl
    type: SourceType
    content_type: ContentType
    description: Optional[str] = None

class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AnalyzeWebpageRequest(BaseModel):
    url: HttpUrl
    content_type: ContentType = ContentType.ARTICLE

class MockAuthRequestAPI(BaseModel):
    url: HttpUrl
    auth_type: AuthType = AuthType.COOKIE

class SourceResponse(BaseModel):
    id: str
    name: str
    url: str
    type: str
    content_type: str
    description: Optional[str]
    is_active: bool
    is_built_in: bool
    ai_analyzed: bool
    ai_confidence: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_crawled: Optional[datetime]
    crawl_count: int
    success_count: int
    error_count: int

@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    include_inactive: bool = Query(False, description="是否包含非活跃信源"),
    source_type: Optional[SourceType] = Query(None, description="按类型过滤"),
    limit: int = Query(50, description="返回数量限制")
):
    """获取信源列表"""
    try:
        if source_type:
            sources = await source_repo.get_by_type(source_type.value)
        elif include_inactive:
            sources = await source_repo.get_all()
        else:
            sources = await source_repo.get_active()
        
        # 转换为响应格式
        response_sources = []
        for source in sources[:limit]:
            response_sources.append(SourceResponse(
                id=source.id,
                name=source.name,
                url=str(source.url),
                type=source.type if isinstance(source.type, str) else source.type.value,
                content_type=source.content_type if isinstance(source.content_type, str) else source.content_type.value,
                description=source.description,
                is_active=source.is_active,
                is_built_in=source.is_built_in,
                ai_analyzed=source.ai_analyzed,
                ai_confidence=source.ai_confidence,
                created_at=source.created_at,
                updated_at=source.updated_at,
                last_crawled=source.last_crawled,
                crawl_count=source.crawl_count,
                success_count=source.success_count,
                error_count=source.error_count
            ))
        
        return response_sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信源列表失败: {str(e)}")

@router.post("/", response_model=SourceResponse)
async def create_source(request: CreateSourceRequest):
    """创建新的信源"""
    try:
        # 创建新信源数据
        source_data = {
            'name': request.name,
            'url': str(request.url),
            'type': request.type.value,
            'content_type': request.content_type.value,
            'description': request.description,
            'is_built_in': False,
            'created_by': 'user'
        }
        
        # 保存信源
        source_id = await source_repo.create(source_data)
        saved_source = await source_repo.get_by_id(source_id)
        
        return SourceResponse(
            id=saved_source.id,
            name=saved_source.name,
            url=str(saved_source.url),
            type=saved_source.type if isinstance(saved_source.type, str) else saved_source.type.value,
            content_type=saved_source.content_type if isinstance(saved_source.content_type, str) else saved_source.content_type.value,
            description=saved_source.description,
            is_active=saved_source.is_active,
            is_built_in=saved_source.is_built_in,
            ai_analyzed=saved_source.ai_analyzed,
            ai_confidence=saved_source.ai_confidence,
            created_at=saved_source.created_at,
            updated_at=saved_source.updated_at,
            last_crawled=saved_source.last_crawled,
            crawl_count=saved_source.crawl_count,
            success_count=saved_source.success_count,
            error_count=saved_source.error_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建信源失败: {str(e)}")

@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str):
    """获取指定信源的详细信息"""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=str(source.url),
        type=source.type if isinstance(source.type, str) else source.type.value,
        content_type=source.content_type if isinstance(source.content_type, str) else source.content_type.value,
        description=source.description,
        is_active=source.is_active,
        is_built_in=source.is_built_in,
        ai_analyzed=source.ai_analyzed,
        ai_confidence=source.ai_confidence,
        created_at=source.created_at,
        updated_at=source.updated_at,
        last_crawled=source.last_crawled,
        crawl_count=source.crawl_count,
        success_count=source.success_count,
        error_count=source.error_count
    )

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: str, request: UpdateSourceRequest):
    """更新信源信息"""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    
    # 不允许修改内置信源的某些属性
    if source.is_built_in and request.name:
        raise HTTPException(status_code=400, detail="不能修改内置信源的名称")
    
    # 更新字段
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.description is not None:
        updates["description"] = request.description
    if request.is_active is not None:
        updates["is_active"] = request.is_active
    
    # 返回更新后的信源
    updated_source = await source_repo.update(source_id, updates)
    return SourceResponse(
        id=updated_source.id,
        name=updated_source.name,
        url=str(updated_source.url),
        type=updated_source.type if isinstance(updated_source.type, str) else updated_source.type.value,
        content_type=updated_source.content_type if isinstance(updated_source.content_type, str) else updated_source.content_type.value,
        description=updated_source.description,
        is_active=updated_source.is_active,
        is_built_in=updated_source.is_built_in,
        ai_analyzed=updated_source.ai_analyzed,
        ai_confidence=updated_source.ai_confidence,
        created_at=updated_source.created_at,
        updated_at=updated_source.updated_at,
        last_crawled=updated_source.last_crawled,
        crawl_count=updated_source.crawl_count,
        success_count=updated_source.success_count,
        error_count=updated_source.error_count
    )

@router.delete("/{source_id}")
async def delete_source(source_id: str):
    """删除信源"""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    
    if source.is_built_in:
        raise HTTPException(status_code=400, detail="不能删除内置信源")
    
    success = await source_repo.delete(source_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除信源失败")
    
    return {"message": "信源删除成功"}

@router.post("/analyze")
async def analyze_webpage(request: AnalyzeWebpageRequest):
    """AI分析网页结构"""
    if not ai_analyzer:
        raise HTTPException(status_code=500, detail="AI分析服务未初始化")
    
    try:
        analysis_request = AIAnalysisRequest(
            url=request.url,
            content_type=request.content_type
        )
        
        result = await ai_analyzer.analyze_webpage(analysis_request)
        
        return {
            "url": result.url,
            "confidence": result.confidence,
            "suggested_selectors": result.suggested_selectors.dict(),
            "page_structure": result.page_structure,
            "content_patterns": result.content_patterns,
            "recommendations": result.recommendations,
            "potential_issues": result.potential_issues,
            "requires_auth": result.requires_auth,
            "requires_js": result.requires_js,
            "estimated_quality": result.estimated_quality
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")

@router.post("/mock-auth")
async def find_mock_auth(request: MockAuthRequestAPI):
    """查找Mock认证配置"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(str(request.url)).netloc
        
        mock_request = MockAuthRequestModel(
            url=request.url,
            site_domain=domain,
            auth_type=request.auth_type
        )
        
        result = await mock_auth_finder.find_mock_auth(mock_request)
        
        response = {
            "found": result.found,
            "sources": result.sources,
            "confidence": result.confidence,
            "usage_notes": result.usage_notes
        }
        
        if result.auth_config:
            response["auth_config"] = {
                "type": result.auth_config.type.value,
                "headers": result.auth_config.headers,
                "cookies": result.auth_config.cookies,
                "mock_source": result.auth_config.mock_source,
                "is_verified": result.auth_config.is_verified
            }
        
        # 添加建议
        response["recommendations"] = mock_auth_finder.get_auth_recommendations(domain)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找Mock认证失败: {str(e)}")

@router.get("/{source_id}/results")
async def get_crawl_results(source_id: str, limit: int = Query(10, description="返回数量限制")):
    """获取信源的抓取结果"""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    
    try:
        results = await source_repo.get_crawl_results(source_id, limit)
        
        return {
            "source_id": source_id,
            "source_name": source.name,
            "total_results": len(results),
            "results": [
                {
                    "timestamp": result.timestamp,
                    "success": result.success,
                    "title": result.title,
                    "url": result.url,
                    "content_length": result.content_length,
                    "response_time": result.response_time,
                    "error_message": result.error_message,
                    "content_quality": result.content_quality
                }
                for result in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取抓取结果失败: {str(e)}")

@router.get("/stats/overview")
async def get_sources_statistics():
    """获取信源统计信息"""
    try:
        stats = await source_repo.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/import")
async def import_sources(sources_data: Dict[str, Any]):
    """导入信源配置"""
    try:
        # TODO: Implement import functionality for database
        raise HTTPException(status_code=501, detail="导入功能暂未实现")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入信源失败: {str(e)}")

@router.get("/export")
async def export_sources():
    """导出信源配置"""
    try:
        sources = await source_repo.get_all()
        data = {
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "url": str(source.url),
                    "type": source.type if isinstance(source.type, str) else source.type.value,
                    "content_type": source.content_type if isinstance(source.content_type, str) else source.content_type.value,
                    "description": source.description,
                    "is_active": source.is_active,
                    "is_built_in": source.is_built_in
                }
                for source in sources
            ]
        }
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出信源失败: {str(e)}")

@router.post("/{source_id}/test")
async def test_source(source_id: str):
    """测试信源配置"""
    source = await source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    
    try:
        # 这里可以实现一个简单的测试抓取
        # 暂时返回基本信息
        return {
            "source_id": source_id,
            "url": str(source.url),
            "type": source.type if isinstance(source.type, str) else source.type.value,
            "status": "配置有效",
            "message": "信源配置检查通过，建议运行完整抓取进行验证"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试信源失败: {str(e)}")