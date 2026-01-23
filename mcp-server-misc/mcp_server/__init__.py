"""
MCP Server Misc - Web Context Protocol Server

A generalized MCP server for fetching and caching web documentation.
Can be configured for any set of URLs and integrated into multiple projects.
"""

__version__ = "1.0.0"
__author__ = "artqcid"

from .server import MCPServer
from .context import ContextResolver
from .config import Config

__all__ = ["MCPServer", "ContextResolver", "Config"]
