from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class AgentState(BaseModel):
    """Base state for all agents"""
    messages: List[BaseMessage] = []
    data: Dict[str, Any] = {}
    current_step: str = ""
    error: Optional[str] = None
    progress: Dict[str, Any] = {}
    
class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """Execute the agent's main logic"""
        pass
    
    def format_output(self, data: Any) -> Dict[str, Any]:
        """Format agent output for next step"""
        return {"agent": self.name, "output": data}