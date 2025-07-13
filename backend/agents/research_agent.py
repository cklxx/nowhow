"""
Research Agent implementation using LangGraph ReactAgent.
This agent is responsible for researching and gathering additional information
about topics found in crawled content.
"""

from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime

from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain.agents import AgentExecutor

from config import Settings
from core.interfaces import IModelService
from core.exceptions import AppException, ModelServiceError
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent that uses LangGraph ReactAgent to perform in-depth research
    on topics and validate information from crawled content.
    """
    
    def __init__(self, settings: Settings, model_service: IModelService):
        super().__init__("research", settings.agents.research)
        self.model_service = model_service
        self.react_agent = None
        self._tools = []
        self._setup_tools()
        self._setup_react_agent()
    
    def _setup_tools(self):
        """Setup tools for the ReactAgent."""
        self._tools = [
            Tool(
                name="web_search",
                description="Search the web for information about a topic. Input should be a search query string.",
                func=self._web_search_tool
            ),
            Tool(
                name="content_analyzer",
                description="Analyze content for key insights, facts, and relevance. Input should be the content text.",
                func=self._content_analyzer_tool
            ),
            Tool(
                name="fact_checker",
                description="Verify facts and claims in content. Input should be a specific claim or fact to verify.",
                func=self._fact_checker_tool
            ),
            Tool(
                name="topic_expander",
                description="Find related topics and subtopics for a given subject. Input should be the main topic.",
                func=self._topic_expander_tool
            ),
            Tool(
                name="source_validator",
                description="Validate the credibility and authority of information sources. Input should be source URL or description.",
                func=self._source_validator_tool
            )
        ]
    
    def _setup_react_agent(self):
        """Setup the LangGraph ReactAgent."""
        try:
            # Create a mock LLM for ReactAgent
            # In a real implementation, you would use a proper LangChain LLM
            from langchain.llms.base import LLM
            
            class MockLLM(LLM):
                def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
                    # This would use your model service
                    # For now, return a simple response
                    return f"I need to research: {prompt}"
                
                @property
                def _llm_type(self) -> str:
                    return "mock"
                
                def bind_tools(self, tools):
                    """Mock implementation of bind_tools for compatibility."""
                    return self
            
            llm = MockLLM()
            
            # Create ReactAgent
            self.react_agent = create_react_agent(
                llm,
                self._tools
            )
            
        except Exception as e:
            logger.error(f"Failed to setup ReactAgent: {e}")
            self.react_agent = None
    
    async def _web_search_tool(self, query: str) -> str:
        """Tool for web search functionality."""
        try:
            # In a real implementation, this would use a web search API
            # For now, simulate search results
            logger.info(f"Performing web search for: {query}")
            
            # Simulate web search with AI model
            search_prompt = f"""
            Simulate a web search for the query: "{query}"
            
            Provide relevant information that would typically be found in search results.
            Focus on AI, technology, and scientific information.
            Include potential sources and key facts.
            
            Format the response as if it were search results.
            """
            
            result = await self.model_service.generate_text(
                search_prompt,
                max_tokens=500,
                temperature=0.7
            )
            
            return f"Web search results for '{query}':\n{result}"
            
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return f"Error performing web search: {str(e)}"
    
    async def _content_analyzer_tool(self, content: str) -> str:
        """Tool for analyzing content."""
        try:
            logger.info("Analyzing content for insights")
            
            analysis_prompt = f"""
            Analyze the following content and provide:
            1. Key insights and main points
            2. Important facts and claims
            3. Relevance to AI/technology topics
            4. Potential areas for further research
            5. Quality and credibility assessment
            
            Content to analyze:
            {content[:2000]}...
            
            Provide a structured analysis.
            """
            
            result = await self.model_service.analyze_content(
                content,
                analysis_type="detailed"
            )
            
            return f"Content analysis results:\n{result}"
            
        except Exception as e:
            logger.error(f"Content analyzer tool error: {e}")
            return f"Error analyzing content: {str(e)}"
    
    async def _fact_checker_tool(self, claim: str) -> str:
        """Tool for fact checking."""
        try:
            logger.info(f"Fact checking claim: {claim}")
            
            fact_check_prompt = f"""
            Fact-check the following claim:
            "{claim}"
            
            Provide:
            1. Verification status (True/False/Partially True/Unclear)
            2. Supporting evidence or contradicting information
            3. Confidence level (High/Medium/Low)
            4. Additional context if needed
            5. Recommended sources for verification
            
            Focus on accuracy and reliability.
            """
            
            result = await self.model_service.generate_text(
                fact_check_prompt,
                max_tokens=400,
                temperature=0.3
            )
            
            return f"Fact check results for '{claim}':\n{result}"
            
        except Exception as e:
            logger.error(f"Fact checker tool error: {e}")
            return f"Error fact checking: {str(e)}"
    
    async def _topic_expander_tool(self, topic: str) -> str:
        """Tool for expanding topics."""
        try:
            logger.info(f"Expanding topic: {topic}")
            
            expansion_prompt = f"""
            For the topic "{topic}", provide:
            1. Related subtopics and areas of interest
            2. Current trends and developments
            3. Key researchers and organizations in this field
            4. Recent breakthroughs or important papers
            5. Potential future directions
            
            Focus on actionable research directions and specific areas to explore.
            """
            
            result = await self.model_service.generate_text(
                expansion_prompt,
                max_tokens=600,
                temperature=0.6
            )
            
            return f"Topic expansion for '{topic}':\n{result}"
            
        except Exception as e:
            logger.error(f"Topic expander tool error: {e}")
            return f"Error expanding topic: {str(e)}"
    
    async def _source_validator_tool(self, source: str) -> str:
        """Tool for validating sources."""
        try:
            logger.info(f"Validating source: {source}")
            
            validation_prompt = f"""
            Evaluate the credibility and authority of this source:
            "{source}"
            
            Assess:
            1. Source authority and reputation
            2. Potential bias or conflicts of interest
            3. Accuracy track record
            4. Peer review status (for academic sources)
            5. Overall credibility score (1-10)
            
            Provide reasoning for the assessment.
            """
            
            result = await self.model_service.generate_text(
                validation_prompt,
                max_tokens=300,
                temperature=0.4
            )
            
            return f"Source validation for '{source}':\n{result}"
            
        except Exception as e:
            logger.error(f"Source validator tool error: {e}")
            return f"Error validating source: {str(e)}"
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research on the provided content."""
        try:
            logger.info("Starting research agent execution")
            
            # Extract research topics from state
            research_topics = state.get("research_topics", [])
            content_to_verify = state.get("content_for_verification", [])
            
            if not research_topics and not content_to_verify:
                logger.warning("No research topics or content provided")
                return {
                    **state,
                    "research_results": [],
                    "fact_check_results": [],
                    "research_status": "no_content",
                    "research_timestamp": datetime.now().isoformat()
                }
            
            research_results = []
            fact_check_results = []
            
            # Research topics if ReactAgent is available
            if self.react_agent and research_topics:
                for topic in research_topics[:self.config.max_iterations]:
                    try:
                        research_query = f"Research the topic: {topic}. Provide comprehensive information including recent developments, key facts, and related areas."
                        
                        # Use ReactAgent for research
                        result = await self._run_react_agent(research_query)
                        
                        research_results.append({
                            "topic": topic,
                            "research_data": result,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"Error researching topic {topic}: {e}")
                        research_results.append({
                            "topic": topic,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
            
            # Fact check content
            if content_to_verify:
                for content_item in content_to_verify:
                    try:
                        # Extract key claims for fact checking
                        claims = await self._extract_claims(content_item)
                        
                        content_fact_checks = []
                        for claim in claims[:3]:  # Limit to 3 claims per content item
                            fact_check = await self._fact_checker_tool(claim)
                            content_fact_checks.append({
                                "claim": claim,
                                "verification": fact_check
                            })
                        
                        fact_check_results.append({
                            "content_id": content_item.get("id", "unknown"),
                            "fact_checks": content_fact_checks,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"Error fact checking content: {e}")
                        fact_check_results.append({
                            "content_id": content_item.get("id", "unknown"),
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
            
            return {
                **state,
                "research_results": research_results,
                "fact_check_results": fact_check_results,
                "research_status": "completed",
                "research_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Research agent execution failed: {e}")
            raise ModelServiceError(f"Research agent failed: {str(e)}")
    
    async def _run_react_agent(self, query: str) -> str:
        """Run the ReactAgent with a query."""
        if not self.react_agent:
            # Fallback to direct model service if ReactAgent not available
            return await self.model_service.generate_text(
                f"Research query: {query}",
                max_tokens=800,
                temperature=0.7
            )
        
        try:
            # Run ReactAgent
            messages = [HumanMessage(content=query)]
            result = await self.react_agent.ainvoke({"messages": messages})
            
            # Extract the final response
            if isinstance(result, dict) and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
            
            return str(result)
            
        except Exception as e:
            logger.error(f"ReactAgent execution error: {e}")
            # Fallback to model service
            return await self.model_service.generate_text(
                f"Research query: {query}",
                max_tokens=800,
                temperature=0.7
            )
    
    async def _extract_claims(self, content_item: Dict[str, Any]) -> List[str]:
        """Extract key claims from content for fact checking."""
        content_text = content_item.get("content", "")
        if not content_text:
            return []
        
        extraction_prompt = f"""
        Extract 3-5 key factual claims from the following content that can be fact-checked:
        
        {content_text[:1500]}
        
        Return only the claims, one per line, focusing on specific facts, statistics, or assertions.
        """
        
        try:
            result = await self.model_service.generate_text(
                extraction_prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse claims from result
            claims = [claim.strip() for claim in result.split('\n') if claim.strip()]
            return claims[:5]  # Limit to 5 claims
            
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return []