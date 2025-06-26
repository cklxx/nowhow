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
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        
    async def execute(self, state: AgentState) -> AgentState:
        """Process and structure crawled content"""
        try:
            state.current_step = "processing_content"
            
            crawled_content = state.data.get("crawled_content", {})
            processed_items = []
            
            # Process RSS content
            for article in crawled_content.get("rss_content", []):
                structured = await self._process_content(article)
                if structured:
                    processed_items.append(structured)
            
            # Process web content
            for page in crawled_content.get("web_content", []):
                structured = await self._process_content(page)
                if structured:
                    processed_items.append(structured)
            
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
        try:
            # Prepare content for LLM processing
            content_text = content.get("summary", "") or content.get("content", "")
            title = content.get("title", "")
            
            if not content_text or len(content_text) < 50:
                return None
            
            # Create prompt for structuring content
            system_prompt = """
You are an AI content analyst. Structure the given content into the following format:
- Extract a clear title
- Write a concise summary (2-3 sentences)
- Identify 3-5 key points
- Categorize into one of: Research, Product, Tutorial, News, Opinion
- Add relevant tags
- Score relevance to AI field (0.0-1.0)

Return JSON format only.
"""
            
            user_prompt = f"""
Title: {title}
Content: {content_text[:1500]}
Source URL: {content.get('url', 'N/A')}

Structure this content:
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse LLM response
            try:
                structured_data = json.loads(response.content)
                
                return StructuredContent(
                    title=structured_data.get("title", title),
                    summary=structured_data.get("summary", ""),
                    key_points=structured_data.get("key_points", []),
                    category=structured_data.get("category", "Other"),
                    tags=structured_data.get("tags", []),
                    relevance_score=float(structured_data.get("relevance_score", 0.5)),
                    source_url=content.get("url", ""),
                    content_type=content.get("type", "unknown")
                )
                
            except json.JSONDecodeError:
                # Fallback processing if JSON parsing fails
                return self._fallback_processing(content)
                
        except Exception as e:
            print(f"Error processing content: {e}")
            return None
    
    def _fallback_processing(self, content: Dict[str, Any]) -> StructuredContent:
        """Fallback processing without LLM"""
        content_text = content.get("summary", "") or content.get("content", "")
        
        return StructuredContent(
            title=content.get("title", "Untitled"),
            summary=content_text[:200] + "..." if len(content_text) > 200 else content_text,
            key_points=[content_text[:100]] if content_text else [],
            category="Other",
            tags=["ai", "technology"],
            relevance_score=0.5,
            source_url=content.get("url", ""),
            content_type=content.get("type", "unknown")
        )
    
    def _filter_and_rank(self, items: List[StructuredContent]) -> List[Dict[str, Any]]:
        """Filter and rank processed content by relevance"""
        # Filter items with relevance score above threshold
        filtered = [item for item in items if item.relevance_score >= 0.6]
        
        # Sort by relevance score (descending)
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Convert to dict for JSON serialization
        return [item.dict() for item in filtered[:20]]  # Keep top 20 items