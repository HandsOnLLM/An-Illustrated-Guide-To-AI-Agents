import re
from rich.console import Console
from rich.rule import Rule

from illustrated_agents import LLM, Memory, Tools, ReAct, Reflector, Skills
from illustrated_agents.utils import CodeAnnotator, DiffViewer
from illustrated_agents.chapters import ch9

console = Console()


class XMLReAct(ReAct):
    """ReACT module."""

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
<tool>a_tool_name</tool>
<param_name>value</param_name>

An observation will be provided after each action. You do not generate the observation yourself.

## ReACT Completion

To provide the final answer to the task, use the final_answer tool.
It is the only way to complete the task, else you will be stuck on a loop. So your final output should look like this:

ACTION:
<tool>final_answer</tool>
<answer>insert your final answer here</answer>

Use the `final_answer` tool when you are completely done with all subtasks and have the final answer ready.
You can also use `final_answer` to directly reply to a user's question without using any tools if you think you can answer it directly.
"""


class XMLTools(Tools):
    """Tool registry for the Agent."""

    @property
    def prompt(self):
        return f"""
# Tools

If needed, you can only use the following tools to assist you in completing tasks:

{self.descriptions}

To use a tool, respond with XML tags:
<tool>tool_name</tool>
<param_name>value</param_name>
"""

    def has_tool_call(self, text: str) -> bool:
        return "<tool>" in text

    def parse_tool_call(self, text: str) -> dict:
        """Parse an XML tool call from text."""
        # Extract the tool name
        tool = re.search(r"<tool>(.*?)</tool>", text, re.DOTALL).group(1).strip()

        # Extract parameters as kwargs
        kwargs = {}
        for match in re.finditer(r"<(\w+)>(.*?)</\1>", text, re.DOTALL):
            name, value = match.group(1), match.group(2).strip()
            if name != "tool":
                kwargs[name] = value

        return {"tool": tool, "kwargs": kwargs}


class Display:
    """Formats agent events for the terminal."""

    def __init__(self):
        self._status = None

    def __call__(self, event, data=None):

        # Animate thinking
        if event == "thinking":
            self._status = console.status("Thinking...", spinner="dots")
            self._status.start()

        # Print THOUGHT
        elif event == "response":
            self.stop()
            thought = re.search(r"THOUGHT:\s*(.+?)(?=ACTION:|$)", data, re.IGNORECASE | re.DOTALL).group(1).strip()
            console.print(f"  [bold dark_orange]{'THOUGHT':<13}[/][dim italic]{thought}[/]\n")

        # Print ACTION
        elif event == "tool_call" and data:
            tool = data.get("tool")
            if tool != "final_answer":
                args = ", ".join(f"{k}={v!r}" for k, v in data.get("kwargs", {}).items())
                console.print(f"  [bold yellow]{'ACTION':<13}[/][yellow]{tool}({args})[/]")

        # Print OBSERVATION
        elif event == "observation":
            console.print(f"  [bold green]{'OBSERVATION':<13}[/]{data}\n")
            console.print(Rule(style="dim"), end="\n\n")

    def stop(self):
        if self._status:
            self._status.stop()
            self._status = None


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, reflector: Reflector, skills: Skills, display=Display):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.reflector = reflector
        self.skills = skills
        self.display = display

        # Build system prompt with all components
        system_prompt = "You are a helpful AI agent.\n\n"
        system_prompt += self.planner.prompt + "\n\n"
        system_prompt += self.tools.prompt
        system_prompt += self.skills.prompt
        self.memory.add("user", system_prompt)

    def run(self, task: str, image_url: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_url=image_url)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            # Reflection step before taking the next action
            if self.reflector.should_reflect(step):
                self.memory.add("user", self.reflector.prompt)

            # Perform a step and check for completion
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # Generate response and add to memory
        self.display("thinking")
        response = self.llm.generate(self.memory.get_messages())
        self.display("response", response)
        self.memory.add("assistant", response)

        # Parse planner's response to extract action if needed
        response = self.planner.parse(response)

        # Tool parsing and execution
        if self.tools.has_tool_call(response):
            return self._execute_action(response)

        return None

    def _execute_action(self, action: str) -> str | None:
        """Execute a tool action."""
        tool_call = self.tools.parse_tool_call(action)
        self.display("tool_call", tool_call)

        # Final answer ends the loop
        if tool_call["tool"] == "final_answer":
            return tool_call["kwargs"]["answer"]

        # Activate skill and extract the observation
        if tool_call["tool"] == "use_skill":
            observation = self.skills.activate(tool_call)

        # Execute tool and extract the observation
        else:
            observation = self.tools.run_tool(tool_call)

        # Format the observation and add it to memory
        self.display("observation", observation)
        obs_prompt = f"OBSERVATION: {action} -> {observation}"
        self.memory.add("user", obs_prompt)

        return None


def chat(agent):
    """Interactive chat loop — works in both terminal and Jupyter."""
    display = agent.display

    # Agent Overview
    console.print(f"\n  [dim]Tools:[/]  {', '.join(agent.tools.tools.keys())}")
    console.print("  [dim]Type[/] exit [dim]to quit.[/]\n")

    while True:
        # User input
        try:
            query = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("  [dim]Goodbye![/]")
            break

        # Skip empty input
        if not query:
            continue

        console.print(f"  [bold]> [/]{query}\n")

        # Exit commands
        if query.lower() in ("exit", "quit"):
            console.print("  [dim]Goodbye![/]")
            break

        # Run agent
        try:
            result = agent.run(query)
            display.stop()
            console.print(f"\n  [bold cyan]{'ANSWER':<13}[/]{result}\n")
        except Exception as e:
            display.stop()
            console.print(f"  [bold red]{'ERROR':<13}[/][red]{e}[/]\n")


tinyagents_diff = DiffViewer(ch9.TinyAgent, TinyAgent, "ch9.TinyAgent", "ch11.TinyAgent")
react_diff = DiffViewer(ReAct.prompt, XMLReAct.prompt, "ReAct", "XMLReAct")
tools_diff = DiffViewer(Tools.prompt, XMLTools.prompt, "Tools", "XMLTools")


tools_annotated = CodeAnnotator(
    XMLTools,
    annotations={
        (13, 15): "The prompt now instructs the agent to use XML tags to call tools instead of JSON.",
        19: "We now search for <tool> tags instead of JSON tool calls.",
        24: "Since there will be only a single tool call per response, we can simplify the parsing logic to just look for the first <tool> tag.",
        (27, 31): "There might be multiple keyword arguments (kwargs) in the tool call that need to be extracted.",
    },
)


display_annotated = CodeAnnotator(
    Display.__call__,
    annotations={
        (5, 6): "When the LLM starts generating, show a spinner.",
        (10, 12): "When a response arrives, stop the spinner and display the extracted <b>THOUGHT</b>.",
        18: "Print intermediate answers as an <b>ACTION</b> and continue the loop.",
        (20, 21): "Format tool calls as <b>ACTION</b>.",
        (25, 26): "Display the <b>OBSERVATION</b> returned by the tool.",
    },
)
