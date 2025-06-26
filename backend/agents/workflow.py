import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .base_agent import AgentState
from .crawler_agent import CrawlerAgent
from .processor_agent import ProcessorAgent
from .writer_agent import WriterAgent

class AIContentWorkflow:
    """LangGraph workflow orchestrating the multi-agent content generation pipeline"""
    
    def __init__(self, openai_api_key: str = None):
        self.crawler = CrawlerAgent()
        self.processor = ProcessorAgent(api_key=openai_api_key)
        self.writer = WriterAgent(api_key=openai_api_key)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("crawler", self._crawler_node)
        workflow.add_node("processor", self._processor_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("validator", self._validator_node)
        
        # Define the workflow flow
        workflow.set_entry_point("crawler")
        workflow.add_edge("crawler", "processor")
        workflow.add_edge("processor", "writer")
        workflow.add_edge("writer", "validator")
        workflow.add_edge("validator", END)
        
        return workflow.compile()
    
    async def _crawler_node(self, state: AgentState) -> AgentState:
        """Crawler node execution"""
        print("🕷️  Starting content crawling...")
        return await self.crawler.execute(state)
    
    async def _processor_node(self, state: AgentState) -> AgentState:
        """Processor node execution"""
        if state.error:
            return state
        
        print("⚙️  Processing and structuring content...")
        return await self.processor.execute(state)
    
    async def _writer_node(self, state: AgentState) -> AgentState:
        """Writer node execution"""
        if state.error:
            return state
        
        print("✍️  Generating articles...")
        return await self.writer.execute(state)
    
    async def _validator_node(self, state: AgentState) -> AgentState:
        """Validator node for final checks"""
        if state.error:
            return state
        
        print("✅ Validating generated content...")
        
        # Basic validation
        generated_articles = state.data.get("generated_articles", [])
        
        valid_articles = []
        for article in generated_articles:
            if (article.get("word_count", 0) >= 500 and 
                len(article.get("title", "")) > 10 and
                len(article.get("content", "")) > 100):
                valid_articles.append(article)
        
        state.data["validated_articles"] = valid_articles
        print(f"✅ Validated {len(valid_articles)} high-quality articles")
        
        return state
    
    async def run(self, initial_state: AgentState = None) -> Dict[str, Any]:
        """Run the complete workflow"""
        if initial_state is None:
            initial_state = AgentState()
        
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())[:8]
        initial_state.data["workflow_id"] = workflow_id
        
        print(f"🚀 Starting AI Content Generation Workflow (ID: {workflow_id})...")
        
        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            if result.get("error"):
                print(f"❌ Workflow failed: {result.get('error')}")
                return {"error": result.get("error"), "progress": result.get("progress", {})}
            
            # Extract results
            result_data = result.get("data", {})
            crawled_count = len(result_data.get("crawled_content", {}).get("rss_content", [])) + \
                          len(result_data.get("crawled_content", {}).get("web_content", []))
            
            processed_count = len(result_data.get("processed_content", []))
            articles_count = len(result_data.get("validated_articles", []))
            
            # Extract progress from crawler
            crawler_progress = result_data.get("crawled_content", {}).get("progress", {})
            
            print(f"""
🎉 Workflow completed successfully!
📊 Results:
   - Crawled items: {crawled_count}
   - Processed items: {processed_count}
   - Generated articles: {articles_count}
""")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "crawled_items": crawled_count,
                "processed_items": processed_count,
                "articles_generated": articles_count,
                "articles": result_data.get("validated_articles", []),
                "processed_content": result_data.get("processed_content", []),
                "progress": crawler_progress,
                "file_paths": {
                    "crawled_content": result_data.get("crawled_content_file"),
                    "processed_content": result_data.get("processed_content_file"),
                    "generated_articles": result_data.get("generated_articles_file")
                }
            }
            
        except Exception as e:
            error_msg = f"Workflow execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}

# Convenience function to run the workflow
async def run_content_generation_workflow(openai_api_key: str = None) -> Dict[str, Any]:
    """Run the complete AI content generation workflow"""
    workflow = AIContentWorkflow(openai_api_key=openai_api_key)
    return await workflow.run()