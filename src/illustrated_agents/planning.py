import re
from illustrated_agents.llm import Response, LLM
from illustrated_agents.memory import Memory
from illustrated_agents.tools import Tools


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

    def parse(self, response: Response) -> Response:
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


class NativeReAct(ReAct):
    """ReAct using native LLM reasoning instead of text-based parsing."""

    @property
    def prompt(self) -> str:
        return ""

    def parse(self, response: Response) -> Response:
        return response


class PlanAndSolve(ReAct):
    """ReAct planner that gives the LLM tools to create and update its own plan."""

    def __init__(self, tools: Tools, max_steps: int = 10):
        """Initialize PlanAndSolve planner.

        Arguments:
            tools: The tool registry to attach `update_plan` and `mark_done` to.
            max_steps: Maximum number of ReAct steps to perform.
        """
        super().__init__(max_steps)
        self.plan: list[dict] = []

        tools.add_tool(
            "update_plan",
            self.update_plan,
            "Create or overwrite the plan with a list of sub-tasks: update_plan(items: list[str])",
        )
        tools.add_tool(
            "mark_done",
            self.mark_done,
            "Mark a sub-task complete by 1-based index: mark_done(index: int)",
        )

    @property
    def prompt(self) -> str:
        return super().prompt + (
            "\n## Planning\n\n"
            "For non-trivial tasks, call `update_plan` first to outline your approach, "
            "then `mark_done` as you complete each sub-task. Revise the plan with "
            "`update_plan` whenever new information changes what is needed.\n"
        )

    def update_plan(self, items: list[str]) -> str:
        """Replace the plan with a new list of sub-tasks."""
        self.plan = [{"task": item, "done": False} for item in items]
        return f"Plan updated:\n{self._render()}"

    def mark_done(self, index: int) -> str:
        """Mark a sub-task complete by 1-based index."""
        self.plan[index - 1]["done"] = True
        return f"Plan:\n{self._render()}"

    def _render(self) -> str:
        return "\n".join(
            f"{'[x]' if item['done'] else '[ ]'} {i + 1}. {item['task']}"
            for i, item in enumerate(self.plan)
        )


class Reflexion:
    """Reflector that periodically critiques recent steps and injects a course correction."""

    def __init__(self, llm: LLM, interval: int = 3):
        """Initialize Reflexion reflector.

        Arguments:
            llm: The LLM used to generate critiques.
            interval: Reflect every `interval` steps.
        """
        self.llm = llm
        self.interval = interval

    def reflect(self, memory: Memory, step: int) -> None:
        """Critique recent steps and add a corrective user message to memory."""
        if step == 0 or step % self.interval:
            return
        critique = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": "Critique the agent's recent steps and suggest a course correction.",
                },
                *memory.get_messages()[-6:],
            ]
        )
        memory.add("user", f"[Reflection] {critique.content}")
