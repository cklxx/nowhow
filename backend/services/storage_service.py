"""
File storage service implementation.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
import logging

from config import Settings
from core.interfaces import IStorageService
from core.exceptions import StorageError

logger = logging.getLogger(__name__)


class FileStorageService(IStorageService):
    """File-based storage service implementation."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = settings.services.storage
        
        # Handle config access properly
        base_path = getattr(self.config, 'base_path', './data')
        self.base_path = Path(base_path)
        
        # Create base directory if it doesn't exist
        create_dirs = getattr(self.config, 'create_dirs', True)
        if create_dirs:
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['sources', 'workflows', 'content', 'articles', 'logs']
            for subdir in subdirs:
                (self.base_path / subdir).mkdir(exist_ok=True)
    
    async def save_json(
        self,
        data: Union[Dict, List],
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save data as JSON file."""
        try:
            filepath = self.get_file_path(filename, workflow_id)
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            if isinstance(data, dict):
                data = {
                    **data,
                    "_metadata": {
                        "created_at": datetime.now().isoformat(),
                        "workflow_id": workflow_id,
                        "file_type": "json"
                    }
                }
            
            # Write file atomically
            temp_filepath = filepath.with_suffix('.tmp')
            
            def write_file():
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                temp_filepath.rename(filepath)
            
            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, write_file)
            
            logger.info(f"Saved JSON data to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save JSON data: {e}")
            raise StorageError(f"Failed to save JSON data: {str(e)}")
    
    async def load_json(self, filepath: Union[str, Path]) -> Union[Dict, List]:
        """Load data from JSON file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found: {filepath}")
            
            def read_file():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Run in thread pool to avoid blocking
            data = await asyncio.get_event_loop().run_in_executor(None, read_file)
            
            logger.debug(f"Loaded JSON data from {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {filepath}: {e}")
            raise StorageError(f"Invalid JSON in file {filepath}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load JSON data: {e}")
            raise StorageError(f"Failed to load JSON data: {str(e)}")
    
    async def save_text(
        self,
        content: str,
        filename: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Save content as text file."""
        try:
            filepath = self.get_file_path(filename, workflow_id)
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata header for text files
            metadata_header = f"""---
created_at: {datetime.now().isoformat()}
workflow_id: {workflow_id}
file_type: text
---

"""
            
            full_content = metadata_header + content
            
            # Write file atomically
            temp_filepath = filepath.with_suffix('.tmp')
            
            def write_file():
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                temp_filepath.rename(filepath)
            
            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, write_file)
            
            logger.info(f"Saved text content to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save text content: {e}")
            raise StorageError(f"Failed to save text content: {str(e)}")
    
    async def load_text(self, filepath: Union[str, Path]) -> str:
        """Load content from text file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found: {filepath}")
            
            def read_file():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Run in thread pool to avoid blocking
            content = await asyncio.get_event_loop().run_in_executor(None, read_file)
            
            # Remove metadata header if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            
            logger.debug(f"Loaded text content from {filepath}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load text content: {e}")
            raise StorageError(f"Failed to load text content: {str(e)}")
    
    def get_file_path(
        self,
        pattern: str,
        workflow_id: Optional[str] = None
    ) -> Path:
        """Get file path based on pattern."""
        try:
            # Check if pattern is a predefined pattern
            file_patterns = getattr(self.config, 'file_patterns', {})
            if hasattr(file_patterns, 'to_dict'):
                file_patterns = file_patterns.to_dict()
            
            if pattern in file_patterns:
                pattern = file_patterns[pattern]
            
            # Substitute variables in pattern
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workflow_id = workflow_id or "default"
            
            filename = pattern.format(
                timestamp=timestamp,
                workflow_id=workflow_id,
                date=datetime.now().strftime("%Y%m%d"),
                time=datetime.now().strftime("%H%M%S")
            )
            
            return self.base_path / filename
            
        except Exception as e:
            logger.error(f"Failed to get file path: {e}")
            raise StorageError(f"Failed to get file path: {str(e)}")
    
    async def list_files(
        self,
        pattern: Optional[str] = None,
        directory: Optional[str] = None
    ) -> List[Path]:
        """List files matching pattern in directory."""
        try:
            search_dir = self.base_path
            if directory:
                search_dir = self.base_path / directory
            
            if not search_dir.exists():
                return []
            
            def list_files():
                if pattern:
                    return list(search_dir.glob(pattern))
                else:
                    return list(search_dir.iterdir())
            
            # Run in thread pool to avoid blocking
            files = await asyncio.get_event_loop().run_in_executor(None, list_files)
            
            # Filter to only files (not directories)
            return [f for f in files if f.is_file()]
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise StorageError(f"Failed to list files: {str(e)}")
    
    async def delete_file(self, filepath: Union[str, Path]) -> bool:
        """Delete a file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                logger.warning(f"File not found for deletion: {filepath}")
                return False
            
            def delete_file():
                filepath.unlink()
                return True
            
            # Run in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(None, delete_file)
            
            logger.info(f"Deleted file: {filepath}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise StorageError(f"Failed to delete file: {str(e)}")
    
    async def backup_file(self, filepath: Union[str, Path]) -> Path:
        """Create a backup of a file."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found for backup: {filepath}")
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filepath = filepath.with_name(f"{filepath.stem}_{timestamp}_backup{filepath.suffix}")
            
            def copy_file():
                import shutil
                shutil.copy2(filepath, backup_filepath)
                return backup_filepath
            
            # Run in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(None, copy_file)
            
            logger.info(f"Created backup: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to backup file: {e}")
            raise StorageError(f"Failed to backup file: {str(e)}")
    
    async def get_file_info(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """Get file information."""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise StorageError(f"File not found: {filepath}")
            
            def get_stats():
                stat = filepath.stat()
                return {
                    "path": str(filepath),
                    "name": filepath.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_file": filepath.is_file(),
                    "is_dir": filepath.is_dir(),
                    "suffix": filepath.suffix
                }
            
            # Run in thread pool to avoid blocking
            info = await asyncio.get_event_loop().run_in_executor(None, get_stats)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise StorageError(f"Failed to get file info: {str(e)}")