import sys
from unittest.mock import MagicMock

def mock_tool(*args, **kwargs):
    def decorator(f):
        return f
    return decorator

mock_mcp = MagicMock()
mock_mcp.tool = mock_tool

class MockFastMCP:
    def __init__(self, name):
        self.name = name
        self.tool = mock_tool
    def run(self):
        pass

mock_fastmcp_module = MagicMock()
mock_fastmcp_module.FastMCP = MockFastMCP

sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = mock_fastmcp_module
