from illustrated_agents.utils import CodeAnnotator, ChapterOverview


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self):
        self.llm = None  # Chapter 2 & 3: Add LLM
        self.memory = None  # Chapter 4: Add Memory
        self.tools = None  # Chapter 5: Add Tools
        self.planner = None  # Chapter 6: Add Planning

    def run(self, task: str) -> str:
        """Run the agent on a task."""
        return self._step(task)

    def _step(self, task: str) -> str:
        """Perform a single step."""
        # Placeholder - will be implemented in later chapters
        return f"Received: {task}"

    def _execute_action(self, action: str) -> str:
        """Execute a tool action."""
        # Placeholder - will be implemented in later chapters
        return f"Executed action: {action}"


what_we_built = ChapterOverview(
    [
        (
            "agent.py",
            "new",
            "`TinyAgent` skeleton - The start of something cool ;)",
        ),
    ]
)


agent_annotated = CodeAnnotator(
    TinyAgent,
    annotations={
        (
            12,
            14,
        ): "In the `run` method, we run the `TinyAgent` on a given task in either a single `_step` or multiple `_step`s.",
        (
            16,
            19,
        ): "A single step typically consists of processing the input and generating a response.",
        (21, 24): """
The `_execute_action` method is a placeholder for executing tool actions (like calling external APIs or performing calculations), 
which will be implemented in later chapters.
""",
    },
)
