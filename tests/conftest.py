import sys
from unittest.mock import MagicMock

# Mock 'mcp' module
mock_mcp = MagicMock()
sys.modules['mcp'] = mock_mcp
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()

# FastMCP mock needs to be a class that can be instantiated
class MockFastMCP:
    def __init__(self, *args, **kwargs):
        pass
    def tool(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator
    def run(self, *args, **kwargs):
        pass

sys.modules['mcp.server.fastmcp'].FastMCP = MockFastMCP
