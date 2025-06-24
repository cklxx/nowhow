from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from .base_agent import BaseAgent, AgentState

class GeneratedArticle(BaseModel):
    """Generated article structure"""
    title: str
    content: str
    summary: str
    word_count: int
    sources: List[str]
    tags: List[str]
    category: str

class WriterAgent(BaseAgent):
    """Agent responsible for generating articles from processed content"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("WriterAgent")
        self.llm = ChatOpenAI(
            model="gpt-4",
            api_key=api_key,
            temperature=0.7
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
            
            for category, items in categorized_content.items():
                if len(items) >= 2:  # Need at least 2 items to create an article
                    article = await self._generate_article(category, items)
                    if article:
                        generated_articles.append(article)
            
            state.data["generated_articles"] = [article.dict() for article in generated_articles]
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
        try:
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
            
            # Create article generation prompt
            system_prompt = f"""
You are a professional tech writer specializing in AI content. 
Write a comprehensive article about {category} in AI based on the provided content summaries.

Requirements:
- Write in an engaging, informative style
- Include an introduction, main body with sections, and conclusion
- Synthesize information from multiple sources
- Add insights and analysis
- Target length: 800-1200 words
- Use markdown formatting
- Include relevant subheadings
"""
            
            content_text = "\n\n".join([
                f"Source: {item['title']}\nSummary: {item['summary']}\nKey Points: {', '.join(item['key_points'])}"
                for item in content_summaries
            ])
            
            user_prompt = f"""
Category: {category}
Content to synthesize:

{content_text}

Write a comprehensive article that synthesizes this information into a cohesive, insightful piece.
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            article_content = response.content
            
            # Generate article title
            title = await self._generate_title(category, content_summaries)
            
            # Generate summary
            summary = await self._generate_summary(article_content)
            
            return GeneratedArticle(
                title=title,
                content=article_content,
                summary=summary,
                word_count=len(article_content.split()),
                sources=list(set(all_sources)),
                tags=list(all_tags),
                category=category
            )
            
        except Exception as e:
            print(f"Error generating article for category {category}: {e}")
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