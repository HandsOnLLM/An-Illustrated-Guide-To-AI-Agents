from illustrated_agents.chapters.ch6 import ReAct
from illustrated_agents.utils import ChapterOverview


class NativeReAct(ReAct):
    """ReAct using native LLM reasoning instead of text-based parsing."""

    @property
    def prompt(self) -> str:
        return ""

    def parse(self, response):
        return response


what_we_built = ChapterOverview(
    [
        ("agent.py", None, ""),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", "new", "Added the `NativeReAct` class"),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)
