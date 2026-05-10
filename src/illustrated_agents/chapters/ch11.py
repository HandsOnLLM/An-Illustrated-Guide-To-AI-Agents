from rich.console import Console
from rich.rule import Rule


from illustrated_agents.chapters.ch2 import LLM, Response, Trajectory
from illustrated_agents.chapters.ch4 import Memory
from illustrated_agents.chapters.ch5 import Tools
from illustrated_agents.chapters.ch6 import ReAct

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview
from illustrated_agents.chapters import ch9


console = Console()


class Display:
    """Handles agent events with Rich formatting."""

    def __call__(self, event: str, data: str | Response = None) -> None:
        # Animate "thinking"
        if event == "thinking":
            console.print("  [dim]Thinking...[/]")

        # Print THOUGHT
        elif event == "response":
            console.print(
                f"  [bold dark_orange]{'THOUGHT':<13}[/][dim italic]{data.reasoning}[/]"
            )

            if data.content:
                console.print(
                    f"  [bold cyan]{'ANSWER':<13}[/][dim italic]{data.content}[/]"
                )

        # Print ACTION
        elif event == "tool_call" and data.tool_call:
            tool = data.tool_call["tool"]
            kwargs = data.tool_call["kwargs"]
            console.print(
                f"  [bold yellow]{'ACTION':<13}[/][yellow]{tool}({kwargs})[/]"
            )

        # Print OBSERVATION
        elif event == "observation":
            console.print(f"  [bold green]{'OBSERVATION':<13}[/]{data}")
            console.print(Rule(style="dim"), end="\n\n")


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(
        self,
        llm: LLM,
        memory: Memory,
        tools: Tools,
        planner: ReAct,
        display=Display,
    ):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.display = display

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n"
        system_prompt += self.planner.prompt + "\n"
        system_prompt += self.tools.prompt + "\n"
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
        response = self.llm.generate(
            self.memory.get_messages(), tools=self.tools.schemas
        )
        self.memory.add(
            "assistant", response.content, tool_call=response.tool_call
        )
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
        (
            "agent.py",
            "updated",
            "Added printing to the `Display` to see its intermediate steps.",
        ),
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
        (
            "tools.py",
            "updated",
            "Added XML-based tool parsing and calling with human-in-the-loop checks.",
        ),
        ("trajectory.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(
    ch9.TinyAgent, TinyAgent, "ch9.TinyAgent", "ch11.TinyAgent"
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
