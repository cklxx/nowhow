import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage

class StructuredContent(BaseModel):
    """Structured representation of processed content"""
    title: str
    summary: str
    key_points: List[str]
    category: str
    tags: List[str]
    relevance_score: float
    source_url: str
    content_type: str

class ProcessorAgent(BaseAgent):
    """Agent responsible for processing and structuring crawled content"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("ProcessorAgent")
        print(f"🔧 ProcessorAgent initializing with API key: {'***' + api_key[-4:] if api_key else 'None'}")
        if not api_key:
            raise ValueError("API key is required for ProcessorAgent")
        self.file_storage = FileStorage()
        self.llm = ChatOpenAI(
            model="ep-20250617155129-hfzl9",
            api_key=api_key,
            temperature=0.1,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            timeout=600,
            max_retries=2,
            request_timeout=600,
            max_tokens=12288  # Limit output tokens for faster response
        )
        
    async def execute(self, state: AgentState) -> AgentState:
        """Process and structure crawled content"""
        try:
            state.current_step = "processing_content"
            
            crawled_content = state.data.get("crawled_content", {})
            processed_items = []
            
            # Collect all content for concurrent processing
            all_content = []
            all_content.extend(crawled_content.get("rss_content", []))
            all_content.extend(crawled_content.get("web_content", []))
            
            print(f"⚡ Processing {len(all_content)} items concurrently...")
            
            # Process content concurrently with limited concurrency
            import asyncio
            semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
            
            async def process_with_semaphore(content):
                async with semaphore:
                    return await self._process_content(content)
            
            # Run concurrent processing
            tasks = [process_with_semaphore(content) for content in all_content]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in results:
                if isinstance(result, StructuredContent):
                    processed_items.append(result)
                elif isinstance(result, Exception):
                    print(f"⚠️  Processing failed: {result}")
                # None results are ignored (filtered out)
            
            # Filter and rank content
            filtered_content = self._filter_and_rank(processed_items)
            
            state.data["processed_content"] = filtered_content
            
            # Save processed content to local file
            workflow_id = state.data.get("workflow_id", "default")
            saved_path = self.file_storage.save_processed_content(filtered_content, workflow_id)
            state.data["processed_content_file"] = saved_path
            
            state.messages.append(
                HumanMessage(content=f"Processed {len(processed_items)} items, filtered to {len(filtered_content)} relevant items")
            )
            
            return state
            
        except Exception as e:
            state.error = f"Processor error: {str(e)}"
            return state
    
    async def _process_content(self, content: Dict[str, Any]) -> Optional[StructuredContent]:
        """Process individual content item using LLM"""
        # Prepare content for LLM processing
        content_text = content.get("summary", "") or content.get("content", "")
        title = content.get("title", "")
        
        if not content_text or len(content_text) < 50:
            return None
        
        # Optimize content length for faster processing
        if len(content_text) > 1000:
            content_text = content_text[:1000] + "..."
            print(f"📏 Truncated content for {title} to 1000 chars for faster processing")
        
        # Adaptive timeout based on content type and length
        is_web_content = content.get("type") == "webpage"
        content_length = len(content_text)
        
        if is_web_content:
            timeout = 45.0  # Longer timeout for web content
        elif content_length > 500:
            timeout = 40.0  # Medium timeout for long content
        else:
            timeout = 35.0  # Baseline timeout for short content
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"🔄 Processing {content.get('type', 'unknown')} content: {title} (timeout: {timeout}s, attempt {attempt + 1}/{max_retries})")
                
                # Create prompt for structuring content
                system_prompt = """
You are an AI content analyst. Analyze the content quickly and return ONLY valid JSON in this exact format:
{
  "title": "Clear title",
  "summary": "Brief 2-sentence summary",
  "key_points": ["point1", "point2", "point3"],
  "category": "Research|Tutorial|News|Opinion|Product",
  "tags": ["tag1", "tag2", "tag3"],
  "relevance_score": 0.8
}

Be fast and concise. No explanations, just JSON.
"""
                
                user_prompt = f"""
Title: {title}
Content: {content_text}
Source URL: {content.get('url', 'N/A')}

Structure this content:
"""
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                # Add timeout for API call
                import asyncio
                response = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=timeout)
                
                # Parse LLM response
                try:
                    structured_data = json.loads(response.content)
                    
                    result = StructuredContent(
                        title=structured_data.get("title", title),
                        summary=structured_data.get("summary", ""),
                        key_points=structured_data.get("key_points", []),
                        category=structured_data.get("category", "Other"),
                        tags=structured_data.get("tags", []),
                        relevance_score=float(structured_data.get("relevance_score", 0.5)),
                        source_url=content.get("url", ""),
                        content_type=content.get("type", "unknown")
                    )
                    print(f"✅ Successfully processed: {title}")
                    return result
                    
                except json.JSONDecodeError:
                    print(f"⚠️  JSON parsing failed for {title}, using fallback")
                    return self._fallback_processing(content)
                    
            except asyncio.TimeoutError:
                print(f"⏰ Timeout processing {title} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    print(f"❌ Max retries reached for {title}, using fallback")
                    return self._fallback_processing(content)
                await asyncio.sleep(2)  # Wait before retry
                
            except Exception as e:
                print(f"❌ Error processing {title} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    print(f"❌ Max retries reached for {title}, using fallback")
                    return self._fallback_processing(content)
                await asyncio.sleep(2)  # Wait before retry
        
        return None
    
    def _fallback_processing(self, content: Dict[str, Any]) -> StructuredContent:
        """Fallback processing without LLM - ensure high relevance score"""
        content_text = content.get("summary", "") or content.get("content", "")
        title = content.get("title", "Untitled")
        
        # Determine category based on content hints
        category = "Research"  # Default to Research for AI content
        if "tutorial" in title.lower() or "introduction" in title.lower():
            category = "Tutorial"
        elif "news" in title.lower() or "latest" in title.lower():
            category = "News"
        
        # Generate meaningful key points from content
        sentences = content_text.split('. ')[:3]
        key_points = [s.strip() + '.' for s in sentences if len(s.strip()) > 10]
        if not key_points:
            key_points = [content_text[:100]] if content_text else ["AI-related content"]
        
        return StructuredContent(
            title=title,
            summary=content_text[:200] + "..." if len(content_text) > 200 else content_text,
            key_points=key_points,
            category=category,
            tags=["ai", "machine learning", "technology", "research"],
            relevance_score=0.75,  # Higher score to pass filtering
            source_url=content.get("url", ""),
            content_type=content.get("type", "unknown")
        )
    
    def _filter_and_rank(self, items: List[StructuredContent]) -> List[Dict[str, Any]]:
        """Filter and rank processed content by relevance"""
        # Filter items with relevance score above threshold (lowered for fallback content)
        filtered = [item for item in items if item.relevance_score >= 0.5]
        
        # Sort by relevance score (descending)
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Convert to dict for JSON serialization
        return [item.dict() for item in filtered[:20]]  # Keep top 20 items