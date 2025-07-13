"""
Article writer service implementation.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from collections import defaultdict

from config import Settings
from core.interfaces import IArticleWriter, IModelService
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class AIArticleWriter(IArticleWriter):
    """AI-powered article writer implementation."""
    
    def __init__(self, settings: Settings, model_service: IModelService):
        self.settings = settings
        self.model_service = model_service
        self.config = settings.agents.writer
    
    async def generate_article(
        self,
        content_group: List[Dict[str, Any]],
        category: str,
        style_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate an article from content group."""
        try:
            if not content_group:
                raise ProcessingError("No content provided for article generation")
            
            logger.info(f"Generating article for category '{category}' with {len(content_group)} content items")
            
            # Prepare content summary
            content_summary = self._prepare_content_summary(content_group)
            
            # Generate article title
            article_title = await self._generate_title(content_summary, category)
            
            # Generate article content
            article_content = await self._generate_content(
                content_summary, article_title, category, style_config
            )
            
            # Generate article summary
            article_summary = await self._generate_summary(article_content)
            
            # Create article structure
            article = {
                "id": f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{category.lower().replace(' ', '_')}",
                "title": article_title,
                "content": article_content,
                "summary": article_summary,
                "category": category,
                "word_count": len(article_content.split()),
                "source_count": len(content_group),
                "sources": [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", "")
                    }
                    for item in content_group
                ],
                "created_at": datetime.now().isoformat(),
                "style": style_config.get("template_style", self.config.template_style) if style_config else self.config.template_style,
                "metadata": {
                    "relevance_scores": [item.get("relevance_score", 0.0) for item in content_group],
                    "avg_relevance": sum(item.get("relevance_score", 0.0) for item in content_group) / len(content_group),
                    "source_categories": list(set(item.get("category", "") for item in content_group)),
                    "key_insights": self._extract_key_insights(content_group)
                }
            }
            
            logger.info(f"Generated article '{article_title}' ({article['word_count']} words)")
            return article
            
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            raise ProcessingError(f"Article generation failed: {str(e)}")
    
    async def group_content_by_category(
        self,
        content_list: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group content by category."""
        try:
            grouped_content = defaultdict(list)
            
            for content_item in content_list:
                category = content_item.get("category", "General")
                grouped_content[category].append(content_item)
            
            # Sort each group by relevance score (highest first)
            for category in grouped_content:
                grouped_content[category].sort(
                    key=lambda x: x.get("relevance_score", 0.0),
                    reverse=True
                )
            
            # Convert to regular dict
            result = dict(grouped_content)
            
            logger.info(f"Grouped {len(content_list)} items into {len(result)} categories")
            for category, items in result.items():
                logger.debug(f"Category '{category}': {len(items)} items")
            
            return result
            
        except Exception as e:
            logger.error(f"Content grouping failed: {e}")
            raise ProcessingError(f"Content grouping failed: {str(e)}")
    
    def _prepare_content_summary(self, content_group: List[Dict[str, Any]]) -> str:
        """Prepare a summary of content for article generation."""
        summaries = []
        
        for i, content_item in enumerate(content_group[:10], 1):  # Limit to 10 items
            title = content_item.get("title", "")
            content_text = content_item.get("content", "")
            insights = content_item.get("insights", [])
            source = content_item.get("source", "")
            
            summary = f"Source {i} ({source}):\n"
            if title:
                summary += f"Title: {title}\n"
            if content_text:
                summary += f"Content: {content_text[:500]}...\n"
            if insights:
                summary += f"Key Insights: {'; '.join(insights[:3])}\n"
            summary += "\n"
            
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    async def _generate_title(self, content_summary: str, category: str) -> str:
        """Generate article title."""
        try:
            prompt = f"""
            Based on the following content about {category}, generate a compelling article title.
            
            Content Summary:
            {content_summary[:1000]}
            
            Requirements:
            - Title should be engaging and informative
            - 50-80 characters long
            - Capture the main theme/development
            - Professional tone
            - Include key terms from the content
            
            Return only the title, nothing else.
            """
            
            title = await self.model_service.generate_text(
                prompt,
                max_tokens=50,
                temperature=0.7
            )
            
            return title.strip().strip('"\'')
            
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return f"Latest Developments in {category}"
    
    async def _generate_content(
        self,
        content_summary: str,
        title: str,
        category: str,
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate article content."""
        try:
            style = style_config.get("template_style", self.config.template_style) if style_config else self.config.template_style
            min_words = style_config.get("min_word_count", self.config.min_word_count) if style_config else self.config.min_word_count
            max_words = style_config.get("max_word_count", self.config.max_word_count) if style_config else self.config.max_word_count
            
            prompt = f"""
            Write a comprehensive article about {category} based on the following content sources.
            
            Article Title: {title}
            
            Source Content:
            {content_summary}
            
            Requirements:
            - Write {min_words}-{max_words} words
            - Use {style} style
            - Include an engaging introduction
            - Organize content into clear sections with headings
            - Synthesize information from multiple sources
            - Include specific details and examples
            - Provide insights and analysis
            - End with a conclusion about future implications
            - Use markdown formatting for headings and structure
            
            Structure:
            ## Introduction
            [Engaging introduction that sets context]
            
            ## Key Developments
            [Main content sections with subheadings]
            
            ## Technical Insights
            [Technical details and analysis]
            
            ## Industry Impact
            [Broader implications and impact]
            
            ## Future Outlook
            [Predictions and future directions]
            
            ## Conclusion
            [Summary and key takeaways]
            
            Write the article now:
            """
            
            content = await self.model_service.generate_text(
                prompt,
                max_tokens=2000,
                temperature=0.6
            )
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return f"# {title}\n\nThis article could not be generated due to a technical error."
    
    async def _generate_summary(self, article_content: str) -> str:
        """Generate article summary."""
        try:
            prompt = f"""
            Create a concise summary (100-150 words) of the following article:
            
            {article_content}
            
            The summary should:
            - Capture the main points
            - Be engaging and informative
            - Stand alone as a complete overview
            - Use clear, professional language
            
            Return only the summary:
            """
            
            summary = await self.model_service.generate_text(
                prompt,
                max_tokens=200,
                temperature=0.4
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary generation failed."
    
    def _extract_key_insights(self, content_group: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from content group."""
        all_insights = []
        
        for content_item in content_group:
            insights = content_item.get("insights", [])
            if isinstance(insights, list):
                all_insights.extend(insights)
        
        # Remove duplicates and limit
        unique_insights = list(dict.fromkeys(all_insights))  # Preserves order
        return unique_insights[:10]  # Limit to 10 insights
    
    async def optimize_article(
        self,
        article: Dict[str, Any],
        optimization_type: str = "readability"
    ) -> Dict[str, Any]:
        """Optimize article for specific criteria."""
        try:
            content = article.get("content", "")
            
            if optimization_type == "readability":
                prompt = f"""
                Improve the readability of this article while maintaining its technical accuracy:
                
                {content}
                
                Make these improvements:
                - Simplify complex sentences
                - Add transitions between sections
                - Improve paragraph structure
                - Ensure consistent tone
                - Maintain all technical details
                
                Return the improved article:
                """
            elif optimization_type == "seo":
                prompt = f"""
                Optimize this article for SEO while maintaining quality:
                
                {content}
                
                Improvements:
                - Add relevant keywords naturally
                - Improve heading structure
                - Add meta-description worthy introduction
                - Ensure good keyword density
                - Maintain readability
                
                Return the optimized article:
                """
            else:
                return article  # No optimization
            
            optimized_content = await self.model_service.generate_text(
                prompt,
                max_tokens=2500,
                temperature=0.3
            )
            
            # Update article
            optimized_article = {
                **article,
                "content": optimized_content.strip(),
                "optimized_for": optimization_type,
                "optimized_at": datetime.now().isoformat()
            }
            
            return optimized_article
            
        except Exception as e:
            logger.error(f"Article optimization failed: {e}")
            return article  # Return original on failure