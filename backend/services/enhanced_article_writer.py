"""
增强的文章写作服务 - 支持来源引用和知识声明
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from core.interfaces import IArticleWriter, IModelService
from models.knowledge_models import (
    ArticleWithSources, FormattedCitation, CitationStyle,
    SourceReference, KnowledgeClaim
)
from database.connection import get_database_manager
from database.models import (
    EnhancedArticleModel, KnowledgeClaimModel, SourceReferenceModel
)

class EnhancedArticleWriter(IArticleWriter):
    """增强的文章写作器 - 支持来源引用"""
    
    def __init__(self, model_service: IModelService):
        self.model_service = model_service
        self.db_manager = get_database_manager()
        self.citation_counter = 0
    
    async def generate_article(self, processed_content: List[Dict[str, Any]], 
                             config: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成带来源引用的文章"""
        
        if not processed_content:
            return {'error': 'No content provided'}
        
        config = config or {}
        workflow_id = config.get('workflow_id', 'unknown')
        
        # 收集知识声明
        all_claims = await self._collect_knowledge_claims(processed_content)
        
        if not all_claims:
            # 如果没有知识声明，使用传统方法生成文章
            return await self._generate_traditional_article(processed_content, config)
        
        # 基于知识声明生成文章
        article_with_sources = await self._generate_article_with_sources(all_claims, config)
        
        # 保存到数据库
        article_id = await self._save_enhanced_article(article_with_sources, workflow_id)
        
        # 转换为传统格式以保持兼容性
        traditional_format = await self._convert_to_traditional_format(article_with_sources)
        traditional_format['enhanced_article_id'] = article_id
        
        return traditional_format
    
    async def _collect_knowledge_claims(self, processed_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """收集处理后内容中的知识声明"""
        
        session = self.db_manager.get_sync_session()
        try:
            all_claims = []
            
            for content in processed_content:
                # 获取相关的知识声明
                claim_ids = content.get('knowledge_claims_ids', [])
                
                for claim_id in claim_ids:
                    claim_model = session.query(KnowledgeClaimModel).filter(
                        KnowledgeClaimModel.id == claim_id
                    ).first()
                    
                    if claim_model:
                        # 获取来源引用
                        refs = session.query(SourceReferenceModel).filter(
                            SourceReferenceModel.knowledge_claim_id == claim_id
                        ).all()
                        
                        claim_data = {
                            'id': claim_model.id,
                            'claim_text': claim_model.claim_text,
                            'knowledge_type': claim_model.knowledge_type,
                            'confidence_score': claim_model.confidence_score,
                            'quality_score': claim_model.quality_score,
                            'topic': claim_model.topic,
                            'keywords': claim_model.keywords,
                            'entities': claim_model.entities,
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
                            ],
                            'source_content': content  # 关联原始内容
                        }
                        all_claims.append(claim_data)
            
            # 按质量和置信度排序
            all_claims.sort(key=lambda x: (x['quality_score'] * x['confidence_score']), reverse=True)
            
            return all_claims
            
        finally:
            session.close()
    
    async def _generate_article_with_sources(self, claims: List[Dict[str, Any]], 
                                           config: Dict[str, Any]) -> ArticleWithSources:
        """基于知识声明生成带来源的文章"""
        
        # 按主题聚类知识声明
        topic_clusters = self._cluster_claims_by_topic(claims)
        
        # 生成文章结构
        article_structure = await self._plan_article_structure(topic_clusters, config)
        
        # 生成每个部分的内容
        structured_content = []
        source_mapping = {}
        all_citations = []
        self.citation_counter = 0
        
        for section in article_structure['sections']:
            section_content = await self._generate_section_with_citations(
                section, topic_clusters, source_mapping, all_citations
            )
            structured_content.extend(section_content)
        
        # 生成完整文章文本
        full_content = self._assemble_article_content(structured_content)
        
        # 计算统计信息
        unique_sources = len(set(ref['source_url'] for ref in source_mapping.values()))
        citation_count = len(all_citations)
        
        return ArticleWithSources(
            title=article_structure['title'],
            content=full_content,
            summary=article_structure['summary'],
            category=config.get('category', 'AI技术'),
            structured_content=structured_content,
            source_mapping=source_mapping,
            knowledge_claims=[self._convert_claim_to_model(claim) for claim in claims[:20]],  # 限制数量
            citation_count=citation_count,
            unique_sources=unique_sources,
            source_diversity=min(1.0, unique_sources / 10.0),  # 简单的多样性计算
            citation_density=citation_count / max(1, len(full_content.split())),
            generation_model=config.get('model', 'enhanced_writer')
        )
    
    def _cluster_claims_by_topic(self, claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按主题聚类知识声明"""
        
        clusters = {}
        
        for claim in claims:
            topic = claim.get('topic', '未分类')
            
            # 简单的主题规范化
            if any(keyword in topic.lower() for keyword in ['ai', '人工智能', 'artificial intelligence']):
                normalized_topic = 'AI技术'
            elif any(keyword in topic.lower() for keyword in ['machine learning', '机器学习', 'ml']):
                normalized_topic = '机器学习'
            elif any(keyword in topic.lower() for keyword in ['deep learning', '深度学习', 'dl']):
                normalized_topic = '深度学习'
            elif any(keyword in topic.lower() for keyword in ['nlp', '自然语言', 'natural language']):
                normalized_topic = '自然语言处理'
            else:
                normalized_topic = topic
            
            if normalized_topic not in clusters:
                clusters[normalized_topic] = []
            
            clusters[normalized_topic].append(claim)
        
        # 按每个主题的声明质量排序
        for topic in clusters:
            clusters[topic].sort(key=lambda x: x['quality_score'], reverse=True)
        
        return clusters
    
    async def _plan_article_structure(self, topic_clusters: Dict[str, List[Dict[str, Any]]], 
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        """规划文章结构"""
        
        topics = list(topic_clusters.keys())
        total_claims = sum(len(claims) for claims in topic_clusters.values())
        
        planning_prompt = f"""
        请基于以下信息规划一篇AI技术文章的结构:

        主要话题: {', '.join(topics)}
        知识声明总数: {total_claims}
        目标字数: {config.get('target_words', 1000)}

        请按以下JSON格式返回文章结构:
        {{
            "title": "文章标题",
            "summary": "文章摘要（100-150字）",
            "sections": [
                {{
                    "title": "章节标题",
                    "topic": "对应主题",
                    "target_length": "目标字数",
                    "key_points": ["要点1", "要点2"]
                }}
            ]
        }}

        要求:
        1. 标题要吸引人且准确反映内容
        2. 摘要要概括主要观点
        3. 章节要逻辑清晰，循序渐进
        4. 每个主题都要有对应的章节
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            structure = json.loads(response.choices[0].message.content)
            return structure
            
        except Exception as e:
            print(f"文章结构规划失败: {e}")
            # 返回默认结构
            return {
                "title": "AI技术最新发展综述",
                "summary": "本文综述了人工智能领域的最新技术发展，涵盖多个重要方向的突破性进展。",
                "sections": [
                    {"title": f"{topic}发展现状", "topic": topic, "target_length": "200", "key_points": []}
                    for topic in topics
                ]
            }
    
    async def _generate_section_with_citations(self, section: Dict[str, Any], 
                                             topic_clusters: Dict[str, List[Dict[str, Any]]],
                                             source_mapping: Dict[str, Any],
                                             all_citations: List[str]) -> List[Dict[str, Any]]:
        """生成带引用的章节内容"""
        
        topic = section['topic']
        relevant_claims = topic_clusters.get(topic, [])[:5]  # 限制每节最多5个声明
        
        if not relevant_claims:
            return []
        
        # 准备声明文本
        claims_text = "\n".join([
            f"- {claim['claim_text']} (置信度: {claim['confidence_score']:.2f})"
            for claim in relevant_claims
        ])
        
        content_prompt = f"""
        请为文章章节"{section['title']}"撰写内容，要求整合以下知识声明：

        知识声明:
        {claims_text}

        要求:
        1. 内容要连贯流畅，不要简单罗列
        2. 每个重要观点后面用[引用X]标记需要引用的位置
        3. 字数控制在{section.get('target_length', 200)}字左右
        4. 使用专业但易懂的语言
        5. 确保逻辑清晰，结构完整

        请返回JSON格式:
        {{
            "content": "章节内容，在需要引用的地方标记[引用X]",
            "citations_needed": ["对应的知识声明索引"]
        }}
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": content_prompt}],
                temperature=0.2,
                max_tokens=600
            )
            
            result = json.loads(response.choices[0].message.content)
            content = result['content']
            
            # 处理引用标记，替换为实际的引用
            processed_content = self._process_citations_in_content(
                content, relevant_claims, source_mapping, all_citations
            )
            
            return [{
                'type': 'section',
                'title': section['title'],
                'content': processed_content,
                'topic': topic
            }]
            
        except Exception as e:
            print(f"章节生成失败: {e}")
            return [{
                'type': 'section',
                'title': section['title'],
                'content': f"关于{topic}的内容正在整理中...",
                'topic': topic
            }]
    
    def _process_citations_in_content(self, content: str, claims: List[Dict[str, Any]],
                                    source_mapping: Dict[str, Any], all_citations: List[str]) -> str:
        """处理内容中的引用标记"""
        
        # 查找所有引用标记 [引用X]
        citation_pattern = r'\[引用(\d+)\]'
        matches = re.findall(citation_pattern, content)
        
        for match in matches:
            claim_index = int(match) - 1  # 转换为0基索引
            
            if 0 <= claim_index < len(claims):
                claim = claims[claim_index]
                
                # 生成引用ID
                self.citation_counter += 1
                citation_id = f"ref_{self.citation_counter}"
                
                # 添加到引用列表
                all_citations.append(citation_id)
                
                # 选择最佳来源引用
                best_ref = self._select_best_source_reference(claim['source_references'])
                
                if best_ref:
                    # 添加到来源映射
                    source_mapping[citation_id] = {
                        'source_url': best_ref['source_url'],
                        'source_title': best_ref['source_title'],
                        'sentence_text': best_ref['sentence_text'],
                        'paragraph_index': best_ref['paragraph_index'],
                        'sentence_index': best_ref['sentence_index'],
                        'relevance_score': best_ref['relevance_score']
                    }
                    
                    # 替换引用标记
                    content = content.replace(f'[引用{match}]', f'[{self.citation_counter}]')
        
        return content
    
    def _select_best_source_reference(self, references: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """选择最佳的来源引用"""
        
        if not references:
            return None
        
        # 按相关性分数排序，选择最佳引用
        sorted_refs = sorted(references, key=lambda x: x.get('relevance_score', 0), reverse=True)
        return sorted_refs[0]
    
    def _assemble_article_content(self, structured_content: List[Dict[str, Any]]) -> str:
        """组装完整的文章内容"""
        
        content_parts = []
        
        for item in structured_content:
            if item['type'] == 'section':
                content_parts.append(f"## {item['title']}\n\n{item['content']}\n")
        
        return '\n'.join(content_parts)
    
    def _convert_claim_to_model(self, claim_data: Dict[str, Any]) -> KnowledgeClaim:
        """转换声明数据为模型对象"""
        
        from models.knowledge_models import KnowledgeType, ConfidenceLevel
        
        # 创建来源引用
        source_refs = []
        for ref_data in claim_data.get('source_references', []):
            source_ref = SourceReference(
                source_id=claim_data.get('source_content', {}).get('source_id', ''),
                source_url=ref_data['source_url'],
                source_title=ref_data['source_title'],
                paragraph_index=ref_data['paragraph_index'],
                paragraph_text="",
                sentence_index=ref_data['sentence_index'],
                sentence_text=ref_data['sentence_text'],
                relevance_score=ref_data['relevance_score']
            )
            source_refs.append(source_ref)
        
        return KnowledgeClaim(
            claim_text=claim_data['claim_text'],
            knowledge_type=KnowledgeType(claim_data['knowledge_type']),
            confidence_score=claim_data['confidence_score'],
            confidence_level=ConfidenceLevel('high' if claim_data['confidence_score'] > 0.8 else 
                                           'medium' if claim_data['confidence_score'] > 0.5 else 'low'),
            quality_score=claim_data['quality_score'],
            topic=claim_data['topic'],
            keywords=claim_data.get('keywords', []),
            entities=claim_data.get('entities', []),
            source_references=source_refs
        )
    
    async def _save_enhanced_article(self, article: ArticleWithSources, workflow_id: str) -> str:
        """保存增强文章到数据库"""
        
        session = self.db_manager.get_sync_session()
        try:
            article_model = EnhancedArticleModel(
                workflow_id=workflow_id,
                title=article.title,
                content=article.content,
                summary=article.summary,
                category=article.category,
                tags=article.tags if hasattr(article, 'tags') else [],
                structured_content=article.structured_content,
                source_mapping=article.source_mapping,
                citation_count=article.citation_count,
                unique_sources=article.unique_sources,
                source_diversity=article.source_diversity,
                citation_density=article.citation_density,
                word_count=len(article.content.split()),
                reading_time=max(1, len(article.content.split()) // 200),  # 估算阅读时间
                language="zh",
                generation_model=article.generation_model
            )
            
            session.add(article_model)
            session.commit()
            
            return article_model.id
            
        finally:
            session.close()
    
    async def _convert_to_traditional_format(self, article: ArticleWithSources) -> Dict[str, Any]:
        """转换为传统格式以保持兼容性"""
        
        # 添加引用部分到文章末尾
        content_with_refs = article.content
        
        if article.source_mapping:
            content_with_refs += "\n\n## 参考来源\n\n"
            
            for i, (citation_id, ref) in enumerate(article.source_mapping.items(), 1):
                content_with_refs += f"{i}. {ref['source_title']} - {ref['source_url']}\n"
        
        return {
            'title': article.title,
            'content': content_with_refs,
            'summary': article.summary,
            'category': article.category,
            'word_count': len(article.content.split()),
            'citations': len(article.source_mapping),
            'unique_sources': article.unique_sources,
            'generation_method': 'enhanced_with_sources',
            'quality_indicators': {
                'source_diversity': article.source_diversity,
                'citation_density': article.citation_density,
                'knowledge_claims_count': len(article.knowledge_claims)
            }
        }
    
    async def _generate_traditional_article(self, processed_content: List[Dict[str, Any]], 
                                          config: Dict[str, Any]) -> Dict[str, Any]:
        """生成传统格式文章（兼容性方法）"""
        
        # 提取基本信息
        summaries = [content.get('summary', '') for content in processed_content if content.get('summary')]
        categories = [content.get('category', '') for content in processed_content if content.get('category')]
        
        # 选择主要分类
        main_category = max(set(categories), key=categories.count) if categories else 'AI技术'
        
        # 生成文章
        combined_summary = ' '.join(summaries[:5])  # 限制摘要数量
        
        article_prompt = f"""
        基于以下内容摘要，写一篇关于{main_category}的文章:

        内容摘要:
        {combined_summary}

        要求:
        1. 文章长度800-1200字
        2. 结构清晰，包含引言、主体和结论
        3. 语言专业但易懂
        4. 观点要有逻辑性

        请返回JSON格式:
        {{
            "title": "文章标题",
            "content": "文章正文",
            "summary": "文章摘要"
        }}
        """

        try:
            response = await self.model_service.chat_completion(
                messages=[{"role": "user", "content": article_prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'title': result['title'],
                'content': result['content'],
                'summary': result['summary'],
                'category': main_category,
                'word_count': len(result['content'].split()),
                'generation_method': 'traditional',
                'source_count': len(processed_content)
            }
            
        except Exception as e:
            print(f"传统文章生成失败: {e}")
            return {
                'title': f'{main_category}最新发展',
                'content': '文章内容生成中遇到问题，请稍后重试。',
                'summary': '技术文章摘要',
                'category': main_category,
                'error': str(e)
            }
    
    # 实现接口要求的方法
    async def create_article_from_content(self, content_list: List[str], 
                                        topic: str = None, style: str = "professional") -> Dict[str, Any]:
        """从内容列表创建文章"""
        
        # 转换格式
        processed_content = [{'content': content, 'summary': content[:200]} for content in content_list]
        config = {'category': topic or 'AI技术', 'style': style}
        
        return await self.generate_article(processed_content, config)
    
    async def enhance_article_quality(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """增强文章质量"""
        # 简单实现，返回原文章
        return article
    
    async def generate_article_variations(self, base_article: Dict[str, Any], 
                                        count: int = 3) -> List[Dict[str, Any]]:
        """生成文章变体"""
        # 简单实现，返回原文章的列表
        return [base_article] * count
    
    async def group_content_by_category(self, content_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按类别分组内容"""
        groups = {}
        
        for content in content_list:
            category = content.get('category', 'unknown')
            if category not in groups:
                groups[category] = []
            groups[category].append(content)
        
        return groups