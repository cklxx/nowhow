import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class FileStorage:
    """Utility class for storing crawled content and generated articles to local files"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Get the project root directory (one level up from backend)
            current_dir = Path(__file__).parent.parent.parent  # /Users/ckl/code/nowhow
            base_path = current_dir
        
        self.base_path = Path(base_path)
        self.docs_path = self.base_path / "docs"
        self.articles_path = self.base_path / "generated_articles"
        
        # Create directories if they don't exist
        self.docs_path.mkdir(exist_ok=True)
        self.articles_path.mkdir(exist_ok=True)
        
    def save_crawled_content(self, content: Dict[str, Any], workflow_id: str = None) -> str:
        """Save crawled content to docs folder"""
        if not workflow_id:
            workflow_id = str(uuid.uuid4())[:8]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawled_content_{timestamp}_{workflow_id}.json"
        filepath = self.docs_path / filename
        
        # Add metadata
        content_with_meta = {
            "metadata": {
                "workflow_id": workflow_id,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "content_type": "crawled_raw"
            },
            "content": content
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content_with_meta, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"📁 Saved crawled content to: {filepath}")
        return str(filepath)
    
    def save_processed_content(self, content: List[Dict[str, Any]], workflow_id: str = None) -> str:
        """Save processed/structured content to docs folder"""
        if not workflow_id:
            workflow_id = str(uuid.uuid4())[:8]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_content_{timestamp}_{workflow_id}.json"
        filepath = self.docs_path / filename
        
        # Add metadata
        content_with_meta = {
            "metadata": {
                "workflow_id": workflow_id,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "content_type": "processed_structured",
                "item_count": len(content)
            },
            "content": content
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content_with_meta, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"📁 Saved processed content to: {filepath}")
        return str(filepath)
    
    def save_generated_articles(self, articles: List[Dict[str, Any]], workflow_id: str = None) -> str:
        """Save generated articles to separate folder"""
        if not workflow_id:
            workflow_id = str(uuid.uuid4())[:8]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articles_{timestamp}_{workflow_id}.json"
        filepath = self.articles_path / filename
        
        # Add metadata
        articles_with_meta = {
            "metadata": {
                "workflow_id": workflow_id,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "content_type": "generated_articles",
                "article_count": len(articles)
            },
            "articles": articles
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles_with_meta, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"📝 Saved generated articles to: {filepath}")
        
        # Also save individual markdown files for each article
        self._save_individual_articles(articles, workflow_id, timestamp)
        
        return str(filepath)
    
    def _save_individual_articles(self, articles: List[Dict[str, Any]], workflow_id: str, timestamp: str):
        """Save individual articles as markdown files"""
        articles_dir = self.articles_path / f"articles_{timestamp}_{workflow_id}"
        articles_dir.mkdir(exist_ok=True)
        
        for i, article in enumerate(articles, 1):
            # Create safe filename from title
            title = article.get("title", f"Article_{i}")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            filename = f"{i:02d}_{safe_title}.md"
            filepath = articles_dir / filename
            
            # Create markdown content
            md_content = self._format_article_as_markdown(article)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
                
        print(f"📄 Saved {len(articles)} individual articles to: {articles_dir}")
    
    def _format_article_as_markdown(self, article: Dict[str, Any]) -> str:
        """Format article as markdown"""
        title = article.get("title", "Untitled")
        content = article.get("content", "")
        summary = article.get("summary", "")
        category = article.get("category", "General")
        tags = article.get("tags", [])
        word_count = article.get("word_count", 0)
        sources = article.get("sources", [])
        
        md_content = f"""# {title}

**Category:** {category}  
**Tags:** {', '.join(tags)}  
**Word Count:** {word_count}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

{summary}

---

{content}

---

## Sources

"""
        
        for source in sources:
            md_content += f"- {source}\n"
            
        return md_content
    
    def load_crawled_content(self, workflow_id: str = None) -> Optional[Dict[str, Any]]:
        """Load crawled content from docs folder"""
        if workflow_id:
            pattern = f"crawled_content_*_{workflow_id}.json"
        else:
            pattern = "crawled_content_*.json"
            
        files = list(self.docs_path.glob(pattern))
        if not files:
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_processed_content(self, workflow_id: str = None) -> Optional[List[Dict[str, Any]]]:
        """Load processed content from docs folder"""
        if workflow_id:
            pattern = f"processed_content_*_{workflow_id}.json"
        else:
            pattern = "processed_content_*.json"
            
        files = list(self.docs_path.glob(pattern))
        if not files:
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("content", [])
    
    def list_stored_workflows(self) -> List[Dict[str, Any]]:
        """List all stored workflow results"""
        workflows = {}
        
        # Scan all files in docs and articles directories
        for pattern in ["crawled_content_*.json", "processed_content_*.json"]:
            for filepath in self.docs_path.glob(pattern):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    workflow_id = metadata.get("workflow_id")
                    
                    if workflow_id not in workflows:
                        workflows[workflow_id] = {
                            "workflow_id": workflow_id,
                            "timestamp": metadata.get("timestamp"),
                            "created_at": metadata.get("created_at"),
                            "files": []
                        }
                    
                    workflows[workflow_id]["files"].append({
                        "type": metadata.get("content_type"),
                        "filepath": str(filepath)
                    })
        
        # Add article files
        for filepath in self.articles_path.glob("articles_*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata = data.get("metadata", {})
                workflow_id = metadata.get("workflow_id")
                
                if workflow_id in workflows:
                    workflows[workflow_id]["files"].append({
                        "type": metadata.get("content_type"),
                        "filepath": str(filepath)
                    })
        
        return list(workflows.values())
    
    def load_generated_articles(self, workflow_id: str = None) -> Optional[List[Dict[str, Any]]]:
        """Load generated articles from articles folder"""
        if workflow_id:
            pattern = f"articles_*_{workflow_id}.json"
        else:
            pattern = "articles_*.json"
            
        files = list(self.articles_path.glob(pattern))
        if not files:
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("articles", [])
    
    def get_latest_articles_metadata(self) -> Optional[Dict[str, Any]]:
        """Get metadata of the latest generated articles"""
        files = list(self.articles_path.glob("articles_*.json"))
        if not files:
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            metadata = data.get("metadata", {})
            metadata["article_count"] = len(data.get("articles", []))
            metadata["filepath"] = str(latest_file)
            return metadata