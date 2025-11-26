"""Public entry point for the MCP web tool package."""

from .metadata import TOOL_METADATA
from .web import WebTool

__all__ = ["WebTool", "TOOL_METADATA"]
