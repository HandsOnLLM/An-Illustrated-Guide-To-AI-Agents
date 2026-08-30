import argparse
import re


# --- Detect rich; fall back to a plain console if missing ---

try:
    from rich.console import Console
    from rich.table import Table

    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Table = None

    class _PlainConsole:
        """Minimal rich.Console stand-in that strips markup."""

        _MARKUP = re.compile(r"\[/?[^\]]*\]")

        def print(self, *args, end="\n"):
            for arg in args:
                if isinstance(arg, str):
                    print(self._MARKUP.sub("", arg), end=end)
                # Non-strings (Rule, Table) are silently skipped

        @property
        def width(self):
            import shutil

            return shutil.get_terminal_size().columns

    console = _PlainConsole()


from illustrated_agents import LLM, TinyAgent, NativeReAct
from illustrated_agents.memory import MultimodalMemory
from illustrated_agents.display import (
    label,
    Display,
    RichDisplay,
    LOGO,
    FLAMINGO_LOGO,
)
from illustrated_agents.toolbox import create_native_code_tools


COMMANDS = {
    "/help": "Show available commands",
    "/clear": "Clear conversation memory (keeps system prompt)",
    "/memory": "Show current conversation memory",
    "/model": "Show current model name",
    "/tools": "List available tools",
    "/skills": "List available skills",
}


def handle_command(cmd, agent):
    """Handle a slash command."""
    cmd = cmd.strip().lower()

    # `/help` command lists available commands
    if cmd == "/help":
        if HAS_RICH:
            table = Table(show_header=False, box=None, padding=(0, 2))
            for name, desc in COMMANDS.items():
                table.add_row(f"[bold]{name}[/]", f"[dim]{desc}[/]")
            console.print(table)
        else:
            for name, desc in COMMANDS.items():
                console.print(f"  {name:<12}  {desc}")

    # `/clear` command clears memory except system prompt
    elif cmd == "/clear":
        agent.memory.messages = agent.memory.messages[:1]
        console.print("  [dim]Memory cleared (system prompt kept).[/]")

    # `/memory` command shows current conversation memory
    elif cmd == "/memory":
        messages = agent.memory.get_messages()
        console.print(f"  [dim]{len(messages)} message(s) in memory:[/]")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content = (
                msg["content"]
                if isinstance(msg["content"], str)
                else "[multimodal]"
            )
            style = (
                "blue"
                if role == "user"
                else "green"
                if role == "assistant"
                else "dim"
            )
            console.print(f"     [{style}]{i}: {role}: {content}[/]")

    # `/model` command shows current model name
    elif cmd == "/model":
        console.print(f"  [dim]{agent.llm.model}[/]")

    # `/tools` command lists available tools with descriptions
    elif cmd == "/tools":
        for name, tool in agent.tools.registry.items():
            console.print(f"  [yellow]{name}[/] - [dim]{tool['description']}[/]")

    # `/skills` command lists available skills with descriptions
    elif cmd == "/skills":
        for name, skill in agent.skills.skills.items():
            console.print(
                f"  [magenta]{name}[/] - [dim]{skill['description']}[/]"
            )

    # Unknown command
    else:
        console.print(
            f"  [red]Unknown command: {cmd}[/] (type [bold]/help[/] for commands)"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--pink", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="LLM model name",
        default="gemma4:e4b",
    )
    parser.add_argument(
        "-ab",
        "--api_base",
        type=str,
        help="API base URL",
        default="http://localhost:11434/v1",
    )
    parser.add_argument(
        "-ak", "--api_key", type=str, help="API key", default="no_key"
    )
    args = parser.parse_args()

    # Display: rich-based if available, otherwise pure-Python ANSI
    display = (RichDisplay if HAS_RICH else Display)(pink=args.pink)

    # LLM
    llm = LLM(
        model=args.model,
        base_url=args.api_base,
        api_key=args.api_key,
        think=True,
    )

    # Tools and Skills
    tools = create_native_code_tools()

    # ReAct planner with native reasoning and tool calling (no text parsing needed)
    planner = NativeReAct(max_steps=10)

    # Coding Agent
    agent = TinyAgent(
        llm=llm,
        memory=MultimodalMemory(),
        tools=tools,
        planner=planner,
        display=display,
    )

    # Display welcome message with model, tools, and skills
    tool_names = ", ".join(agent.tools.registry.keys())
    console.print(FLAMINGO_LOGO if args.pink else LOGO)
    console.print(f"\n  [dim]Model:[/]  {args.model}")
    console.print(f"  [dim]Tools:[/]  {tool_names}")
    console.print("  [dim]Type[/] /help [dim]for commands.[/]\n")

    while True:
        # User input
        try:
            w = console.width
            print(
                f"\033[48;5;237m \033[36m▎\033[97;1m >  {' ' * (w - 6)}\033[{w - 6}D",
                end="",
                flush=True,
            )
            query = input().strip()
            print("\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\033[0m", end="")
            console.print("  [dim]Goodbye![/]")
            break

        # Skip empty input
        if not query:
            continue

        # Exit commands
        if query.lower() in ("exit", "quit"):
            console.print("  [dim]Goodbye![/]")
            break

        # Slash commands
        if query.startswith("/"):
            handle_command(query, agent)
            console.print()
            continue

        # Run agent
        try:
            result = agent.run(query)
            if hasattr(display, "_stop_thinking"):
                display._stop_thinking()
        except Exception as e:
            if hasattr(display, "_stop_thinking"):
                display._stop_thinking()
            if HAS_RICH:
                console.print(f"  {label('ERROR', 'red')}[red]{e}[/]\n")
            else:
                console.print(f"  ERROR    {e}\n")


if __name__ == "__main__":
    main()
