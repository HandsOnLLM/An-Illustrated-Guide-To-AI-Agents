import re


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
Make sure to break down a given task into smaller steps and decide whether to use a tool or provide a final answer.

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
It is the only way to complete the task, else you will be stuck on a loop. So your final output should look like this:

ACTION:
{
    "tool": "final_answer",
    "kwargs": "insert your final answer here"
}

Use the `final_answer` tool when you are completely done with all subtasks and have the final answer ready.
You can also use `final_answer` to directly reply to a user's question without using any tools if you think you can answer it directly.
"""

    def parse(self, text: str) -> dict:
        """Parse a ReAct formatted response into THOUGHT and ACTION."""

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

        return result["ACTION"]


class XMLReAct(ReAct):
    """ReAct module."""

    @property
    def prompt(self) -> str:
        return """
# ReAct (Reason and Act)

You are a ReAct agent that performs exactly ONE step per turn.
That step always contains a THOUGHT followed by an ACTION (XML formatted).

## ReAct Format

You use the following format for each step:

THOUGHT: [Your reasoning about what to do next]
ACTION: (see example below for XML format)

An OBSERVATION will be provided after each action. You do not generate the OBSERVATION yourself.

### Example

One round of THOUGHT and ACTION could look like this:

THOUGHT: I need to find the installation instructions in the README to answer the user's question.
ACTION:
<tool>search_file</tool>
<query>pip install</query>
<path>README.md</path>

## Answering and Completion

To provide the final answer to the task or to answer a question directly, use the ACTION like so:

THOUGHT: The answer to the user's question is found in the README, so I will provide it directly without using any tools.
ACTION:
<tool>final_answer</tool>
<answer>You can install the package using the following command: 
`pip install illustrated_agents`.
</answer>

Use this when you are completely done with all subtasks and have the final answer ready.
You can also use this to directly reply to a user's question without using any tools if you think you can answer it directly.
"""
