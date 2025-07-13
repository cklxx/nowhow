"""
知识提取和来源追踪服务
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from models.knowledge_models import (
    KnowledgeClaim, KnowledgeType, ConfidenceLevel, SourceReference,
    EnhancedSentence, EnhancedParagraph, SourceDocumentAnalysis
)
from core.interfaces import IModelService

class KnowledgeExtractor:
    """知识提取器"""
    
    def __init__(self, model_service: IModelService):
        self.model_service = model_service
        self.sentence_splitter = SentenceSplitter()
        
    async def analyze_document(self, content: str, source_info: Dict[str, Any]) -> SourceDocumentAnalysis:
        """分析整个文档并提取知识"""
        
        # 分割段落
        paragraphs_text = self._split_paragraphs(content)
        
        # 分析每个段落
        paragraphs = []
        all_claims = []
        
        for para_idx, para_text in enumerate(paragraphs_text):
            if para_text.strip():
                enhanced_para = await self._analyze_paragraph(para_text, para_idx, source_info)
                paragraphs.append(enhanced_para)
                
                # 收集段落中的知识声明
                for sentence in enhanced_para.sentences:
                    all_claims.extend(sentence.knowledge_claims)
        
        # 生成文档级别摘要和洞察
        exec_summary = await self._generate_executive_summary(content, source_info)
        key_insights = await self._extract_key_insights(all_claims)
        
        # 评估文档质量
        quality_scores = await self._assess_document_quality(content, all_claims)
        
        return SourceDocumentAnalysis(
            document_id=source_info.get('id', ''),
            source_url=source_info.get('url', ''),
            title=source_info.get('title', ''),
            author=source_info.get('author'),
            publish_date=source_info.get('publish_date'),
            paragraphs=paragraphs,
            document_claims=await self._extract_document_level_claims(content, source_info),
            executive_summary=exec_summary,
            key_insights=key_insights,
            overall_quality=quality_scores['overall_quality'],
            credibility_score=quality_scores['credibility_score']
        )
    
    async def _analyze_paragraph(self, paragraph_text: str, para_idx: int, source_info: Dict[str, Any]) -> EnhancedParagraph:
        """分析单个段落"""
        
        # 分割句子
        sentences_text = self.sentence_splitter.split(paragraph_text)
        
        # 分析每个句子
        sentences = []
        char_offset = 0
        
        for sent_idx, sent_text in enumerate(sentences_text):
            if sent_text.strip():
                char_start = paragraph_text.find(sent_text, char_offset)
                char_end = char_start + len(sent_text)
                char_offset = char_end
                
                enhanced_sent = await self._analyze_sentence(
                    sent_text, sent_idx, para_idx, char_start, char_end, source_info
                )
                sentences.append(enhanced_sent)
        
        # 段落级别分析
        para_analysis = await self._analyze_paragraph_content(paragraph_text)
        
        return EnhancedParagraph(
            paragraph_text=paragraph_text,
            paragraph_index=para_idx,
            sentences=sentences,
            main_topic=para_analysis['main_topic'],
            key_points=para_analysis['key_points'],
            summary=para_analysis['summary'],
            coherence_score=para_analysis['coherence_score'],
            relevance_score=para_analysis['relevance_score'],
            knowledge_density=para_analysis['knowledge_density'],
            fact_count=len([s for s in sentences for c in s.knowledge_claims if c.knowledge_type == KnowledgeType.FACT])
        )
    
    async def _analyze_sentence(self, sentence_text: str, sent_idx: int, para_idx: int, 
                               char_start: int, char_end: int, source_info: Dict[str, Any]) -> EnhancedSentence:
        """分析单个句子"""
        
        # 基本分析
        basic_analysis = await self._get_basic_sentence_analysis(sentence_text)
        
        # 提取知识声明
        knowledge_claims = await self._extract_knowledge_claims(sentence_text, sent_idx, para_idx, source_info)
        
        # 命名实体识别
        named_entities = await self._extract_named_entities(sentence_text)
        
        return EnhancedSentence(
            sentence_text=sentence_text,
            sentence_index=sent_idx,
            paragraph_index=para_idx,
            char_start=char_start,
            char_end=char_end,
            word_count=len(sentence_text.split()),
            importance_score=basic_analysis['importance_score'],
            informativeness=basic_analysis['informativeness'],
            novelty_score=basic_analysis['novelty_score'],
            knowledge_claims=knowledge_claims,
            named_entities=named_entities
        )
    
    async def _extract_knowledge_claims(self, sentence_text: str, sent_idx: int, 
                                       para_idx: int, source_info: Dict[str, Any]) -> List[KnowledgeClaim]:
        """从句子中提取知识声明"""
        
        # 构建提示词
        prompt = f"""
        请分析以下句子，提取其中的核心知识声明。每个知识声明应该是一个完整的、可独立理解的认知单元。

        句子: "{sentence_text}"

        请按以下JSON格式返回结果:
        {{
            "claims": [
                {{
                    "claim_text": "核心知识声明（一句话）",
                    "knowledge_type": "fact|opinion|definition|statistic|quote|prediction|research_finding|trend|comparison|explanation",
                    "confidence_score": 0.0-1.0,
                    "confidence_level": "high|medium|low",
                    "quality_score": 0.0-1.0,
                    "topic": "主题",
                    "keywords": ["关键词1", "关键词2"],
                    "entities": ["实体1", "实体2"],
                    "fact_check_status": "verified|unverified|disputed|unknown",
                    "temporal_info": {{"type": "时间类型", "value": "时间值"}},
                    "extraction_method": "ai_analysis"
                }}
            ]
        }}

        注意:
        1. 只提取真正有价值的知识声明，避免提取无意义的内容
        2. 确保每个声明都是原子性的（不可再分）
        3. 准确识别知识类型
        4. 合理评估置信度和质量
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            # 解析JSON响应
            result = json.loads(response.choices[0].message.content)
            claims = []
            
            for claim_data in result.get('claims', []):
                # 创建来源引用
                source_ref = SourceReference(
                    source_id=source_info.get('id', ''),
                    source_url=source_info.get('url', ''),
                    source_title=source_info.get('title', ''),
                    paragraph_index=para_idx,
                    paragraph_text="",  # 需要从上层传入
                    sentence_index=sent_idx,
                    sentence_text=sentence_text,
                    relevance_score=claim_data.get('quality_score', 0.5)
                )
                
                # 创建知识声明
                claim = KnowledgeClaim(
                    claim_text=claim_data['claim_text'],
                    knowledge_type=KnowledgeType(claim_data['knowledge_type']),
                    confidence_score=claim_data['confidence_score'],
                    confidence_level=ConfidenceLevel(claim_data['confidence_level']),
                    quality_score=claim_data['quality_score'],
                    topic=claim_data['topic'],
                    keywords=claim_data.get('keywords', []),
                    entities=claim_data.get('entities', []),
                    source_references=[source_ref],
                    fact_check_status=claim_data.get('fact_check_status'),
                    temporal_info=claim_data.get('temporal_info'),
                    extraction_method=claim_data.get('extraction_method', 'ai_analysis')
                )
                
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            print(f"知识提取失败: {e}")
            return []
    
    async def _get_basic_sentence_analysis(self, sentence_text: str) -> Dict[str, float]:
        """获取句子的基本分析"""
        
        prompt = f"""
        请分析以下句子的特征，返回数值评分:

        句子: "{sentence_text}"

        请按以下JSON格式返回结果:
        {{
            "importance_score": 0.0-1.0,  // 重要性分数
            "informativeness": 0.0-1.0,   // 信息量
            "novelty_score": 0.0-1.0       // 新颖性分数
        }}

        评分标准:
        - importance_score: 句子对理解主题的重要程度
        - informativeness: 句子包含的信息密度
        - novelty_score: 句子内容的新颖性和独特性
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                'importance_score': result.get('importance_score', 0.5),
                'informativeness': result.get('informativeness', 0.5),
                'novelty_score': result.get('novelty_score', 0.5)
            }
            
        except Exception as e:
            print(f"句子分析失败: {e}")
            return {
                'importance_score': 0.5,
                'informativeness': 0.5,
                'novelty_score': 0.5
            }
    
    async def _analyze_paragraph_content(self, paragraph_text: str) -> Dict[str, Any]:
        """分析段落内容"""
        
        prompt = f"""
        请分析以下段落的内容特征:

        段落: "{paragraph_text}"

        请按以下JSON格式返回结果:
        {{
            "main_topic": "主要主题",
            "key_points": ["要点1", "要点2", "要点3"],
            "summary": "段落摘要",
            "coherence_score": 0.0-1.0,     // 连贯性分数
            "relevance_score": 0.0-1.0,     // 相关性分数
            "knowledge_density": 0.0-1.0    // 知识密度
        }}
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"段落分析失败: {e}")
            return {
                'main_topic': '未知主题',
                'key_points': [],
                'summary': paragraph_text[:100] + '...',
                'coherence_score': 0.5,
                'relevance_score': 0.5,
                'knowledge_density': 0.5
            }
    
    async def _extract_named_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取命名实体"""
        
        prompt = f"""
        请从以下文本中提取命名实体:

        文本: "{text}"

        请按以下JSON格式返回结果:
        {{
            "entities": [
                {{
                    "text": "实体文本",
                    "type": "PERSON|ORG|GPE|PRODUCT|EVENT|DATE|MONEY|PERCENT",
                    "start": 开始位置,
                    "end": 结束位置,
                    "confidence": 0.0-1.0
                }}
            ]
        }}
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('entities', [])
            
        except Exception as e:
            print(f"实体提取失败: {e}")
            return []
    
    async def _generate_executive_summary(self, content: str, source_info: Dict[str, Any]) -> str:
        """生成执行摘要"""
        
        prompt = f"""
        请为以下文档生成执行摘要（100-200字）:

        标题: {source_info.get('title', '无标题')}
        内容: {content[:2000]}...

        摘要应包含:
        1. 文档的核心主题
        2. 最重要的3-5个关键点
        3. 主要结论或观点

        请直接返回摘要文本，不需要格式化。
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return f"来自 {source_info.get('title', '未知来源')} 的内容摘要。"
    
    async def _extract_key_insights(self, claims: List[KnowledgeClaim]) -> List[str]:
        """从知识声明中提取关键洞察"""
        
        if not claims:
            return []
        
        # 按质量和置信度排序
        sorted_claims = sorted(claims, 
                             key=lambda x: (x.quality_score * x.confidence_score), 
                             reverse=True)
        
        # 取前5个最重要的声明作为关键洞察
        insights = []
        for claim in sorted_claims[:5]:
            insights.append(claim.claim_text)
        
        return insights
    
    async def _assess_document_quality(self, content: str, claims: List[KnowledgeClaim]) -> Dict[str, float]:
        """评估文档质量"""
        
        # 基于内容长度、知识声明数量等因素评估质量
        content_length = len(content)
        claims_count = len(claims)
        high_quality_claims = len([c for c in claims if c.quality_score > 0.7])
        
        # 简单的质量评估算法
        overall_quality = min(1.0, (content_length / 1000) * 0.3 + 
                             (claims_count / 10) * 0.4 + 
                             (high_quality_claims / max(1, claims_count)) * 0.3)
        
        credibility_score = min(1.0, (high_quality_claims / max(1, claims_count)) * 0.7 + 
                               (1 if content_length > 500 else 0.5) * 0.3)
        
        return {
            'overall_quality': overall_quality,
            'credibility_score': credibility_score
        }
    
    async def _extract_document_level_claims(self, content: str, source_info: Dict[str, Any]) -> List[KnowledgeClaim]:
        """提取文档级别的知识声明"""
        
        prompt = f"""
        请从以下完整文档中提取3-5个最重要的文档级别知识声明:

        标题: {source_info.get('title', '无标题')}
        内容: {content[:3000]}...

        请提取代表整个文档核心观点的知识声明，按以下JSON格式返回:
        {{
            "claims": [
                {{
                    "claim_text": "文档级别知识声明",
                    "knowledge_type": "fact|opinion|definition|statistic|quote|prediction|research_finding|trend|comparison|explanation",
                    "confidence_score": 0.0-1.0,
                    "confidence_level": "high|medium|low",
                    "quality_score": 0.0-1.0,
                    "topic": "主题",
                    "keywords": ["关键词"],
                    "entities": ["实体"]
                }}
            ]
        }}
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            claims = []
            
            for claim_data in result.get('claims', []):
                source_ref = SourceReference(
                    source_id=source_info.get('id', ''),
                    source_url=source_info.get('url', ''),
                    source_title=source_info.get('title', ''),
                    paragraph_index=-1,  # 文档级别
                    paragraph_text="",
                    sentence_index=-1,   # 文档级别
                    sentence_text="",
                    relevance_score=claim_data.get('quality_score', 0.5)
                )
                
                claim = KnowledgeClaim(
                    claim_text=claim_data['claim_text'],
                    knowledge_type=KnowledgeType(claim_data['knowledge_type']),
                    confidence_score=claim_data['confidence_score'],
                    confidence_level=ConfidenceLevel(claim_data['confidence_level']),
                    quality_score=claim_data['quality_score'],
                    topic=claim_data['topic'],
                    keywords=claim_data.get('keywords', []),
                    entities=claim_data.get('entities', []),
                    source_references=[source_ref],
                    extraction_method='document_level_analysis'
                )
                
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            print(f"文档级别知识提取失败: {e}")
            return []
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]


class SentenceSplitter:
    """句子分割器"""
    
    def __init__(self):
        # 中文句子结束标点
        self.chinese_endings = r'[。！？；]'
        # 英文句子结束标点
        self.english_endings = r'[.!?;]'
        # 组合模式
        self.sentence_pattern = rf'({self.chinese_endings}|{self.english_endings})\s*'
    
    def split(self, text: str) -> List[str]:
        """分割句子"""
        # 使用正则表达式分割
        sentences = re.split(self.sentence_pattern, text)
        
        # 重新组合句子（保留标点）
        result = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
                if sentence.strip():
                    result.append(sentence.strip())
        
        # 处理最后一个可能没有标点的句子
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1].strip())
        
        return result