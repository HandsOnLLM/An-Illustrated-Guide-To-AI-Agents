from dataclasses import dataclass

from illustrated_agents.llm import Response


@dataclass
class Step:
    """A single step in an agent's trajectory."""

    thought: str = ""
    action: dict | None = None
    observation: str | None = None
    answer: str | None = None
    metadata: dict | None = None


class Trajectory:
    """Records agent execution as a sequence of runs.

    Each run is a dict with keys "query" (str) and "steps" (list[Step]).
    """

    def __init__(self) -> None:
        self.runs: list[dict] = []

    def new_run(self, query: str) -> None:
        """Register a new run with the given query."""
        self.runs.append({"query": query, "steps": []})

    def add_step(self, response: Response, observation: str | None = None) -> None:
        """Record a step from a Response, optionally with a tool observation."""
        step = Step(
            thought=response.reasoning or "",
            metadata=response.metadata,
        )
        if observation is not None:
            step.action = response.tool_call
            step.observation = observation
        else:
            step.answer = response.content
        self.runs[-1]["steps"].append(step)

    @property
    def steps(self) -> list[Step]:
        """All steps across all runs (flat list)."""
        return [step for run in self.runs for step in run["steps"]]

    @property
    def last_run(self) -> dict | None:
        """The most recent run."""
        return self.runs[-1] if self.runs else None
