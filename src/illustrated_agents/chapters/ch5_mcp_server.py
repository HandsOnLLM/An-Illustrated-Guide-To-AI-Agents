import requests
from mcp.server.fastmcp import FastMCP


# Initialize an MCP server
mcp = FastMCP("file_reader")


# Define our tools
@mcp.tool()
def read_markdown(path: str) -> str:
    """Read the content of a local markdown file.

    Args:
        path (str): The path to the markdown file.
    """
    return requests.get(path).text


# Run the server
def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
