from illustrated_agents.llm import LLM
from illustrated_agents.utils import CodeAnnotator, DiffViewer
from illustrated_agents.chapters import ch1


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM):
        self.llm = llm
        self.memory = None  # Chapter 4: Add Memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning
        self.reflector = None  # Chapter 6: Add Reflection
        self.skills = None  # Chapter 6: Add Skills

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        messages = [{"role": "user", "content": task}]
        return self.llm.generate(messages)

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        # Placeholder - will be implemented in later chapters
        return f"Executed action: {action}"


llm_annotated = CodeAnnotator(
    LLM,
    annotations={
        6: "'kwargs' are additional keyword arguments that can be passed to the underlying LLM API, such as 'api_key' or 'api_base'.",
        11: "We call the 'completion' function with any additional keyword arguments which gives back the `response` object from the LLM API.",
        14: "Although some LLMs return explicit tool calls or reasoning traces, we simply extract the answer only. This allows us to create Agents from any LLM, even those that don't support tool calls natively.",
        19: "Here, we also return only the content of the message.",
    },
)


tinyagents_diff = DiffViewer(ch1.TinyAgent, TinyAgent, "ch1.TinyAgent", "ch2.TinyAgent")
