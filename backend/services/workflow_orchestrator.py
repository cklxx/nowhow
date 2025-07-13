"""
Workflow orchestrator implementation using LangGraph.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config import Settings
from core.interfaces import (
    IWorkflowOrchestrator,
    ICrawlerService,
    IContentProcessor,
    IArticleWriter,
    IStorageService,
    ISourceRepository
)
from core.exceptions import WorkflowError
from agents.research_agent import ResearchAgent
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LangGraphOrchestrator(IWorkflowOrchestrator):
    """LangGraph-based workflow orchestrator."""
    
    def __init__(
        self,
        settings: Settings,
        crawler_service: ICrawlerService,
        content_processor: IContentProcessor,
        article_writer: IArticleWriter,
        storage_service: IStorageService,
        source_repository: ISourceRepository,
        research_agent: ResearchAgent
    ):
        self.settings = settings
        self.crawler_service = crawler_service
        self.content_processor = content_processor
        self.article_writer = article_writer
        self.storage_service = storage_service
        self.source_repository = source_repository
        self.research_agent = research_agent
        
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_graph = None
        self._setup_workflow_graph()
    
    def _setup_workflow_graph(self):
        """Setup the LangGraph workflow."""
        try:
            # Define the workflow state
            workflow = StateGraph(dict)
            
            # Add nodes for each step
            workflow.add_node("crawl", self._crawl_step)
            workflow.add_node("process", self._process_step)
            workflow.add_node("research", self._research_step)
            workflow.add_node("write", self._write_step)
            workflow.add_node("save", self._save_step)
            
            # Define the workflow flow
            workflow.set_entry_point("crawl")
            workflow.add_edge("crawl", "process")
            workflow.add_edge("process", "research")
            workflow.add_edge("research", "write")
            workflow.add_edge("write", "save")
            workflow.add_edge("save", END)
            
            # Compile the workflow
            memory = MemorySaver()
            self._workflow_graph = workflow.compile(checkpointer=memory)
            
            logger.info("Workflow graph setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup workflow graph: {e}")
            self._workflow_graph = None
    
    async def run_workflow(self, workflow_config: Dict[str, Any], workflow_id: str = None) -> Dict[str, Any]:
        """Run complete content generation workflow."""
        if workflow_id is None:
            workflow_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting workflow {workflow_id}")
            
            # Initialize or get existing workflow state
            if workflow_id in self._active_workflows:
                initial_state = self._active_workflows[workflow_id]
                initial_state["config"] = workflow_config
                initial_state["status"] = "running"
                initial_state["current_step"] = "initializing"
            else:
                initial_state = {
                    "workflow_id": workflow_id,
                    "config": workflow_config,
                    "timestamp": datetime.now().isoformat(),
                    "status": "running",
                    "current_step": "initializing",
                    "progress": {},
                    "results": {}
                }
                # Store workflow state
                self._active_workflows[workflow_id] = initial_state
            
            if not self._workflow_graph:
                raise WorkflowError("Workflow graph not initialized")
            
            # Run the workflow
            config = {"configurable": {"thread_id": workflow_id}}
            final_state = await self._workflow_graph.ainvoke(initial_state, config)
            
            # Update final state
            final_state["status"] = "completed"
            final_state["completed_at"] = datetime.now().isoformat()
            self._active_workflows[workflow_id] = final_state
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow {workflow_id} failed: {str(e)}"
            logger.error(error_msg)
            
            # Update workflow state with error
            error_state = self._active_workflows.get(workflow_id, {})
            error_state.update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            })
            self._active_workflows[workflow_id] = error_state
            
            raise WorkflowError(error_msg)
    
    async def start_workflow_async(self, workflow_config: Dict[str, Any]) -> str:
        """Start workflow asynchronously and return workflow ID."""
        workflow_id = str(uuid.uuid4())
        
        # Initialize workflow state
        initial_state = {
            "workflow_id": workflow_id,
            "config": workflow_config,
            "timestamp": datetime.now().isoformat(),
            "status": "starting",
            "current_step": "initializing",
            "progress": {},
            "results": {}
        }
        
        self._active_workflows[workflow_id] = initial_state
        
        # Start workflow in background
        asyncio.create_task(self._run_workflow_background(workflow_id, workflow_config))
        
        logger.info(f"Started workflow {workflow_id} in background")
        return workflow_id
    
    async def _run_workflow_background(self, workflow_id: str, workflow_config: Dict[str, Any]):
        """Run workflow in background."""
        try:
            # Update status to running
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["status"] = "running"
                self._active_workflows[workflow_id]["current_step"] = "crawling"
            
            result = await self.run_workflow(workflow_config, workflow_id)
            
            # Update with final result
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id].update(result)
                self._active_workflows[workflow_id]["status"] = "completed"
                
        except Exception as e:
            logger.error(f"Background workflow {workflow_id} failed: {e}")
            # Update status to failed
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["status"] = "failed"
                self._active_workflows[workflow_id]["error"] = str(e)
                self._active_workflows[workflow_id]["failed_at"] = datetime.now().isoformat()
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        return self._active_workflows.get(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow."""
        if workflow_id in self._active_workflows:
            workflow_state = self._active_workflows[workflow_id]
            if workflow_state.get("status") == "running":
                workflow_state["status"] = "cancelled"
                workflow_state["cancelled_at"] = datetime.now().isoformat()
                logger.info(f"Cancelled workflow {workflow_id}")
                return True
        
        return False
    
    async def _crawl_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Crawling step."""
        try:
            logger.info(f"Executing crawl step for workflow {state['workflow_id']}")
            
            # Update progress
            state = self._update_progress(state, "crawling", 10)
            
            # Get sources to crawl
            config = state.get("config", {})
            source_ids = config.get("sources", [])
            categories = config.get("categories", [])
            
            sources = []
            if source_ids:
                for source_id in source_ids:
                    source = await self.source_repository.get_by_id(source_id)
                    if source:
                        sources.append(source)
            elif categories:
                for category in categories:
                    category_sources = await self.source_repository.get_by_category(category)
                    sources.extend(category_sources)
            else:
                # Get all active sources
                sources = await self.source_repository.get_active_sources()
            
            if not sources:
                raise WorkflowError("No sources available for crawling")
            
            # Crawl sources
            async with self.crawler_service:
                crawl_results = await self.crawler_service.crawl_multiple(sources)
            
            # Save crawled content
            await self.storage_service.save_json(
                crawl_results,
                "crawled",
                state["workflow_id"]
            )
            
            state["results"]["crawled_content"] = crawl_results
            state = self._update_progress(state, "crawling completed", 25)
            
            logger.info(f"Crawl step completed for workflow {state['workflow_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Crawl step failed: {e}")
            raise WorkflowError(f"Crawl step failed: {str(e)}")
    
    async def _process_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Content processing step."""
        try:
            logger.info(f"Executing process step for workflow {state['workflow_id']}")
            
            state = self._update_progress(state, "processing", 30)
            
            crawled_content = state["results"].get("crawled_content", [])
            
            # Extract all content items
            all_content = []
            for source_result in crawled_content:
                if source_result.get("status") == "success":
                    content_items = source_result.get("content", [])
                    all_content.extend(content_items)
            
            if not all_content:
                raise WorkflowError("No content available for processing")
            
            # Process content
            processed_content = await self.content_processor.process_batch(all_content)
            
            # Filter by relevance
            agents_config = getattr(self.settings, 'agents', None)
            processor_config = getattr(agents_config, 'processor', None) if agents_config else None
            threshold = getattr(processor_config, 'relevance_threshold', 0.6) if processor_config else 0.6
            filtered_content = await self.content_processor.filter_by_relevance(
                processed_content, threshold
            )
            
            # Save processed content
            await self.storage_service.save_json(
                filtered_content,
                "processed",
                state["workflow_id"]
            )
            
            state["results"]["processed_content"] = filtered_content
            state = self._update_progress(state, "processing completed", 50)
            
            logger.info(f"Process step completed for workflow {state['workflow_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Process step failed: {e}")
            raise WorkflowError(f"Process step failed: {str(e)}")
    
    async def _research_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Research step using ReactAgent."""
        try:
            logger.info(f"Executing research step for workflow {state['workflow_id']}")
            
            state = self._update_progress(state, "researching", 60)
            
            processed_content = state["results"].get("processed_content", [])
            config = state.get("config", {})
            
            # Extract research topics
            research_topics = config.get("research_topics", [])
            if not research_topics:
                # Extract topics from processed content
                research_topics = self._extract_research_topics(processed_content)
            
            # Prepare research state
            research_state = {
                "research_topics": research_topics[:5],  # Limit to 5 topics
                "content_for_verification": processed_content[:10],  # Limit to 10 items
                "workflow_id": state["workflow_id"]
            }
            
            # Execute research agent
            research_results = await self.research_agent.execute(research_state)
            
            state["results"]["research_results"] = research_results
            state = self._update_progress(state, "research completed", 75)
            
            logger.info(f"Research step completed for workflow {state['workflow_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Research step failed: {e}")
            # Continue workflow even if research fails
            state["results"]["research_results"] = {
                "research_results": [],
                "fact_check_results": [],
                "research_status": "failed",
                "error": str(e)
            }
            state = self._update_progress(state, "research failed, continuing", 75)
            return state
    
    async def _write_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Article writing step."""
        try:
            logger.info(f"Executing write step for workflow {state['workflow_id']}")
            
            state = self._update_progress(state, "writing", 80)
            
            processed_content = state["results"].get("processed_content", [])
            research_results = state["results"].get("research_results", {})
            
            if not processed_content:
                raise WorkflowError("No processed content available for writing")
            
            # Group content by category
            content_groups = await self.article_writer.group_content_by_category(processed_content)
            
            # Generate articles for each category
            articles = []
            for category, content_group in content_groups.items():
                if len(content_group) >= 2:  # Only generate articles for categories with enough content
                    try:
                        article = await self.article_writer.generate_article(
                            content_group, category
                        )
                        
                        # Add research insights if available
                        if research_results and research_results.get("research_results"):
                            article["research_insights"] = research_results["research_results"]
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.error(f"Failed to generate article for category {category}: {e}")
            
            if not articles:
                raise WorkflowError("No articles were generated")
            
            state["results"]["articles"] = articles
            state = self._update_progress(state, "writing completed", 90)
            
            logger.info(f"Write step completed for workflow {state['workflow_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Write step failed: {e}")
            raise WorkflowError(f"Write step failed: {str(e)}")
    
    async def _save_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save results step."""
        try:
            logger.info(f"Executing save step for workflow {state['workflow_id']}")
            
            state = self._update_progress(state, "saving", 95)
            
            articles = state["results"].get("articles", [])
            
            # Save articles
            await self.storage_service.save_json(
                {
                    "articles": articles,
                    "metadata": {
                        "workflow_id": state["workflow_id"],
                        "created_at": datetime.now().isoformat(),
                        "total_articles": len(articles),
                        "categories": list(set(article.get("category", "") for article in articles))
                    }
                },
                "articles",
                state["workflow_id"]
            )
            
            state = self._update_progress(state, "completed", 100)
            
            logger.info(f"Save step completed for workflow {state['workflow_id']}")
            return state
            
        except Exception as e:
            logger.error(f"Save step failed: {e}")
            raise WorkflowError(f"Save step failed: {str(e)}")
    
    def _update_progress(self, state: Dict[str, Any], step: str, progress: int) -> Dict[str, Any]:
        """Update workflow progress."""
        state["current_step"] = step
        state["progress"]["overall"] = progress
        state["progress"]["last_update"] = datetime.now().isoformat()
        
        # Update active workflow state
        workflow_id = state.get("workflow_id")
        if workflow_id and workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].update(state)
        
        return state
    
    def _extract_research_topics(self, processed_content: List[Dict[str, Any]]) -> List[str]:
        """Extract research topics from processed content."""
        topics = set()
        
        for content_item in processed_content:
            # Extract from categories
            category = content_item.get("category", "")
            if category:
                topics.add(category)
            
            # Extract from key insights if available
            insights = content_item.get("insights", [])
            if isinstance(insights, list):
                topics.update(insights[:2])  # Add first 2 insights as topics
        
        return list(topics)[:5]  # Return maximum 5 topics