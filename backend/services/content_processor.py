"""
Content processor service implementation.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from config import Settings
from core.interfaces import IContentProcessor, IModelService
from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class AIContentProcessor(IContentProcessor):
    """AI-powered content processor implementation."""
    
    def __init__(self, settings: Settings, model_service: IModelService):
        self.settings = settings
        self.model_service = model_service
        self.config = getattr(getattr(settings, 'agents', None), 'processor', None) or type('Config', (), {
            'max_content_length': 10000,
            'batch_size': 10
        })()
    
    async def process_content(
        self,
        content: Dict[str, Any],
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a single piece of content."""
        try:
            content_text = content.get("content", "")
            title = content.get("title", "")
            
            if not content_text and not title:
                raise ProcessingError("No content to process")
            
            # Combine title and content for analysis
            max_length = getattr(self.config, 'max_content_length', 10000)
            full_text = f"{title}\n\n{content_text}"[:max_length]
            
            # Analyze content using AI model
            analysis = await self.model_service.analyze_content(
                full_text,
                analysis_type="detailed"
            )
            
            # Score relevance
            relevance_score = await self.model_service.score_relevance(
                full_text,
                "AI, technology, machine learning, artificial intelligence, tech news"
            )
            
            # Extract key insights
            insights = await self._extract_insights(full_text)
            
            # Categorize content
            category = await self._categorize_content(full_text, analysis)
            
            # Create processed content
            processed = {
                **content,  # Preserve original fields
                "processed_at": datetime.now().isoformat(),
                "relevance_score": relevance_score,
                "category": category,
                "insights": insights,
                "analysis": analysis,
                "word_count": len(full_text.split()),
                "processing_status": "success"
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            return {
                **content,
                "processed_at": datetime.now().isoformat(),
                "processing_status": "failed",
                "processing_error": str(e),
                "relevance_score": 0.0
            }
    
    async def process_batch(
        self,
        content_list: List[Dict[str, Any]],
        processing_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple pieces of content."""
        try:
            # Process in batches to avoid overwhelming the API
            batch_size = getattr(self.config, 'batch_size', 10)
            processed_content = []
            
            for i in range(0, len(content_list), batch_size):
                batch = content_list[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [
                    self.process_content(content_item, processing_config)
                    for content_item in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle exceptions
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error for item {i+j}: {result}")
                        # Create error result
                        error_result = {
                            **batch[j],
                            "processed_at": datetime.now().isoformat(),
                            "processing_status": "failed",
                            "processing_error": str(result),
                            "relevance_score": 0.0
                        }
                        processed_content.append(error_result)
                    else:
                        processed_content.append(result)
                
                # Small delay between batches
                if i + batch_size < len(content_list):
                    await asyncio.sleep(0.5)
            
            logger.info(f"Processed {len(processed_content)} content items")
            return processed_content
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise ProcessingError(f"Batch processing failed: {str(e)}")
    
    async def filter_by_relevance(
        self,
        content_list: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Filter content by relevance score."""
        try:
            filtered_content = []
            
            for content_item in content_list:
                relevance_score = content_item.get("relevance_score", 0.0)
                
                if relevance_score >= threshold:
                    filtered_content.append(content_item)
                else:
                    logger.debug(
                        f"Filtered out content '{content_item.get('title', 'Unknown')}' "
                        f"(score: {relevance_score:.2f} < {threshold})"
                    )
            
            logger.info(
                f"Filtered {len(content_list)} items to {len(filtered_content)} "
                f"(threshold: {threshold})"
            )
            
            return filtered_content
            
        except Exception as e:
            logger.error(f"Relevance filtering failed: {e}")
            raise ProcessingError(f"Relevance filtering failed: {str(e)}")
    
    async def _extract_insights(self, content_text: str) -> List[str]:
        """Extract key insights from content."""
        try:
            prompt = f"""
            Extract 3-5 key insights from the following content:
            
            {content_text[:1500]}
            
            Return only the insights as a bullet list, focusing on:
            - Technical innovations
            - Important developments
            - Key findings or results
            - Business implications
            - Future trends
            
            Format as bullet points without numbers.
            """
            
            result = await self.model_service.generate_text(
                prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse insights from result
            insights = []
            for line in result.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    insight = line.lstrip('•-* ').strip()
                    if insight:
                        insights.append(insight)
            
            return insights[:5]  # Limit to 5 insights
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []
    
    async def _categorize_content(
        self,
        content_text: str,
        analysis: Dict[str, Any]
    ) -> str:
        """Categorize content into appropriate category."""
        try:
            # Define available categories
            services_config = getattr(self.settings, 'services', None)
            sources_config = getattr(services_config, 'sources', None) if services_config else None
            categories = getattr(sources_config, 'categories', None) if sources_config else None
            
            if not categories:
                categories = [
                    "AI Research",
                    "Machine Learning", 
                    "Deep Learning",
                    "NLP",
                    "Computer Vision",
                    "Technology News",
                    "General"
                ]
            
            prompt = f"""
            Categorize the following content into one of these categories:
            {', '.join(categories)}
            
            Content: {content_text[:800]}
            
            Return only the category name that best fits the content.
            If none fit well, return "General".
            """
            
            result = await self.model_service.generate_text(
                prompt,
                max_tokens=20,
                temperature=0.1
            )
            
            # Clean and validate category
            category = result.strip().strip('"\'')
            
            # Check if returned category is in our list
            for valid_category in categories:
                if category.lower() == valid_category.lower():
                    return valid_category
            
            # If not found, try partial matching
            for valid_category in categories:
                if category.lower() in valid_category.lower() or valid_category.lower() in category.lower():
                    return valid_category
            
            # Fallback to General
            return "General"
            
        except Exception as e:
            logger.error(f"Categorization failed: {e}")
            return "General"
    
    async def get_content_statistics(
        self,
        content_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get statistics about processed content."""
        try:
            total_content = len(content_list)
            successful_processing = len([
                c for c in content_list 
                if c.get("processing_status") == "success"
            ])
            
            # Category distribution
            categories = {}
            relevance_scores = []
            
            for content_item in content_list:
                category = content_item.get("category", "Unknown")
                categories[category] = categories.get(category, 0) + 1
                
                score = content_item.get("relevance_score", 0.0)
                if isinstance(score, (int, float)):
                    relevance_scores.append(score)
            
            # Calculate relevance statistics
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            high_relevance = len([s for s in relevance_scores if s >= 0.8])
            medium_relevance = len([s for s in relevance_scores if 0.6 <= s < 0.8])
            low_relevance = len([s for s in relevance_scores if s < 0.6])
            
            return {
                "total_content": total_content,
                "successful_processing": successful_processing,
                "processing_success_rate": successful_processing / total_content if total_content > 0 else 0,
                "categories": categories,
                "relevance_stats": {
                    "average_score": round(avg_relevance, 3),
                    "high_relevance": high_relevance,
                    "medium_relevance": medium_relevance,
                    "low_relevance": low_relevance
                }
            }
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {e}")
            return {"error": str(e)}