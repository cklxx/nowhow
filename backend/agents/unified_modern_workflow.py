"""
Unified modern workflow using cutting-edge 2024 tools.
Replaces all legacy crawling components with modern alternatives.
"""

import uuid
import os
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from .base_agent import AgentState
from .modern_crawler_agent import ModernCrawlerAgent
from .processor_agent import ProcessorAgent
from .writer_agent import WriterAgent


class UnifiedModernWorkflow:
    """
    Unified modern AI content workflow using 2024's best tools.
    
    Architecture:
    - ModernCrawlerAgent: Firecrawl + Crawl4AI + Playwright + fallbacks
    - ProcessorAgent: Enhanced content processing
    - WriterAgent: AI-powered article generation
    - QualityValidator: Advanced quality control
    """
    
    def __init__(self, openai_api_key: str = None, firecrawl_api_key: str = None):
        # Initialize with modern tools
        self.crawler = ModernCrawlerAgent(firecrawl_api_key=firecrawl_api_key)
        self.processor = ProcessorAgent(api_key=openai_api_key)
        self.writer = WriterAgent(api_key=openai_api_key)
        
        # Store keys for reporting
        self.openai_api_key = openai_api_key
        self.firecrawl_api_key = firecrawl_api_key
        
        self.workflow = self._build_modern_workflow()
    
    def _build_modern_workflow(self) -> StateGraph:
        """Build the modern LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent with modern naming
        workflow.add_node("modern_crawler", self._modern_crawler_node)
        workflow.add_node("ai_processor", self._ai_processor_node)
        workflow.add_node("ai_writer", self._ai_writer_node)
        workflow.add_node("quality_validator", self._quality_validator_node)
        
        # Define the enhanced workflow flow
        workflow.set_entry_point("modern_crawler")
        workflow.add_edge("modern_crawler", "ai_processor")
        workflow.add_edge("ai_processor", "ai_writer")
        workflow.add_edge("ai_writer", "quality_validator")
        workflow.add_edge("quality_validator", END)
        
        return workflow.compile()
    
    async def _modern_crawler_node(self, state: AgentState) -> AgentState:
        """Modern crawler node with advanced tools"""
        print("🚀 Starting modern AI content crawling...")
        print("📡 Using: Firecrawl + Crawl4AI + Playwright + Premium Sources")
        
        try:
            result = await self.crawler.execute(state)
            
            # Enhanced progress reporting
            if result.data.get("crawled_content"):
                stats = result.data["crawled_content"].get("stats", {})
                tools_used = result.data["crawled_content"].get("metadata", {}).get("tools_used", [])
                
                print(f"✅ Modern crawling completed:")
                print(f"   • Success rate: {stats.get('success_rate', 0):.1%}")
                print(f"   • Total items: {stats.get('total_items', 0)}")
                print(f"   • Tools used: {', '.join(tools_used) if tools_used else 'Fallback only'}")
                print(f"   • Quality score: {result.data['crawled_content'].get('metadata', {}).get('extraction_quality', 0):.2f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Modern crawler failed: {e}")
            state.error = f"Modern crawler error: {str(e)}"
            return state
    
    async def _ai_processor_node(self, state: AgentState) -> AgentState:
        """Enhanced AI processor node"""
        if state.error:
            print("⏭️  Skipping AI processing due to crawler error")
            return state
        
        # Check content availability
        crawled_content = state.data.get("crawled_content", {})
        total_items = crawled_content.get("stats", {}).get("total_items", 0)
        
        if total_items == 0:
            error_msg = "No content available for AI processing"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
        
        print(f"🧠 Starting AI content processing...")
        print(f"📊 Processing {total_items} items with AI analysis")
        
        try:
            result = await self.processor.execute(state)
            
            # Enhanced processing feedback
            if result.data.get("processed_content"):
                processed_count = len(result.data["processed_content"])
                print(f"✅ AI processing completed: {processed_count} items processed")
            
            return result
            
        except Exception as e:
            error_msg = f"AI processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _ai_writer_node(self, state: AgentState) -> AgentState:
        """Enhanced AI writer node"""
        if state.error:
            print("⏭️  Skipping AI writing due to previous error")
            return state
        
        processed_content = state.data.get("processed_content", [])
        
        if not processed_content:
            error_msg = "No processed content available for AI article generation"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
        
        print(f"✍️  Starting AI article generation...")
        print(f"📝 Generating articles from {len(processed_content)} processed items")
        
        try:
            result = await self.writer.execute(state)
            
            # Enhanced writing feedback
            if result.data.get("generated_articles"):
                articles_count = len(result.data["generated_articles"])
                avg_word_count = sum(a.get("word_count", 0) for a in result.data["generated_articles"]) / max(articles_count, 1)
                print(f"✅ AI writing completed: {articles_count} articles generated")
                print(f"   • Average word count: {avg_word_count:.0f}")
            
            return result
            
        except Exception as e:
            error_msg = f"AI writing failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.error = error_msg
            return state
    
    async def _quality_validator_node(self, state: AgentState) -> AgentState:
        """Advanced quality validator with modern standards"""
        if state.error:
            print("⏭️  Skipping quality validation due to previous error")
            return state
        
        print("🔍 Starting advanced quality validation...")
        
        generated_articles = state.data.get("generated_articles", [])
        
        if not generated_articles:
            print("⚠️  No articles to validate")
            state.data["validated_articles"] = []
            state.data["validation_report"] = {
                "total_articles": 0,
                "valid_articles": 0,
                "overall_quality": 0.0,
                "rejection_reasons": []
            }
            return state
        
        valid_articles = []
        validation_report = {
            "total_articles": len(generated_articles),
            "valid_articles": 0,
            "rejected_articles": 0,
            "rejection_reasons": [],
            "quality_distribution": {"high": 0, "medium": 0, "low": 0},
            "average_quality": 0.0,
            "modern_metrics": {
                "ai_relevance": 0.0,
                "content_structure": 0.0,
                "source_quality": 0.0
            }
        }
        
        total_quality_score = 0
        
        for i, article in enumerate(generated_articles, 1):
            print(f"   📄 Validating article {i}/{len(generated_articles)}")
            
            # Modern validation criteria
            validation_result = self._validate_article_modern(article)
            
            if validation_result["is_valid"]:
                # Enhanced article with validation metadata
                enhanced_article = {
                    **article,
                    "validation_score": validation_result["score"],
                    "quality_tier": validation_result["tier"],
                    "validation_details": validation_result["details"]
                }
                valid_articles.append(enhanced_article)
                validation_report["valid_articles"] += 1
                validation_report["quality_distribution"][validation_result["tier"]] += 1
            else:
                validation_report["rejected_articles"] += 1
                validation_report["rejection_reasons"].extend(validation_result["reasons"])
                print(f"      ❌ Rejected: {', '.join(validation_result['reasons'])}")
            
            total_quality_score += validation_result["score"]
        
        # Calculate metrics
        validation_report["average_quality"] = total_quality_score / len(generated_articles)
        validation_report["success_rate"] = validation_report["valid_articles"] / validation_report["total_articles"]
        
        # Modern metrics calculation
        if valid_articles:
            validation_report["modern_metrics"] = {
                "ai_relevance": sum(a.get("ai_relevance_score", 0.5) for a in valid_articles) / len(valid_articles),
                "content_structure": sum(a.get("structure_score", 0.5) for a in valid_articles) / len(valid_articles),
                "source_quality": sum(a.get("source_quality", 0.5) for a in valid_articles) / len(valid_articles)
            }
        
        state.data["validated_articles"] = valid_articles
        state.data["validation_report"] = validation_report
        
        print(f"✅ Quality validation completed:")
        print(f"   • Valid articles: {validation_report['valid_articles']}/{validation_report['total_articles']}")
        print(f"   • Success rate: {validation_report['success_rate']:.1%}")
        print(f"   • Average quality: {validation_report['average_quality']:.2f}")
        print(f"   • Quality distribution: High({validation_report['quality_distribution']['high']}) Medium({validation_report['quality_distribution']['medium']}) Low({validation_report['quality_distribution']['low']})")
        
        return state
    
    def _validate_article_modern(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Modern article validation with enhanced criteria"""
        score = 0.0
        reasons = []
        details = {}
        
        # Basic content validation
        title = article.get("title", "")
        content = article.get("content", "")
        word_count = article.get("word_count", 0)
        
        # Title validation (20% of score)
        if len(title) < 10:
            reasons.append("Title too short")
        elif len(title) > 200:
            reasons.append("Title too long")
        elif 30 <= len(title) <= 120:
            score += 0.2
        elif 10 <= len(title) <= 200:
            score += 0.1
        
        details["title_length"] = len(title)
        
        # Content length validation (25% of score)
        if word_count < 300:
            reasons.append("Content too short")
        elif word_count >= 800:
            score += 0.25
        elif word_count >= 500:
            score += 0.15
        elif word_count >= 300:
            score += 0.1
        
        details["word_count"] = word_count
        
        # AI relevance validation (20% of score)
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'neural', 'algorithm', 'model', 'llm', 'gpt', 'deep learning']
        ai_relevance = sum(1 for keyword in ai_keywords if keyword.lower() in content.lower()) / len(ai_keywords)
        article["ai_relevance_score"] = ai_relevance
        
        if ai_relevance >= 0.3:
            score += 0.2
        elif ai_relevance >= 0.2:
            score += 0.15
        elif ai_relevance >= 0.1:
            score += 0.1
        else:
            reasons.append("Low AI relevance")
        
        details["ai_relevance"] = ai_relevance
        
        # Content structure validation (15% of score)
        structure_indicators = [
            content.count('\n\n') >= 3,  # Multiple paragraphs
            len(content.split('.')) >= 10,  # Sufficient sentences
            any(marker in content.lower() for marker in ['introduction', 'conclusion', 'overview', 'summary']),  # Structure markers
            content.count('•') + content.count('-') + content.count('*') >= 2  # Lists or bullet points
        ]
        structure_score = sum(structure_indicators) / len(structure_indicators)
        article["structure_score"] = structure_score
        
        if structure_score >= 0.75:
            score += 0.15
        elif structure_score >= 0.5:
            score += 0.1
        elif structure_score >= 0.25:
            score += 0.05
        
        details["structure_score"] = structure_score
        
        # Source quality validation (10% of score)
        sources_count = article.get("sources_count", 0)
        source_quality = min(sources_count / 3, 1.0)  # Normalize to 0-1
        article["source_quality"] = source_quality
        
        if source_quality >= 0.8:
            score += 0.1
        elif source_quality >= 0.5:
            score += 0.05
        
        details["source_quality"] = source_quality
        
        # Modern content indicators (10% of score)
        modern_indicators = [
            any(year in content for year in ['2024', '2023', '2025']),  # Recent content
            any(term in content.lower() for term in ['chatgpt', 'claude', 'gemini', 'llama']),  # Modern AI tools
            any(term in content.lower() for term in ['transformer', 'attention', 'embedding']),  # Modern techniques
        ]
        modernity_score = sum(modern_indicators) / len(modern_indicators)
        
        if modernity_score >= 0.67:
            score += 0.1
        elif modernity_score >= 0.33:
            score += 0.05
        
        details["modernity_score"] = modernity_score
        
        # Determine quality tier
        if score >= 0.8:
            tier = "high"
        elif score >= 0.6:
            tier = "medium"
        else:
            tier = "low"
        
        # Article is valid if score >= 0.6 and no critical issues
        is_valid = score >= 0.6 and len(reasons) == 0
        
        return {
            "is_valid": is_valid,
            "score": score,
            "tier": tier,
            "reasons": reasons,
            "details": details
        }
    
    async def run(self, initial_state: AgentState = None) -> Dict[str, Any]:
        """Run the unified modern workflow"""
        if initial_state is None:
            initial_state = AgentState()
        
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        initial_state.data["workflow_id"] = workflow_id
        
        print("🚀 Starting Unified Modern AI Content Workflow")
        print("=" * 70)
        print("🔧 Modern Tools Stack:")
        print("   • Crawler: Firecrawl + Crawl4AI + Playwright")
        print("   • Processor: Enhanced AI Analysis")
        print("   • Writer: Advanced AI Generation")
        print("   • Validator: Modern Quality Control")
        print(f"   • Workflow ID: {workflow_id}")
        print("=" * 70)
        
        try:
            # Run the modern workflow
            result = await self.workflow.ainvoke(initial_state)
            
            if result.error:
                print(f"❌ Workflow failed: {result.error}")
                return {
                    "success": False,
                    "error": result.error,
                    "workflow_id": workflow_id,
                    "progress": getattr(result, 'progress', {})
                }
            
            # Extract comprehensive results
            result_data = result.data
            
            # Crawling metrics
            crawled_content = result_data.get("crawled_content", {})
            crawl_stats = crawled_content.get("stats", {})
            tools_used = crawled_content.get("metadata", {}).get("tools_used", [])
            
            # Processing metrics
            processed_content = result_data.get("processed_content", [])
            
            # Generation metrics
            validated_articles = result_data.get("validated_articles", [])
            validation_report = result_data.get("validation_report", {})
            
            # Calculate comprehensive statistics
            workflow_results = {
                "success": True,
                "workflow_id": workflow_id,
                "timestamp": crawled_content.get("crawl_timestamp"),
                
                # Crawling results
                "crawling": {
                    "total_sources": crawl_stats.get("total_sources", 0),
                    "successful_sources": crawl_stats.get("successful", 0),
                    "success_rate": crawl_stats.get("success_rate", 0),
                    "total_items": crawl_stats.get("total_items", 0),
                    "tools_used": tools_used,
                    "extraction_quality": crawled_content.get("metadata", {}).get("extraction_quality", 0)
                },
                
                # Processing results
                "processing": {
                    "items_processed": len(processed_content),
                    "processing_success": len(processed_content) > 0
                },
                
                # Generation results
                "generation": {
                    "articles_generated": validation_report.get("total_articles", 0),
                    "articles_validated": validation_report.get("valid_articles", 0),
                    "validation_success_rate": validation_report.get("success_rate", 0),
                    "average_quality": validation_report.get("average_quality", 0),
                    "quality_distribution": validation_report.get("quality_distribution", {}),
                    "modern_metrics": validation_report.get("modern_metrics", {})
                },
                
                # Final output
                "articles": validated_articles,
                "processed_content": processed_content,
                "validation_report": validation_report,
                
                # File paths
                "file_paths": {
                    "crawled_content": result_data.get("crawled_content_file"),
                    "processed_content": result_data.get("processed_content_file"),
                    "generated_articles": result_data.get("generated_articles_file")
                },
                
                # Configuration used
                "configuration": {
                    "firecrawl_enabled": bool(self.firecrawl_api_key),
                    "openai_enabled": bool(self.openai_api_key),
                    "crawler_tools": len(tools_used),
                    "workflow_version": "unified_modern_v1.0"
                }
            }
            
            # Final summary
            print("=" * 70)
            print("🎉 Unified Modern Workflow Completed Successfully!")
            print("📊 Final Results:")
            print(f"   • Sources crawled: {workflow_results['crawling']['successful_sources']}/{workflow_results['crawling']['total_sources']}")
            print(f"   • Content extracted: {workflow_results['crawling']['total_items']} items")
            print(f"   • Articles generated: {workflow_results['generation']['articles_validated']} validated")
            print(f"   • Overall quality: {workflow_results['generation']['average_quality']:.2f}/1.0")
            print(f"   • Tools utilized: {', '.join(tools_used) if tools_used else 'Fallback only'}")
            print(f"   • Extraction quality: {workflow_results['crawling']['extraction_quality']:.2f}/1.0")
            print("=" * 70)
            
            return workflow_results
            
        except Exception as e:
            error_msg = f"Unified workflow execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id
            }


# Convenience function to run the unified modern workflow
async def run_unified_modern_workflow(
    openai_api_key: str = None,
    firecrawl_api_key: str = None
) -> Dict[str, Any]:
    """
    Run the complete unified modern AI content generation workflow.
    
    Args:
        openai_api_key: OpenAI API key for content processing and generation
        firecrawl_api_key: Firecrawl API key for premium content extraction
    
    Returns:
        Comprehensive workflow results with modern metrics
    """
    # Auto-detect API keys from environment if not provided
    if not openai_api_key:
        openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ARK_API_KEY')
    
    if not firecrawl_api_key:
        firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    workflow = UnifiedModernWorkflow(
        openai_api_key=openai_api_key,
        firecrawl_api_key=firecrawl_api_key
    )
    
    return await workflow.run()