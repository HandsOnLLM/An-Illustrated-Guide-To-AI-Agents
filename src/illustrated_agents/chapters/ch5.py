from illustrated_agents import LLM, Memory, Tools
from illustrated_agents.utils import DiffViewer
from illustrated_agents.chapters import ch4
from illustrated_agents.utils import CodeAnnotator


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = None  # Chapter 6: Add Planning
        self.reflector = None  # Chapter 6: Add Reflection

        # Tell the LLM about available tools
        system_prompt = "You are a helpful assistant.\n\n" + self.tools.prompt
        self.memory.add("user", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        # 1. Every step, we add the user task to memory
        self.memory.add("user", task)

        # 2. Then, we generate a response based on the conversation history
        response = self.llm.generate(self.memory.get_messages())

        # 3. Finally, we add the assistant's response to memory
        self.memory.add("assistant", response)

        # 4. Tool parsing and execution
        if self.tools.is_tool_call(response):
            tool_call = self.tools.parse_tool_call(response)
            observation = self.tools.run_tool(tool_call)
            return str(observation)

        return response


tinyagents_diff = DiffViewer(ch4.TinyAgent, TinyAgent, "ch4.TinyAgent", "ch5.TinyAgent")


add_tool_annotated = CodeAnnotator(
    Tools.is_tool_call,
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
        (15, 16): "We also handle the special 'intermediate_answer' tool which allows the LLM to respond without calling a real tool.",
    },
)
