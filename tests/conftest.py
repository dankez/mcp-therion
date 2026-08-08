import sys
from unittest.mock import MagicMock

def mock_tool(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

# Mock mcp module
mcp_mock = MagicMock()
fastmcp_mock = MagicMock()
fastmcp_mock.tool = mock_tool
mcp_mock.server.fastmcp.FastMCP = MagicMock(return_value=fastmcp_mock)

sys.modules["mcp"] = mcp_mock
sys.modules["mcp.server"] = mcp_mock.server
sys.modules["mcp.server.fastmcp"] = mcp_mock.server.fastmcp
