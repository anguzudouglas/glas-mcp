from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import yaml
import os

class BaseTool(ABC):
    """
    Abstract base class for all Glas MCP tools.
    """

    def __init__(self, tool_dir: str):
        self.tool_dir = tool_dir
        self.config = self._load_tool_yaml()

    def _load_tool_yaml(self) -> Dict[str, Any]:
        """
        Loads the tool.yaml file from the tool directory.
        """
        yaml_path = os.path.join(self.tool_dir, "tool.yaml")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"tool.yaml not found in {self.tool_dir}")
        
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f)

    @property
    def name(self) -> str:
        return self.config.get("name", "unknown_tool")

    @property
    def description(self) -> str:
        return self.config.get("description", "")

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.config.get("input_schema", {"type": "object", "properties": {}})

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """
        The core logic of the tool.
        """
        pass
