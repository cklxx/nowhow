from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from .base_agent import BaseAgent, AgentState
from utils.file_storage import FileStorage
from services.unified_storage_service import UnifiedStorageService

class GeneratedArticle(BaseModel):
    """Generated article structure"""
    title: str
    content: str
    summary: str
    word_count: int
    sources: List[str]
    tags: List[str]
    category: str
    url: Optional[str] = None

class WriterAgent(BaseAgent):
    """Agent responsible for generating articles from processed content"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("WriterAgent")
        print(f"✍️ WriterAgent initializing with API key: {'***' + api_key[-4:] if api_key else 'None'}")
        if not api_key:
            raise ValueError("API key is required for WriterAgent")
        
        # Use both old and new storage for backward compatibility
        self.file_storage = FileStorage()
        self.unified_storage = UnifiedStorageService()
        
        self.llm = ChatOpenAI(
            model="ep-20250617155129-hfzl9",
            api_key=api_key,
            temperature=0.7,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            timeout=600,
            max_retries=2,
            request_timeout=600,
            max_tokens=12288  # Limit output tokens for faster response
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """Generate articles from processed content"""
        try:
            state.current_step = "generating_articles"
            
            processed_content = state.data.get("processed_content", [])
            
            if not processed_content:
                state.error = "No processed content available for article generation"
                return state
            
            # Group content by category for themed articles
            categorized_content = self._categorize_content(processed_content)
            
            generated_articles = []
            
            # Generate articles concurrently for different categories
            print(f"📝 Generating articles for {len(categorized_content)} categories concurrently...")
            
            import asyncio
            
            async def generate_category_article(category, items):
                if len(items) >= 1:
                    print(f"📝 Attempting to generate article for category '{category}' with {len(items)} items")
                    article = await self._generate_article(category, items)
                    if article:
                        print(f"✅ Successfully added article for category '{category}'")
                        return article
                    else:
                        print(f"❌ Failed to generate article for category '{category}'")
                        return None
                return None
            
            # Run article generation concurrently
            tasks = [generate_category_article(cat, items) for cat, items in categorized_content.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful articles
            for result in results:
                if isinstance(result, GeneratedArticle):
                    generated_articles.append(result)
                elif isinstance(result, Exception):
                    print(f"⚠️  Article generation failed: {result}")
            
            articles_data = [article.dict() for article in generated_articles]
            state.data["generated_articles"] = articles_data
            
            # Save generated articles using unified storage (both old and new)
            workflow_id = state.data.get("workflow_id", "default")
            
            # Save with unified storage (async)
            import asyncio
            try:
                modern_path = await self.unified_storage.save_generated_articles(articles_data, workflow_id)
                state.data["generated_articles_file"] = str(modern_path)
                print(f"📝 Saved articles with unified storage to: {modern_path}")
            except Exception as e:
                print(f"⚠️  Failed to save with unified storage: {e}")
                # Fallback to legacy storage
                saved_path = self.file_storage.save_generated_articles(articles_data, workflow_id)
                state.data["generated_articles_file"] = saved_path
            
            state.messages.append(
                HumanMessage(content=f"Generated {len(generated_articles)} articles from {len(processed_content)} content items")
            )
            
            return state
            
        except Exception as e:
            state.error = f"Writer error: {str(e)}"
            return state
    
    def _categorize_content(self, content: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group content by category"""
        categories = {}
        
        for item in content:
            category = item.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        return categories
    
    async def _generate_article(self, category: str, content_items: List[Dict[str, Any]]) -> Optional[GeneratedArticle]:
        """Generate article from content items in the same category"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"📝 Generating article for category '{category}' (attempt {retry_count + 1}/{max_retries})")
                
                # Prepare content summary for article generation
                content_summaries = []
                all_sources = []
                all_tags = set()
                
                for item in content_items:
                    content_summaries.append({
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "key_points": item.get("key_points", []),
                        "source": item.get("source_url", "")
                    })
                    all_sources.append(item.get("source_url", ""))
                    all_tags.update(item.get("tags", []))
                
                # Create article generation prompt (simplified for ARK API)
                system_prompt = f"""Write a brief {category} article about AI. Be concise and informative. Target: 300-500 words."""
                
                content_text = "\n\n".join([
                    f"Source: {item['title']}\nSummary: {item['summary']}\nKey Points: {', '.join(item['key_points'])}"
                    for item in content_summaries
                ])
                
                user_prompt = f"""Topic: {category} in AI\nContent: {content_text[:800]}\nWrite a brief article."""
                
                # Use simplified approach for better compatibility with ARK API
                import asyncio
                simple_prompt = f"Write a 200-word {category} article about {content_summaries[0]['title']}"
                response = await asyncio.wait_for(
                    self.llm.ainvoke([HumanMessage(content=simple_prompt)]), 
                    timeout=120.0  # Use longer timeout since user increased to 600s
                )
                article_content = response.content
                
                # Generate article title with retry
                title = await self._generate_title_with_retry(category, content_summaries)
                
                # Generate summary with retry
                summary = await self._generate_summary_with_retry(article_content)
                
                print(f"✅ Successfully generated article for category '{category}'")
                
                # Set primary URL from first available source
                primary_url = all_sources[0] if all_sources else None
                
                return GeneratedArticle(
                    title=title,
                    content=article_content,
                    summary=summary,
                    word_count=len(article_content.split()),
                    sources=list(set(all_sources)),
                    tags=list(all_tags),
                    category=category,
                    url=primary_url
                )
                
            except asyncio.TimeoutError:
                retry_count += 1
                print(f"⏰ Timeout generating article for category {category} (attempt {retry_count})")
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Wait before retry
                continue
                
            except Exception as e:
                retry_count += 1
                print(f"❌ Error generating article for category {category} (attempt {retry_count}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Wait before retry
                continue
        
        print(f"❌ Failed to generate article for category {category} after {max_retries} attempts")
        return None
    
    async def _generate_title(self, category: str, content_items: List[Dict[str, Any]]) -> str:
        """Generate engaging title for the article"""
        try:
            titles = [item.get("title", "") for item in content_items]
            
            prompt = f"""
Generate an engaging, SEO-friendly title for an AI {category} article based on these source titles:
{', '.join(titles)}

Requirements:
- Catchy and informative
- 10-15 words
- Include relevant keywords
- Professional tone

Return only the title, no quotes or formatting.
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
            
        except Exception:
            return f"Latest Developments in AI {category}"
    
    async def _generate_summary(self, article_content: str) -> str:
        """Generate summary for the article"""
        try:
            prompt = f"""
Write a concise 2-3 sentence summary of this article:

{article_content[:1000]}

Focus on the main insights and value for readers.
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
            
        except Exception:
            return "An overview of recent developments and insights in artificial intelligence."
    
    async def _generate_title_with_retry(self, category: str, content_items: List[Dict[str, Any]]) -> str:
        """Generate engaging title for the article with retry logic"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                titles = [item.get("title", "") for item in content_items]
                
                prompt = f"""Create a title for an AI {category} article about: {', '.join(titles[:2])}. Be brief."""
                
                import asyncio
                response = await asyncio.wait_for(
                    self.llm.ainvoke([HumanMessage(content=prompt)]), 
                    timeout=60.0
                )
                return response.content.strip()
                
            except Exception as e:
                print(f"❌ Error generating title (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return f"Latest Developments in AI {category}"
                await asyncio.sleep(1)
        
        return f"Latest Developments in AI {category}"
    
    async def _generate_summary_with_retry(self, article_content: str) -> str:
        """Generate summary for the article with retry logic"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                prompt = f"""Summarize in 2 sentences: {article_content[:500]}"""
                
                import asyncio
                response = await asyncio.wait_for(
                    self.llm.ainvoke([HumanMessage(content=prompt)]), 
                    timeout=60.0
                )
                return response.content.strip()
                
            except Exception as e:
                print(f"❌ Error generating summary (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return "An overview of recent developments and insights in artificial intelligence."
                await asyncio.sleep(1)
        
        return "An overview of recent developments and insights in artificial intelligence."