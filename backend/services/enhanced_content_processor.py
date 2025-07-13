"""
增强的内容处理器 - 支持句子级别分析和知识提取
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from core.interfaces import IContentProcessor, IModelService
from services.knowledge_extractor import KnowledgeExtractor
from models.knowledge_models import (
    SourceDocumentAnalysis, KnowledgeClaim, SourceReference,
    EnhancedSentence, EnhancedParagraph
)
from database.connection import get_database_manager
from database.models import (
    KnowledgeClaimModel, SourceReferenceModel, DocumentAnalysisModel,
    ProcessedContentModel
)

class EnhancedContentProcessor(IContentProcessor):
    """增强的内容处理器"""
    
    def __init__(self, model_service: IModelService):
        self.model_service = model_service
        self.knowledge_extractor = KnowledgeExtractor(model_service)
        self.db_manager = get_database_manager()
    
    async def process_content(self, content: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理内容并提取知识"""
        
        # 基本内容处理
        basic_result = await self._basic_content_processing(content, config)
        
        # 如果内容质量足够高，进行深度知识提取
        if basic_result.get('relevance_score', 0) >= 0.6:
            # 进行文档级别的知识分析
            doc_analysis = await self.knowledge_extractor.analyze_document(
                content.get('content', ''),
                {
                    'id': content.get('id', ''),
                    'url': content.get('url', ''),
                    'title': content.get('title', ''),
                    'author': content.get('author'),
                    'publish_date': content.get('publish_date')
                }
            )
            
            # 保存分析结果到数据库
            analysis_id = await self._save_document_analysis(doc_analysis)
            
            # 保存知识声明
            claim_ids = await self._save_knowledge_claims(doc_analysis)
            
            # 更新基本结果
            basic_result.update({
                'document_analysis_id': analysis_id,
                'knowledge_claims_ids': claim_ids,
                'total_claims': len(claim_ids),
                'executive_summary': doc_analysis.executive_summary,
                'key_insights': doc_analysis.key_insights,
                'knowledge_density': doc_analysis.overall_quality,
                'credibility_score': doc_analysis.credibility_score,
                'enhanced_processing': True
            })
        else:
            basic_result['enhanced_processing'] = False
        
        return basic_result
    
    async def _basic_content_processing(self, content: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """基本内容处理（继承原有逻辑）"""
        
        text_content = content.get('content', '')
        title = content.get('title', '')
        
        if not text_content.strip():
            return {
                'success': False,
                'error': 'Empty content',
                'relevance_score': 0.0
            }
        
        # AI分析内容
        analysis_prompt = f"""
        请分析以下内容的相关性和质量:

        标题: {title}
        内容: {text_content[:2000]}...

        请按以下JSON格式返回分析结果:
        {{
            "relevance_score": 0.0-1.0,
            "quality_score": 0.0-1.0,
            "category": "分类",
            "summary": "内容摘要",
            "key_topics": ["主题1", "主题2"],
            "sentiment": "positive|negative|neutral",
            "language": "zh|en",
            "content_type": "news|research|opinion|tutorial|review"
        }}

        评分标准:
        - relevance_score: 内容对AI/技术主题的相关性
        - quality_score: 内容的整体质量和可信度
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            # 构建处理结果
            result = {
                'success': True,
                'title': title,
                'content': text_content,
                'url': content.get('url', ''),
                'source_id': content.get('source_id', ''),
                'crawl_result_id': content.get('crawl_result_id'),
                
                # AI分析结果
                'relevance_score': analysis.get('relevance_score', 0.5),
                'quality_score': analysis.get('quality_score', 0.5),
                'category': analysis.get('category', 'unknown'),
                'summary': analysis.get('summary', ''),
                'key_topics': analysis.get('key_topics', []),
                'sentiment': analysis.get('sentiment', 'neutral'),
                'language': analysis.get('language', 'zh'),
                'content_type': analysis.get('content_type', 'unknown'),
                
                # 基本统计
                'word_count': len(text_content.split()),
                'char_count': len(text_content),
                'processed_at': datetime.now().isoformat(),
                'processing_method': 'enhanced_ai_analysis'
            }
            
            return result
            
        except Exception as e:
            print(f"内容处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'relevance_score': 0.0
            }
    
    async def _save_document_analysis(self, doc_analysis: SourceDocumentAnalysis) -> str:
        """保存文档分析结果到数据库"""
        
        session = self.db_manager.get_sync_session()
        try:
            # 转换段落和句子分析为JSON格式
            paragraphs_data = []
            sentences_data = []
            
            for para in doc_analysis.paragraphs:
                para_data = {
                    'paragraph_index': para.paragraph_index,
                    'paragraph_text': para.paragraph_text,
                    'main_topic': para.main_topic,
                    'key_points': para.key_points,
                    'summary': para.summary,
                    'coherence_score': para.coherence_score,
                    'relevance_score': para.relevance_score,
                    'knowledge_density': para.knowledge_density,
                    'fact_count': para.fact_count
                }
                paragraphs_data.append(para_data)
                
                # 添加句子数据
                for sent in para.sentences:
                    sent_data = {
                        'paragraph_index': para.paragraph_index,
                        'sentence_index': sent.sentence_index,
                        'sentence_text': sent.sentence_text,
                        'char_start': sent.char_start,
                        'char_end': sent.char_end,
                        'word_count': sent.word_count,
                        'importance_score': sent.importance_score,
                        'informativeness': sent.informativeness,
                        'novelty_score': sent.novelty_score,
                        'knowledge_claims_count': len(sent.knowledge_claims),
                        'named_entities': sent.named_entities
                    }
                    sentences_data.append(sent_data)
            
            # 创建文档分析记录
            analysis_model = DocumentAnalysisModel(
                document_id=doc_analysis.document_id,
                source_url=doc_analysis.source_url,
                title=doc_analysis.title,
                author=doc_analysis.author,
                publish_date=doc_analysis.publish_date,
                paragraphs_analysis=paragraphs_data,
                sentences_analysis=sentences_data,
                executive_summary=doc_analysis.executive_summary,
                key_insights=doc_analysis.key_insights,
                overall_quality=doc_analysis.overall_quality,
                credibility_score=doc_analysis.credibility_score,
                total_paragraphs=len(doc_analysis.paragraphs),
                total_sentences=len(sentences_data),
                total_claims=sum(len(p.sentences) for p in doc_analysis.paragraphs for s in p.sentences for c in s.knowledge_claims)
            )
            
            session.add(analysis_model)
            session.commit()
            
            return analysis_model.id
            
        finally:
            session.close()
    
    async def _save_knowledge_claims(self, doc_analysis: SourceDocumentAnalysis) -> List[str]:
        """保存知识声明到数据库"""
        
        session = self.db_manager.get_sync_session()
        try:
            claim_ids = []
            
            # 保存文档级别的知识声明
            for claim in doc_analysis.document_claims:
                claim_id = await self._save_single_claim(claim, session)
                claim_ids.append(claim_id)
            
            # 保存句子级别的知识声明
            for para in doc_analysis.paragraphs:
                for sent in para.sentences:
                    for claim in sent.knowledge_claims:
                        claim_id = await self._save_single_claim(claim, session)
                        claim_ids.append(claim_id)
            
            session.commit()
            return claim_ids
            
        finally:
            session.close()
    
    async def _save_single_claim(self, claim: KnowledgeClaim, session) -> str:
        """保存单个知识声明"""
        
        # 创建知识声明记录
        claim_model = KnowledgeClaimModel(
            claim_text=claim.claim_text,
            knowledge_type=claim.knowledge_type.value,
            confidence_score=claim.confidence_score,
            confidence_level=claim.confidence_level.value,
            quality_score=claim.quality_score,
            topic=claim.topic,
            keywords=claim.keywords,
            entities=claim.entities,
            semantic_embedding=claim.semantic_embedding,
            fact_check_status=claim.fact_check_status,
            verification_sources=claim.verification_sources,
            temporal_info=claim.temporal_info,
            extraction_method=claim.extraction_method,
            processor_version=claim.processor_version
        )
        
        session.add(claim_model)
        session.flush()  # 获取ID
        
        # 保存来源引用
        for source_ref in claim.source_references:
            ref_model = SourceReferenceModel(
                knowledge_claim_id=claim_model.id,
                source_id=source_ref.source_id,
                source_url=source_ref.source_url,
                source_title=source_ref.source_title,
                paragraph_index=source_ref.paragraph_index,
                paragraph_text=source_ref.paragraph_text,
                sentence_index=source_ref.sentence_index,
                sentence_text=source_ref.sentence_text,
                char_start=source_ref.char_start,
                char_end=source_ref.char_end,
                context_before=source_ref.context_before,
                context_after=source_ref.context_after,
                extraction_timestamp=source_ref.extraction_timestamp,
                relevance_score=source_ref.relevance_score
            )
            session.add(ref_model)
        
        return claim_model.id
    
    async def get_knowledge_claims_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """根据主题获取知识声明"""
        
        session = self.db_manager.get_sync_session()
        try:
            claims = session.query(KnowledgeClaimModel).filter(
                KnowledgeClaimModel.topic.contains(topic)
            ).order_by(
                KnowledgeClaimModel.quality_score.desc(),
                KnowledgeClaimModel.confidence_score.desc()
            ).limit(limit).all()
            
            result = []
            for claim in claims:
                # 获取来源引用
                refs = session.query(SourceReferenceModel).filter(
                    SourceReferenceModel.knowledge_claim_id == claim.id
                ).all()
                
                claim_data = {
                    'id': claim.id,
                    'claim_text': claim.claim_text,
                    'knowledge_type': claim.knowledge_type,
                    'confidence_score': claim.confidence_score,
                    'confidence_level': claim.confidence_level,
                    'quality_score': claim.quality_score,
                    'topic': claim.topic,
                    'keywords': claim.keywords,
                    'entities': claim.entities,
                    'fact_check_status': claim.fact_check_status,
                    'created_at': claim.created_at.isoformat(),
                    'source_references': [
                        {
                            'source_url': ref.source_url,
                            'source_title': ref.source_title,
                            'paragraph_index': ref.paragraph_index,
                            'sentence_index': ref.sentence_index,
                            'sentence_text': ref.sentence_text,
                            'relevance_score': ref.relevance_score
                        }
                        for ref in refs
                    ]
                }
                result.append(claim_data)
            
            return result
            
        finally:
            session.close()
    
    async def search_knowledge_claims(self, query: str, filters: Dict[str, Any] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索知识声明"""
        
        session = self.db_manager.get_sync_session()
        try:
            q = session.query(KnowledgeClaimModel)
            
            # 文本搜索
            if query:
                q = q.filter(
                    KnowledgeClaimModel.claim_text.contains(query) |
                    KnowledgeClaimModel.topic.contains(query)
                )
            
            # 应用过滤器
            if filters:
                if filters.get('knowledge_type'):
                    q = q.filter(KnowledgeClaimModel.knowledge_type == filters['knowledge_type'])
                if filters.get('confidence_level'):
                    q = q.filter(KnowledgeClaimModel.confidence_level == filters['confidence_level'])
                if filters.get('min_quality'):
                    q = q.filter(KnowledgeClaimModel.quality_score >= filters['min_quality'])
                if filters.get('fact_check_status'):
                    q = q.filter(KnowledgeClaimModel.fact_check_status == filters['fact_check_status'])
            
            claims = q.order_by(
                KnowledgeClaimModel.quality_score.desc(),
                KnowledgeClaimModel.confidence_score.desc()
            ).limit(limit).all()
            
            # 转换为字典格式（简化版）
            result = []
            for claim in claims:
                claim_data = {
                    'id': claim.id,
                    'claim_text': claim.claim_text,
                    'knowledge_type': claim.knowledge_type,
                    'confidence_score': claim.confidence_score,
                    'quality_score': claim.quality_score,
                    'topic': claim.topic,
                    'keywords': claim.keywords,
                    'entities': claim.entities,
                    'created_at': claim.created_at.isoformat()
                }
                result.append(claim_data)
            
            return result
            
        finally:
            session.close()
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        
        session = self.db_manager.get_sync_session()
        try:
            # 知识声明统计
            total_claims = session.query(KnowledgeClaimModel).count()
            high_quality_claims = session.query(KnowledgeClaimModel).filter(
                KnowledgeClaimModel.quality_score >= 0.8
            ).count()
            
            # 按类型统计
            from sqlalchemy import func
            type_stats = session.query(
                KnowledgeClaimModel.knowledge_type,
                func.count(KnowledgeClaimModel.id)
            ).group_by(KnowledgeClaimModel.knowledge_type).all()
            
            # 文档分析统计
            total_documents = session.query(DocumentAnalysisModel).count()
            
            return {
                'total_claims': total_claims,
                'high_quality_claims': high_quality_claims,
                'quality_ratio': high_quality_claims / max(1, total_claims),
                'claims_by_type': {t: c for t, c in type_stats},
                'total_analyzed_documents': total_documents,
                'average_claims_per_document': total_claims / max(1, total_documents)
            }
            
        finally:
            session.close()
    
    # 实现接口要求的方法
    async def analyze_relevance(self, content: str, context: Dict[str, Any] = None) -> float:
        """分析内容相关性"""
        result = await self._basic_content_processing({'content': content}, {})
        return result.get('relevance_score', 0.0)
    
    async def extract_key_information(self, content: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """提取关键信息"""
        result = await self._basic_content_processing({'content': content}, config)
        return {
            'summary': result.get('summary', ''),
            'key_topics': result.get('key_topics', []),
            'category': result.get('category', ''),
            'sentiment': result.get('sentiment', 'neutral')
        }
    
    async def categorize_content(self, content: str, categories: List[str] = None) -> str:
        """内容分类"""
        result = await self._basic_content_processing({'content': content}, {})
        return result.get('category', 'unknown')
    
    async def filter_by_relevance(self, content_list: List[str], threshold: float = 0.6) -> List[str]:
        """按相关性过滤内容"""
        filtered_content = []
        
        for content in content_list:
            relevance = await self.analyze_relevance(content)
            if relevance >= threshold:
                filtered_content.append(content)
        
        return filtered_content
    
    async def process_batch(self, content_batch: List[Dict[str, Any]], 
                          config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """批量处理内容"""
        results = []
        
        for content in content_batch:
            try:
                result = await self.process_content(content, config)
                results.append(result)
            except Exception as e:
                print(f"批量处理失败: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'content': content
                })
        
        return results