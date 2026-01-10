---
name: ros-mcp
description: List available MCP servers for Ralph-On-Shelf
arguments: []
---

# ROS MCP Servers

List all available MCP (Model Context Protocol) servers that Ralph can connect to.

## Execute

```bash
cd {{cwd}} && python -c "
from mcp_registry import list_servers_summary, get_all_servers
from mcp_selector import get_available_servers

print(list_servers_summary())
print()
print('Currently Available (auth configured):')
available = get_available_servers()
if available:
    for name in available:
        print(f'  - {name}')
else:
    print('  Only open/no-auth servers available')
print()
print('To use MCP servers with ROS:')
print('  /ros \"your task\" --mcp auto        # Auto-select based on task')
print('  /ros \"your task\" --mcp exa-search  # Use specific server')
print('  /ros \"your task\" --mcp none        # Disable MCP')
"
```
