import json

from typing import Callable

from rich.console import Console
from rich.rule import Rule


from illustrated_agents.chapters.ch2 import Response, Trajectory
from illustrated_agents.chapters.ch5_native import LLM, tool_to_schema
from illustrated_agents.chapters.ch6_skills import Skills
from illustrated_agents.chapters.ch6 import ReAct
from illustrated_agents.chapters.ch9 import Memory

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters import ch6, ch9


console = Console()


class Tools:
    """Tool registry for the Agent."""

    def __init__(self, requires_approval: list[str] = []):
        """Initialize Tools

        Arguments:
            requires_approval: A list of tool names that require human approval
        """
        self.registry = {}
        self.requires_approval = requires_approval

    def add_tool(self, name: str, func: Callable, description: str = ""):
        """Register a tool that the Agent can use.

        Arguments:
            name: The name of the tool.
            func: The function implementing the tool.
            description: A description of the tool.
        """
        self.registry[name] = {"function": func, "description": description}

    @property
    def descriptions(self) -> str:
        """Get descriptions of all registered tools."""
        return "\n".join(f"`{tool}`: {self.registry[tool]['description']}" for tool in self.registry)

    @property
    def prompt(self) -> str:
        return f"""
# Tools

If needed, you can only use the following tools to assist you in completing tasks:

{self.descriptions}

To use a tool, respond with JSON: {{"tool": "name", "kwargs": {{"param": "value"}}}}
"""

    def parse(self, response: Response) -> Response:
        """Parse a JSON tool call from text."""
        text = response.content

        if '"tool":' in text or '"tool:"' in text:
            start, end = text.find("{"), text.rfind("}") + 1
            tool_call = json.loads(text[start:end])

            # Add the parsed tool call to the response
            return Response(
                content=response.content,
                reasoning=response.reasoning,
                tool_call=tool_call,
            )

        return response

    def execute(self, response: Response) -> any:
        """Run a registered tool.

        Arguments:
            tool_call: A parsed tool call dict with "tool" and "kwargs" keys.
        """
        tool_call = response.tool_call
        name, kwargs = tool_call["tool"], tool_call.get("kwargs", {})

        # Human-in-the-loop: ask before running dangerous tools
        if name in self.registry and name in self.requires_approval:
            response = input(f"Allow {name}? [y/N] ").strip().lower()
            if response not in ("y", "yes"):
                return f"Tool '{name}' was denied by the user."

        # Handle registered tools
        if name in self.registry:
            tool_func = self.registry[name]["function"]
            return tool_func(**kwargs)

        return f"Tool '{name}' not found."

    def observation(self, result):
        """Return the observation as a user."""
        return "user", f"OBSERVATION: {result}"

    def is_done(self, response: Response) -> bool:
        """The `TinyAgent` is done when it uses the `final_answer` tool."""
        if response.tool_call and response.tool_call["tool"] == "final_answer":
            response.content = response.tool_call.get("kwargs", "")
            return True
        return False

    @property
    def schemas(self):
        """Used only for native tool-calling."""
        return None


class NativeTools(Tools):
    """Tool registry using native function calling."""

    @property
    def schemas(self) -> list:
        """Return tool functions for native function calling."""
        return [tool_to_schema(tool["function"]) for tool in self.registry.values()]

    @property
    def prompt(self) -> str:
        """Empty because we don't need a prompt for native tool calling"""
        return ""

    def has_tool_call(self, response) -> bool:
        """Check whether the tool call is not empty."""
        return response.tool_call is not None

    def parse_tool_call(self, response) -> dict:
        """Parse a tool call."""
        args = response.tool_call["function"]["arguments"]
        if isinstance(args, str):
            args = json.loads(args)
        return {"tool": response.tool_call["function"]["name"], "kwargs": args}


class Display:
    """Handles agent events with Rich formatting."""

    def __call__(self, event: str, data: str | Response = None) -> None:
        # Animate "thinking"
        if event == "thinking":
            console.print("  [dim]Thinking...[/]")

        # Print THOUGHT
        elif event == "response":
            console.print(f"  [bold dark_orange]{'THOUGHT':<13}[/][dim italic]{data.reasoning}[/]")

            if data.content:
                console.print(f"  [bold cyan]{'ANSWER':<13}[/][dim italic]{data.content}[/]")

        # Print ACTION
        elif event == "tool_call" and data.tool_call:
            tool = data.tool_call["tool"]
            kwargs = data.tool_call["kwargs"]
            console.print(f"  [bold yellow]{'ACTION':<13}[/][yellow]{tool}({kwargs})[/]")

        # Print OBSERVATION
        elif event == "observation":
            console.print(f"  [bold green]{'OBSERVATION':<13}[/]{data}")
            console.print(Rule(style="dim"), end="\n\n")


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(
        self, llm: LLM, memory: Memory, tools: Tools, planner: ReAct, skills: Skills, display=Display
    ):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.skills = skills
        self.display = display

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n"
        system_prompt += self.planner.prompt + "\n"
        system_prompt += self.tools.prompt + "\n"
        system_prompt += self.skills.prompt + "\n"
        self.memory.add("system", system_prompt)

    def run(self, task: str, image_data: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_data=image_data)
        self.trajectory.initialize(task)

        # `Autonomy` loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        response = self.llm.generate(self.memory.get_messages(), tools=self.tools.schemas)
        self.memory.add("assistant", response.content, tool_call=response.tool_call)
        self.display("response", response)

        # Tool parsing
        response = self.tools.parse(response)

        # ANSWER: Stopping mechanism
        if self.tools.is_done(response):
            self.trajectory.add(response)
            return response.content

        return self._execute_action(response)

    def _execute_action(self, response: Response) -> None:
        """Execute a tool action."""

        # ACTION: execute tools
        self.display("tool_call", response)
        result = self.tools.execute(response)

        # OBSERVATION: add tool results to memory and display
        role, observation = self.tools.observation(result)
        self.memory.add(role, observation)
        self.trajectory.add(response, observation)
        self.display("observation", observation)

        return None


def chat(agent):
    """Interactive chat loop — works in both terminal and Jupyter."""
    display = agent.display

    # Agent Overview
    console.print(f"\n  [dim]Tools:[/]  {', '.join(agent.tools.registry.keys())}")
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


what_we_built = ChapterOverview(
    [
        ("agent.py", "updated", "Added printing to the `Display` to see its intermediate steps."),
        (
            "display.py",
            "new",
            "A new `Display` class to format the agent's THOUGHTS, ACTIONS, and OBSERVATIONS.",
        ),
        ("llm.py", None, ""),
        ("memory.py", None, ""),
        ("planning.py", None, ""),
        ("skills.py", None, ""),
        ("toolbox.py", "updated", "Added tools for Coding Agents."),
        ("tools.py", "updated", "Added XML-based tool parsing and calling with human-in-the-loop checks."),
        ("trajectory.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(ch9.TinyAgent, TinyAgent, "ch9.TinyAgent", "ch11.TinyAgent")
tool_diff = DiffViewer(ch6.Tools, Tools, "ch6.Tools", "ch11.Tools")

tools_annotated = CodeAnnotator(
    Tools.execute,
    annotations={
        (11, 14): "When running a tool, if it requires human approval, ask the user before executing it.",
    },
)


display_annotated = CodeAnnotator(
    Display.__call__,
    annotations={
        4: "When the LLM starts generating, show `Thinking...` so the user knows the agent is processing.",
        8: "When a response arrives, stop the spinner and display the extracted <b>THOUGHT</b>.",
        17: "Print intermediate answers as an <b>ACTION</b> and continue the loop.",
        21: "Display the <b>OBSERVATION</b> returned by the tool.",
    },
)
