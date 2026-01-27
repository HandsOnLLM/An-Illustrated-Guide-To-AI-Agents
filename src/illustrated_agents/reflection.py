class Reflector:
    """Reflection module for agent self-evaluation."""

    def __init__(self, interval: int = 3):
        """Initialize the reflector.

        Arguments:
            interval: Reflect every N steps.
        """
        self.interval = interval

    @property
    def prompt(self) -> str:
        """The reflection prompt to inject into the conversation."""
        return """
REFLECTION: Take a moment to evaluate your progress.
- Are you making progress toward the goal?
- Should you try a different approach?
- What have you learned from previous steps?

Continue with your next THOUGHT and ACTION."
"""

    def should_reflect(self, step: int) -> bool:
        """Determine if the agent should reflect at this step."""
        return step > 0 and step % self.interval == 0
