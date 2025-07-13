"""
Base agent class for the multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

from core.exceptions import AppException

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Base state for all agents"""
    messages: List[BaseMessage] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    current_step: str = ""
    error: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None
    timestamp: str = ""
    
    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, config: Optional[Any] = None):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"agents.{name}")
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main logic"""
        pass
    
    def format_output(self, data: Any, status: str = "success") -> Dict[str, Any]:
        """Format agent output for next step"""
        return {
            "agent": self.name,
            "status": status,
            "output": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_error(self, error: Exception, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent errors consistently"""
        error_msg = str(error)
        self.logger.error(f"Agent {self.name} failed: {error_msg}")
        
        return {
            **state,
            "error": error_msg,
            "agent_status": f"{self.name}_failed",
            "timestamp": datetime.now().isoformat()
        }
    
    def update_progress(self, state: Dict[str, Any], step: str, progress: int = 0) -> Dict[str, Any]:
        """Update progress information"""
        progress_info = state.get("progress", {})
        progress_info[self.name] = {
            "current_step": step,
            "progress_percent": progress,
            "last_update": datetime.now().isoformat()
        }
        
        return {
            **state,
            "progress": progress_info,
            "current_step": f"{self.name}: {step}"
        }
    
    def validate_input(self, state: Dict[str, Any], required_keys: List[str]) -> None:
        """Validate required input keys"""
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            raise AppException(f"Missing required input keys: {missing_keys}")
    
    async def pre_execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-execution hook for common setup"""
        self.logger.info(f"Starting {self.name} agent execution")
        return self.update_progress(state, "initializing", 0)
    
    async def post_execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Post-execution hook for cleanup"""
        self.logger.info(f"Completed {self.name} agent execution")
        return self.update_progress(state, "completed", 100)