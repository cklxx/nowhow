"""
Model service implementation for ARK API integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Settings
from core.interfaces import IModelService
from core.exceptions import ModelServiceError

logger = logging.getLogger(__name__)


class ARKModelService(IModelService):
    """ARK API model service implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.get_active_model_config()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using ARK API."""
        try:
            payload = {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens or 2000,
                "temperature": temperature or 0.7,
                **kwargs
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ModelServiceError("Invalid response format from ARK API")
                
        except httpx.HTTPError as e:
            logger.error(f"ARK API HTTP error: {e}")
            raise ModelServiceError(f"ARK API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"ARK API error: {e}")
            raise ModelServiceError(f"Text generation failed: {str(e)}")
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using ARK API."""
        try:
            analysis_prompts = {
                "general": f"""
                Analyze the following content and provide a structured analysis:
                
                Content: {content}
                
                Please provide:
                1. Main topics and themes
                2. Key insights and takeaways
                3. Relevance score (0-1) for AI/technology content
                4. Content quality assessment
                5. Potential categories or tags
                
                Respond in JSON format.
                """,
                "detailed": f"""
                Perform a detailed analysis of the following content:
                
                Content: {content}
                
                Provide:
                1. Comprehensive summary
                2. Technical depth assessment
                3. Factual accuracy indicators
                4. Source credibility factors
                5. Relevance to current AI trends
                6. Potential research directions
                7. Key entities and concepts mentioned
                
                Respond in JSON format.
                """,
                "relevance": f"""
                Assess the relevance of this content to AI and technology:
                
                Content: {content}
                
                Provide:
                1. Relevance score (0-1)
                2. Justification for the score
                3. Key AI/tech topics mentioned
                4. Content category classification
                
                Respond in JSON format.
                """
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
            
            result_text = await self.generate_text(
                prompt,
                max_tokens=1000,
                temperature=0.3,
                **kwargs
            )
            
            # Try to parse as JSON, fallback to structured text
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # If not valid JSON, structure the response
                return {
                    "analysis_type": analysis_type,
                    "raw_analysis": result_text,
                    "structured": self._structure_analysis_text(result_text)
                }
                
        except Exception as e:
            logger.error(f"Content analysis error: {e}")
            raise ModelServiceError(f"Content analysis failed: {str(e)}")
    
    async def score_relevance(
        self,
        content: str,
        criteria: str,
        **kwargs
    ) -> float:
        """Score content relevance using ARK API."""
        try:
            prompt = f"""
            Score the relevance of the following content based on these criteria: {criteria}
            
            Content: {content}
            
            Provide only a numeric score between 0.0 and 1.0, where:
            - 0.0 = Not relevant at all
            - 0.5 = Moderately relevant
            - 1.0 = Highly relevant
            
            Return only the numeric score.
            """
            
            result = await self.generate_text(
                prompt,
                max_tokens=10,
                temperature=0.1,
                **kwargs
            )
            
            # Extract numeric score
            score_text = result.strip()
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            except ValueError:
                # Try to extract number from text
                import re
                numbers = re.findall(r'0?\.\d+|[01]\.?\d*', score_text)
                if numbers:
                    return max(0.0, min(1.0, float(numbers[0])))
                else:
                    logger.warning(f"Could not parse relevance score: {score_text}")
                    return 0.5  # Default to moderate relevance
                    
        except Exception as e:
            logger.error(f"Relevance scoring error: {e}")
            raise ModelServiceError(f"Relevance scoring failed: {str(e)}")
    
    def _structure_analysis_text(self, text: str) -> Dict[str, Any]:
        """Structure analysis text into a dictionary."""
        try:
            # Simple text structuring - look for numbered points, sections, etc.
            lines = text.split('\n')
            structured = {
                "summary": "",
                "key_points": [],
                "categories": [],
                "insights": []
            }
            
            current_section = "summary"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect section headers
                if any(keyword in line.lower() for keyword in ['summary', 'key points', 'insights', 'categories']):
                    if 'summary' in line.lower():
                        current_section = 'summary'
                    elif 'key' in line.lower() or 'points' in line.lower():
                        current_section = 'key_points'
                    elif 'insight' in line.lower():
                        current_section = 'insights'
                    elif 'categor' in line.lower():
                        current_section = 'categories'
                    continue
                
                # Add content to appropriate section
                if current_section == 'summary':
                    structured['summary'] += line + " "
                elif current_section in ['key_points', 'insights', 'categories']:
                    structured[current_section].append(line)
            
            return structured
            
        except Exception as e:
            logger.error(f"Text structuring error: {e}")
            return {"raw_text": text}


class OpenAIModelService(IModelService):
    """OpenAI API model service implementation (for future use)."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.models.openai
        if not self.config:
            raise ModelServiceError("OpenAI configuration not found")
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API."""
        # Placeholder implementation
        raise NotImplementedError("OpenAI integration not yet implemented")
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze content using OpenAI API."""
        # Placeholder implementation
        raise NotImplementedError("OpenAI integration not yet implemented")
    
    async def score_relevance(
        self,
        content: str,
        criteria: str,
        **kwargs
    ) -> float:
        """Score content relevance using OpenAI API."""
        # Placeholder implementation
        raise NotImplementedError("OpenAI integration not yet implemented")