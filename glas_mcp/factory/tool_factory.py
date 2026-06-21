import importlib.util
import os
from typing import Type, Optional
from glas_mcp.tools.base import BaseTool

class ToolFactory:
    """
    Factory for creating tool instances.
    """

    @staticmethod
    def create_tool(tool_dir: str) -> Optional[BaseTool]:
        """
        Dynamically loads and instantiates a tool from a directory.
        """
        main_path = os.path.join(tool_dir, "main.py")
        if not os.path.exists(main_path):
            return None

        module_name = os.path.basename(tool_dir)
        spec = importlib.util.spec_from_file_location(f"glas_mcp.tools.{module_name}.main", main_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the class that inherits from BaseTool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseTool) and 
                    attr is not BaseTool):
                    return attr(tool_dir=tool_dir)
        
        return None
