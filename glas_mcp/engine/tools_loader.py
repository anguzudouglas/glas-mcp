import os
from typing import List, Dict, Optional
from glas_mcp.factory.tool_factory import ToolFactory
from glas_mcp.tools.base import BaseTool

class ToolsLoader:
    """
    Engine component to discover and load all tools.
    """

    def __init__(self, tools_root: str):
        self.tools_root = tools_root
        self.tools: Dict[str, BaseTool] = {}

    def load_all(self) -> Dict[str, BaseTool]:
        """
        Scans the tools directory and loads all valid tools.
        """
        for entry in os.scandir(self.tools_root):
            if entry.is_dir() and not entry.name.startswith("__"):
                tool = ToolFactory.create_tool(entry.path)
                if tool:
                    self.tools[tool.name] = tool
        return self.tools

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)
