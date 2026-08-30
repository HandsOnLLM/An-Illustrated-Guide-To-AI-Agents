import urllib.request

from mcp.server.mcpserver import MCPServer


# Initialize an MCP server
server = MCPServer("file_reader")


# Define our tools
@server.tool()
def read_markdown(path: str) -> str:
    """Read the content of a markdown file.

    Args:
        path (str): The path to the markdown file.
    """
    with urllib.request.urlopen(path) as response:
        return response.read().decode()


# Run the server
def main():
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
