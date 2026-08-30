from illustrated_agents.mcp import MCPTools
from illustrated_agents.utils import CodeAnnotator, ChapterOverview


what_we_built = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", None, ""),
        (
            "tools.py",
            "updated",
            "Added `MCPTools` to use Model Context Protocol (MCP).",
        ),
        ("trajectory.py", None, ""),
    ]
)


run_mcp_tool_annotated = CodeAnnotator(
    MCPTools,
    annotations={
        6: "This is the main function for loading the tools.",
        9: "This the the path to your MCP server.",
        (
            15,
            20,
        ): """The tools are retrieved from the MCP Server using `list_tools()`. The `list_tools()` function is a
standardized way to query an MCP server for its available tools. This will always return a list of tool metadata, including
tool names, descriptions, and parameter specifications.""",
        (
            25,
            30,
        ): """The listed tools are added to the registry that we defined previously in Chapter 5 using the `Tools` class.
Here, the `_make_tool_caller` creates a callable function for each tool that knows how to call the MCP server with the correct parameters.""",
        (
            42,
            46,
        ): """As before, the MCP Server is called and the corresponding tool, together with their arguments, are called using
the MCP Server. The execution is done with `session.call_tool` which again is a standardized function according to the MCP Protocol.""",
    },
)
