import re

from illustrated_agents.chapters import ch5
from illustrated_agents.chapters.ch2 import Response
from illustrated_agents.chapters.ch5_native import Tools, LLM, Memory
from illustrated_agents.utils import DiffViewer, CodeAnnotator, ChapterOverview


class ReAct:
    """ReAct module."""

    def __init__(self, max_steps: int = 10):
        """Initialize ReAct module.

        Arguments:
            max_steps: Maximum number of ReAct steps to perform.
        """
        self.max_steps = max_steps

    @property
    def prompt(self) -> str:
        return """
# ReAct (Reason and Act)

You are a ReAct agent that performs exactly ONE step per turn.

## ReAct Format

You use the following format for each step:

THOUGHT: [Your reasoning about what to do next]
ACTION:
{
    "tool": "a_tool_name",
    "kwargs": {"param": "value"},
}

An observation will be provided after each action. You do not generate the observation yourself.

## ReAct Completion

To provide the final answer to the task, use an action blob with "tool": "final_answer" tool. 
It is the only way to complete the task, else you will be stuck on a loop. 
So your final output should look like this:

ACTION:
{
    "tool": "final_answer",
    "kwargs": "insert your final answer here"
}

Use the `final_answer` tool when you are completely done with all subtasks and have the final answer ready.
You can also use `final_answer` to directly reply to a user's question without using any other tools.
"""

    def parse(self, response) -> str:
        """Parse a ReAct formatted response into THOUGHT and ACTION."""
        text = response.content

        # The patterns for each section
        patterns = {
            "THOUGHT": r"THOUGHT:\s*(.+?)(?=ACTION:|OBSERVATION:|$)",
            "ACTION": r"ACTION:\s*(.+?)(?=THOUGHT:|OBSERVATION:|$)",
        }

        # Extract each section using regex
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            result[key] = match.group(1).strip() if match else ""

        # Update Response and extract only the action
        response.content = result["ACTION"]
        response.reasoning = result["THOUGHT"]
        return response


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
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return None

    def _execute_action(self, response: Response) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(response)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call.get("kwargs", "")

        # Execute tool and extract the observation
        observation = self.tools.run_tool(tool_call)

        # Native tool calling should get the role `tool`
        if self.tools.schemas:
            self.memory.add("tool", str(observation))
        else:
            self.memory.add("user", f"OBSERVATION: {observation}")

        return None


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Autonomy with a for-loop and ReAct planner."),
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
        12: "<b>THOUGHT</b> - reasoning about next step.",
        (13, 18): "<b>ACTION</b> - tool call format.",
        19: "<b>OBSERVATION</b> - provided after action.",
        (26, 30): "<b>ACTION</b> - Final answer format - must be used to complete the task.",
    },
)


react_parse_annotated = CodeAnnotator(
    ReAct.parse,
    annotations={
        (6, 9): """Extracts the <b>THOUGHT</b> and <b>ACTION</b> sections from the response. 
        Note that we stop at <b>OBSERVATION</b> to avoid hallucinated observations.""",
        (14, 15): """Searches for all matches using regular expressions (regex). 
        The re.DOTALL flag allows . to match newlines and re.IGNORECASE makes the search case-insensitive. 
        If a match is found, it extracts and trims the content; otherwise, it assigns an empty string.""",
    },
)

tinyagent_init_annotated = CodeAnnotator(
    TinyAgent.__init__,
    annotations={
        (
            11,
            12,
        ): "We added the prompt of the ReAct module to the system prompt and follow it up with the tools prompt.",
    },
)

tinyagent_run_annotated = CodeAnnotator(
    TinyAgent.run,
    annotations={
        3: "The initial task is immediately added to memory as a user message so that the Agent can reference it during the loop.",
        (
            6,
            9,
        ): "The `Autonomy` (ReAct) loop where the agent performs steps until completion or max steps reached.",
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
