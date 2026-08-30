import subprocess
import sys
from pathlib import Path


from illustrated_agents.chapters import ch9
from illustrated_agents.chapters.ch2 import LLM, Response, Trajectory
from illustrated_agents.chapters.ch4 import Memory
from illustrated_agents.chapters.ch5 import Tools, NativeTools
from illustrated_agents.chapters.ch6 import ReAct, NativeReAct

from illustrated_agents.utils import CodeAnnotator, DiffViewer, ChapterOverview


BOLD = "\033[1m"
RESET = "\033[0m"
GREEN = "\033[32m"  # THOUGHT
RED = "\033[31m"  # ACTION
YELLOW = "\033[33m"  # OBSERVATION
PURPLE = "\033[35m"  # ANSWER


def read_file(path: str) -> str:
    """Read a file's contents."""
    target = Path(path)
    if not target.exists():
        return f"Error: '{path}' not found."
    return target.read_text(encoding="utf-8")


def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    target = Path(directory)
    if not target.is_dir():
        return f"Error: '{directory}' is not a directory."
    entries = sorted(target.iterdir())
    return (
        "\n".join(p.name + ("/" if p.is_dir() else "") for p in entries)
        or "(empty)"
    )


def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written to '{path}'."


def execute_python(code: str) -> str:
    """Execute Python code and return output."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30s limit)."

    if result.returncode != 0:
        return (
            f"Exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        ).strip()
    return result.stdout.strip() or "(no output)"


class Display:
    """Chat interface with styling."""

    def __call__(self, event: str, data: str | Response = None) -> None:

        # "Thinking" line
        if event == "thinking":
            print(f"  Thinking...\n{RESET}")

        # THOUGHT
        elif event == "response":
            print(f"{BOLD}{GREEN}{'▒▒ THOUGHT ▒▒':<13}{RESET}")
            print(f"{data.reasoning}{RESET}\n")

            # ANSWER
            if data.content:
                print(f"{BOLD}{PURPLE}{'▒▒ ANSWER ▒▒':<13}{RESET}")
                print(f"{data.content}{RESET}\n")

        # ACTION
        elif event == "tool_call" and data:
            tool = data.tool_call["tool"]
            kwargs = data.tool_call["kwargs"]
            print(f"{BOLD}{RED}{'▒▒ ACTION ▒▒':<13}{RESET}")
            print(f"{tool}({kwargs}){RESET}\n")

        # OBSERVATION
        elif event == "observation":
            print(f"{BOLD}{YELLOW}{'▒▒ OBSERVATION ▒▒':<13}{RESET}")
            print(f"{data}{RESET}\n")
            print(f"{'─' * 40}STEP{'─' * 40}{RESET}\n")


class TinyAgent:
    """A minimal, modular, and educational agent framework."""

    def __init__(
        self,
        llm: LLM,
        memory: Memory,
        tools: Tools,
        planner: ReAct,
        display: Display,
    ):
        self.llm = llm
        self.memory = memory
        self.tools = tools
        self.planner = planner
        self.display = display

        self.trajectory = Trajectory()

        # Build system prompt with all components
        system_prompt = "You are a helpful assistant.\n\n"
        system_prompt += self.planner.prompt
        system_prompt += self.tools.prompt
        self.memory.add("system", system_prompt)

    def run(self, task: str, image_data: str = None) -> str:
        """Run the agent on a task."""
        self.memory.add("user", task, image_data=image_data)
        self.trajectory.initialize(task)

        # *Autonomy* loop
        for step in range(self.planner.max_steps):
            result = self._step()
            if result is not None:
                return result

        return "Max steps reached without completion."

    def _step(self) -> str | None:
        """Perform a single step."""
        # THOUGHT: Generate response and add to memory
        self.display("thinking")
        response = self.llm.generate(
            self.memory.get_messages(), tools=self.tools.schemas
        )
        self.memory.add(
            "assistant", response.content, tool_call=response.tool_call
        )
        self.display("response", response)

        # Tool parsing
        response = self.planner.parse(response)
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


NAME = """
██████ ██ ███  ██ ██  ██   ▄████▄  ▄████  ██████ ███  ██ ██████
  ██   ██ ██ ▀▄██  ▀██▀    ██▄▄██ ██  ▄▄▄ ██▄▄   ██ ▀▄██   ██
  ██   ██ ██   ██   ██     ██  ██  ▀███▀  ██▄▄▄▄ ██   ██   ██
"""  # ANSI Compact


def main():
    import shutil

    # TinyAgent
    tools = NativeTools(requires_approval=["write_file", "execute_python"])
    tools.add_tool("read_file", read_file)
    tools.add_tool("list_files", list_files)
    tools.add_tool("write_file", write_file)
    tools.add_tool("execute_python", execute_python)
    agent = TinyAgent(
        llm=LLM(model="gemma4:e4b", think=True),
        memory=Memory(),
        tools=tools,
        planner=NativeReAct(),
        display=Display(),
    )

    print(f"\n{NAME}\n")

    while True:
        try:
            w = shutil.get_terminal_size().columns
            print(
                f"\033[48;5;237m \033[36m▎\033[97;1m >  {' ' * (w - 6)}\033[{w - 6}D",
                end="",
                flush=True,
            )
            query = input().strip()
            print("\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\033[0m", end="")
            break
        if not query or query.lower() in ("exit", "quit"):
            break
        try:
            agent.run(query)
        except Exception as e:
            print(f"ERROR: {e}\n")


what_we_built = ChapterOverview(
    [
        (
            "agent.py",
            "updated",
            "Add the Display to your TinyAgent.",
        ),
        ("cli.py", "new", "Use the new TinyAgent with Display in the CLI."),
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
        ("tools.py", None, ""),
        ("trajectory.py", None, ""),
    ]
)


tinyagents_diff = DiffViewer(
    ch9.TinyAgent, TinyAgent, "ch9.TinyAgent", "ch10.TinyAgent"
)


display_annotated = CodeAnnotator(
    Display.__call__,
    annotations={
        5: "When the LLM starts generating, show `Thinking...` so the user knows the agent is processing.",
        9: "When a response arrives, stop the spinner and display the extracted <b>THOUGHT</b>.",
        21: "Print intermediate answers as an <b>ACTION</b> and continue the loop.",
        26: "Display the <b>OBSERVATION</b> returned by the tool.",
    },
)

if __name__ == "__main__":
    main()
