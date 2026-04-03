from illustrated_agents import LLM, Memory, Tools, ReAct
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview
from illustrated_agents.chapters import ch5


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.reflector = None  # Chapter 6: Add Reflection
        self.skills = None  # Chapter 6: Add Skills

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages())
        self.memory.add("assistant", response)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return None

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(action)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("kwargs", "")

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)
        obs_prompt = f"OBSERVATION: {action} -> {observation}"
        self.memory.add("user", obs_prompt)

        return None


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Autonomy with a for-loop ;) ..."),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", "new", "Added the ReAct (Reason and Act) framework"),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch5.TinyAgent, TinyAgent, "ch5.TinyAgent", "ch6.TinyAgent")


react_prompt_annotated = CodeAnnotator(
    ReAct.prompt,
    annotations={
        (6, 7): "Main explanation of the ReAct framework.",
        13: "<b>THOUGHT</b> - reasoning about next step.",
        (14, 19): "<b>ACTION</b> - tool call format.",
        20: "<b>OBSERVATION</b> - provided after action.",
        (27, 31): "<b>ACTION</b> - Final answer format - must be used to complete the task.",
    },
)


react_parse_annotated = CodeAnnotator(
    ReAct.parse,
    annotations={
        (5, 8): """Extracts the <b>THOUGHT</b> and <b>ACTION</b> sections from the response. 
        Note that we stop at <b>OBSERVATION</b> to avoid hallucinated observations.""",
        (13, 14): """Searches for all matches using regular expressions (regex). 
        The re.DOTALL flag allows . to match newlines and re.IGNORECASE makes the search case-insensitive. 
        If a match is found, it extracts and trims the content; otherwise, it assigns an empty string.""",
    },
)

tinyagent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (11, 12): "We added the prompt of the ReAct module to the system prompt and follow it up with the tools prompt.",
    },
)

tinyagent_run_annotated = CodeAnnotator(
    TinyAgent.run,
    annotations={
        3: "The initial task is immediately added to memory as a user message so that the Agent can reference it during the loop.",
        (6, 9): "The `Autonomy` (ReAct) loop where the agent performs steps until completion or max steps reached.",
    },
)

tinyagent_step_annotated = CodeAnnotator(
    TinyAgent._step,
    annotations={
        (4, 5): "A response is generated and added to memory.",
        8: "The output needs to be parsed into THOUGHT and ACTION using the ReAct parser. That way, we end with a `parsed` dict containing those two elements.",
        (11, 12): "If the ACTION contains a tool call, we execute it using the `_execute_action` method.",
    },
)

tinyagent_action_annotated = CodeAnnotator(
    TinyAgent._execute_action,
    annotations={
        3: "The JSON string representing the tool call is parsed into a dictionary using the Tools module.",
        (6, 7): "If the tool is 'final_answer', we return the final answer and end the loop.",
        (
            10,
            12,
        ): "If it's a regular tool, we execute it and add the observation to memory. We do not return anything, so the loop can continue.",
    },
)
