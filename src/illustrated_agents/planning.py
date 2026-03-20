import re


class ReAct:
    """ReACT module."""

    def __init__(self, max_steps: int = 10):
        """Initialize ReAct module.

        Arguments:
            max_steps: Maximum number of ReAct steps to perform.
        """
        self.max_steps = max_steps

    @property
    def prompt(self) -> str:
        return """
# ReACT (Reason and Act)

You are a ReAct agent that performs exactly ONE step per turn.
Make sure to break down a given task into smaller steps and decide whether to use a tool or provide a final answer.

## ReACT Format

You use the following format for each step:

THOUGHT: [Your reasoning about what to do next]
ACTION:
{
    "tool": "a_tool_name",
    "kwargs": {"param": "value"},
}

An observation will be provided after each action. You do not generate the observation yourself.

## ReACT Completion

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
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            result[key] = match.group(1).strip() if match else ""

        return result["ACTION"]


class XMLReAct(ReAct):
    """ReAct module."""

    @property
    def prompt(self) -> str:
        return """
# ReACT (Reason and Act)

You are a ReAct agent that performs exactly ONE step per turn.
Make sure to break down a given task into smaller steps and decide whether to use a tool or provide a final answer.

## ReACT Format

You use the following format for each step:

THOUGHT: [Your reasoning about what to do next]
ACTION:
<tool>A_TOOL_NAME</tool>
<PARAMETER_NAME>VALUE</PARAMETER_NAME>

Where each parameter gets its own XML tag matching the parameter name.

An observation will be provided after each action. You do not generate the observation yourself.

### Example

THOUGHT: I need to search the web for the current weather in New York.
ACTION:
<tool>search_web</tool>
<query>current weather in New York</query>
<num_results>1</num_results>

## ReACT Completion

To provide the final answer to the task, use the final_answer tool.
It is the only way to complete the task, else you will be stuck on a loop. So your final output should look like this:

ACTION:
<tool>final_answer</tool>
<answer>insert your final answer here</answer>

Use the `final_answer` tool when you are completely done with all subtasks and have the final answer ready.
You can also use `final_answer` to directly reply to a user's question without using any tools if you think you can answer it directly.
"""
