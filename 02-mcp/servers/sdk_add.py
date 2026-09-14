from mcp.server.mcpserver import MCPServer

mcp = MCPServer("sdk-add")

@mcp.tool()
def add(a: float, b: float) -> str:
    """两个数相加"""
    return str(a + b)

if __name__ == "__main__":
    mcp.run(transport="stdio")