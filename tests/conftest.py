import sys
from unittest.mock import MagicMock

# The environment lacks 'requests' and 'mcp' libraries.
# We inject mocks into sys.modules so that tests and the app can be imported.

if 'requests' not in sys.modules:
    sys.modules['requests'] = MagicMock()

if 'mcp' not in sys.modules:
    mock_mcp = MagicMock()
    # FastMCP is used in some parts of the codebase
    mock_mcp.server.fastmcp.FastMCP = MagicMock()
    sys.modules['mcp'] = mock_mcp
    sys.modules['mcp.server'] = MagicMock()
    sys.modules['mcp.server.fastmcp'] = MagicMock()
