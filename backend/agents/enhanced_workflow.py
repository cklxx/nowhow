"""
Enhanced AI content workflow using fixed crawler agent with premium sources.
"""

import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .base_agent import AgentState
from .fixed_crawler_agent import FixedCrawlerAgent
from .processor_agent import ProcessorAgent
from .writer_agent import WriterAgent


class EnhancedAIContentWorkflow:
    """Enhanced LangGraph workflow with reliable crawling and premium sources"""
    
    def __init__(self, openai_api_key: str = None):
        self.crawler = FixedCrawlerAgent()  # Use the fixed crawler
        self.processor = ProcessorAgent(api_key=openai_api_key)
        self.writer = WriterAgent(api_key=openai_api_key)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the enhanced LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("premium_crawler", self._premium_crawler_node)
        workflow.add_node("content_processor", self._processor_node)
        workflow.add_node("article_writer", self._writer_node)
        workflow.add_node("quality_validator", self._validator_node)
        
        # Define the workflow flow
        workflow.set_entry_point("premium_crawler")
        workflow.add_edge("premium_crawler", "content_processor")
        workflow.add_edge("content_processor", "article_writer")
        workflow.add_edge("article_writer", "quality_validator")
        workflow.add_edge("quality_validator", END)
        
        return workflow.compile()
    
    async def _premium_crawler_node(self, state: AgentState) -> AgentState:
        """Premium crawler node execution with enhanced error handling"""
        print("🕷️  Starting premium AI source crawling...")
        
        try:
            result = await self.crawler.execute(state)
            
            # Check if crawling was successful
            crawled_content = result.data.get("crawled_content", {})
            total_items = crawled_content.get("stats", {}).get("total_actual", 0)
            
            if total_items > 0:
                print(f"✅ Successfully crawled {total_items} items from premium sources")
            else:
                print("⚠️  No content crawled, but continuing workflow...")
                
            return result
            
        except Exception as e:
            error_msg = f"Premium crawler failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _processor_node(self, state: AgentState) -> AgentState:
        """Content processor node execution"""
        if state.error:
            print("⏭️  Skipping processor due to previous error")
            return state
        
        # Check if we have content to process
        crawled_content = state.data.get("crawled_content", {})
        rss_content = crawled_content.get("rss_content", [])
        web_content = crawled_content.get("web_content", [])
        
        if not rss_content and not web_content:
            error_msg = "No content available for processing"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
        
        print("⚙️  Processing and analyzing content...")
        try:
            return await self.processor.execute(state)
        except Exception as e:
            error_msg = f"Content processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _writer_node(self, state: AgentState) -> AgentState:
        """Article writer node execution"""
        if state.error:
            print("⏭️  Skipping writer due to previous error")
            return state
        
        # Check if we have processed content
        processed_content = state.data.get("processed_content", [])
        
        if not processed_content:
            error_msg = "No processed content available for article generation"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
        
        print("✍️  Generating AI articles...")
        try:
            return await self.writer.execute(state)
        except Exception as e:
            error_msg = f"Article generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _validator_node(self, state: AgentState) -> AgentState:
        """Enhanced quality validator node"""
        if state.error:
            print("⏭️  Skipping validation due to previous error")
            return state
        
        print("✅ Validating generated content quality...")
        
        # Enhanced validation
        generated_articles = state.data.get("generated_articles", [])
        
        if not generated_articles:
            print("⚠️  No articles generated to validate")
            state.data["validated_articles"] = []
            return state
        
        valid_articles = []
        validation_stats = {
            "total_articles": len(generated_articles),
            "valid_articles": 0,
            "rejected_articles": 0,
            "rejection_reasons": []
        }
        
        for article in generated_articles:
            # Enhanced validation criteria
            word_count = article.get("word_count", 0)
            title = article.get("title", "")
            content = article.get("content", "")
            
            is_valid = True
            rejection_reasons = []
            
            # Word count validation
            if word_count < 500:
                is_valid = False
                rejection_reasons.append(f"Word count too low: {word_count}")
            
            # Title validation
            if len(title) < 10:
                is_valid = False
                rejection_reasons.append("Title too short")
            elif len(title) > 200:
                is_valid = False
                rejection_reasons.append("Title too long")
            
            # Content validation
            if len(content) < 200:
                is_valid = False
                rejection_reasons.append("Content too short")
            
            # Check for AI-related keywords
            ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'neural', 'algorithm', 'model']
            if not any(keyword.lower() in content.lower() for keyword in ai_keywords):
                is_valid = False
                rejection_reasons.append("Not AI-related content")
            
            if is_valid:
                # Add quality score
                article["quality_score"] = self._calculate_article_quality(article)
                valid_articles.append(article)
                validation_stats["valid_articles"] += 1
            else:
                validation_stats["rejected_articles"] += 1
                validation_stats["rejection_reasons"].extend(rejection_reasons)
                print(f"  ❌ Rejected article '{title[:50]}...': {', '.join(rejection_reasons)}")
        
        state.data["validated_articles"] = valid_articles
        state.data["validation_stats"] = validation_stats
        
        print(f"✅ Validation complete: {validation_stats['valid_articles']}/{validation_stats['total_articles']} articles passed quality checks")
        
        return state
    
    def _calculate_article_quality(self, article: Dict[str, Any]) -> float:
        """Calculate quality score for an article"""
        score = 0.5  # Base score
        
        # Word count scoring
        word_count = article.get("word_count", 0)
        if word_count >= 800:
            score += 0.2
        elif word_count >= 600:
            score += 0.1
        
        # Title quality
        title = article.get("title", "")
        if 50 <= len(title) <= 100:
            score += 0.1
        
        # Content structure
        content = article.get("content", "")
        if content.count('\n\n') >= 3:  # Multiple paragraphs
            score += 0.1
        
        # Source quality
        if article.get("sources_count", 0) >= 3:
            score += 0.1
        
        return min(1.0, score)
    
    async def run(self, initial_state: AgentState = None) -> Dict[str, Any]:
        """Run the enhanced workflow with comprehensive error handling"""
        if initial_state is None:
            initial_state = AgentState()
        
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        initial_state.data["workflow_id"] = workflow_id
        
        print(f"🚀 Starting Enhanced AI Content Generation Workflow (ID: {workflow_id})...")
        print("📊 Using premium AI sources and enhanced quality controls")
        print("=" * 70)
        
        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            if result.error:
                print(f"❌ Workflow failed: {result.error}")
                return {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "error": result.error,
                    "progress": result.progress or {},
                    "timestamp": result.data.get("timestamp")
                }
            
            # Extract results
            validated_articles = result.data.get("validated_articles", [])
            crawled_content = result.data.get("crawled_content", {})
            validation_stats = result.data.get("validation_stats", {})
            
            workflow_results = {
                "workflow_id": workflow_id,
                "status": "completed",
                "articles_generated": len(validated_articles),
                "crawl_stats": crawled_content.get("stats", {}),
                "validation_stats": validation_stats,
                "articles": validated_articles,
                "progress": result.progress or {},
                "timestamp": result.data.get("timestamp")
            }
            
            print("=" * 70)
            print(f"🎉 Enhanced workflow completed successfully!")
            print(f"📊 Results Summary:")
            print(f"   • Articles Generated: {len(validated_articles)}")
            print(f"   • Sources Crawled: {crawled_content.get('stats', {}).get('successful_sources', 0)}")
            print(f"   • Content Items: {crawled_content.get('stats', {}).get('total_actual', 0)}")
            print(f"   • Quality Score: {sum(a.get('quality_score', 0) for a in validated_articles) / max(len(validated_articles), 1):.2f}")
            print("=" * 70)
            
            return workflow_results
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": error_msg,
                "progress": {},
                "timestamp": initial_state.data.get("timestamp")
            }