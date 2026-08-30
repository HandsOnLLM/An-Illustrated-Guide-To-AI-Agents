from dataclasses import dataclass
from typing import Callable

from illustrated_agents.utils import ChapterOverview

# Type hint for the scorers
##  (prediction: str, example: dict) -> bool
Scorer = Callable[[str, dict], bool]


@dataclass
class Benchmark:
    name: str
    examples: list[dict]
    scorer: Callable


class Evaluator:
    """Run a TinyAgent over a Benchmark and aggregate the results."""

    def __init__(self, create_agent: Callable):
        """Initialize with a function that creates a new agent instance."""
        self.create_agent = create_agent

    def run(self, benchmark: Benchmark) -> dict:
        """Run the agent on each example in the benchmark and score the results."""

        # Run each example and collect results
        results = []
        for example in benchmark.examples:
            agent = self.create_agent()
            prediction = agent.run(example["task"]) or ""
            passed = benchmark.scorer(prediction, example)
            results.append(
                {
                    "prediction": prediction,
                    "passed": passed,
                }
            )

        # Aggregate pass rate
        if results:
            pass_rate = sum(result["passed"] for result in results) / len(results)
        else:
            pass_rate = 0.0

        # Return detailed results and overall pass rate
        return {
            "name": benchmark.name,
            "pass_rate": pass_rate,
            "results": results,
        }


what_we_built = ChapterOverview(
    [
        ("agent.py", None, ""),
        (
            "evaluator.py",
            "new",
            "Run a `TinyAgent` over a `Benchmark` suite and score outcomes.",
        ),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", None, ""),
        ("toolbox.py", None, ""),
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)
