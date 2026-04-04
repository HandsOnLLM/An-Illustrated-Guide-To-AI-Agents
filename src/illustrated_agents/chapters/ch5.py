from illustrated_agents import LLM, Memory
from illustrated_agents.tools import Tools, MCPTools
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch4


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning
        self.reflector = None  # Chapter 6: Add Reflection
        self.skills = None  # Chapter 6: Add Skills

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n\n"
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)

        return self._step()

    def _step(self) -> str:
        """Perform a single step."""
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", response.content)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return response

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(action)

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)
        obs_prompt = f"OBSERVATION: {action} -> {observation}"
        self.memory.add("user", obs_prompt)

        return obs_prompt


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added `Tools`!"),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", "new", "This file tracks all tools that were created for easy reference."),
        ("tools.py", "new", "Created a tool registry, parsing, and execution class."),
    ]
)

what_we_built_mcp = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", "updated", "Added `MCPTools` to use Model Context Protocol (MCP)."),
    ]
)


tinyagents_diff = DiffViewer(ch4.TinyAgent, TinyAgent, "ch4.TinyAgent", "ch5.TinyAgent")


agent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (9, 12): """
A system prompt is constructed that includes the base instruction and the tool descriptions. 
This system prompt is added to memory at initialization so that the LLM is aware of the tools from the very beginning.
Note that we use `user` since not all LLMs have a separate system role.
""",
    },
)

agent_step_annotated = CodeAnnotator(
    TinyAgent._step,
    annotations={
        (7, 9): """
After generating a response, we check if the response contains a tool call. If it does, we execute the tool action instead of returning the LLM's response directly.
""",
    },
)

agent_execute_action_annotated = CodeAnnotator(
    TinyAgent._execute_action,
    annotations={
        3: "(1) The tool call is parsed to extract the tool name and arguments.",
        6: "(2) the tool is executed using the `Tools` class which looks up the tool in the registry and calls it.",
        8: "(3) The result of the tool execution is stored as an observation in memory.",
    },
)


add_tool_annotated = CodeAnnotator(
    Tools.has_tool_call,
    annotations={
        3: """We check whether there is a tool call by seeing if `"tool":` appears in the text. If it does, we think there is a tool call. """
    },
)

parse_tool_annotated = CodeAnnotator(
    Tools.parse_tool_call,
    annotations={3: "We expect a simple JSON string and only need to extract within {} brackets."},
)

run_tool_annotated = CodeAnnotator(
    Tools.run_tool,
    annotations={
        7: "The tool name and possible arguments are extracted from the parsed tool call.",
        (11, 12): "Tools are looked up in the registry and executed with the provided arguments.",
    },
)

run_mcp_tool_annotated = CodeAnnotator(
    MCPTools,
    annotations={
        6: "This is the main function for loading the tools.",
        9: "This the the path to your MCP server.",
        (15, 20): """The tools are retrieved from the MCP Server using `list_tools()`. The `list_tools()` function is a 
standardized way to query an MCP server for its available tools. This will always return a list of tool metadata, including 
tool names, descriptions, and parameter specifications.""",
        (25, 30): """The listed tools are added to the registry that we defined previously in Chapter 5 using the `Tools` class. 
Here, the `_make_tool_caller` creates a callable function for each tool that knows how to call the MCP server with the correct parameters.""",
        (42, 46): """As before, the MCP Server is called and the corresponding tool, together with their arguments, are called using 
the MCP Server. The execution is done with `session.call_tool` which again is a standardized function according to the MCP Protocol.""",
    },
)
