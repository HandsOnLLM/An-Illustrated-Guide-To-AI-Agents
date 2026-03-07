"""Interactive CLI for TinyAgent using Rich."""

import argparse
import os

from dotenv import load_dotenv
from pathlib import Path
from rich.console import Console
from rich.table import Table

import illustrated_agents
from illustrated_agents import LLM, Memory, Tools, ReAct, Reflector, Skills, TinyAgent
from illustrated_agents.display import label, Display, LOGO, FLAMINGO_LOGO

load_dotenv()
console = Console()


# --- Demo tools ---


def calculator(a: str, b: str) -> float:
    return float(a) + float(b)


def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72F"


# --- Slash commands ---

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
        table = Table(show_header=False, box=None, padding=(0, 2))
        for name, desc in COMMANDS.items():
            table.add_row(f"[bold]{name}[/]", f"[dim]{desc}[/]")
        console.print(table)

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
            content = msg["content"] if isinstance(msg["content"], str) else "[multimodal]"
            style = "blue" if role == "user" else "green" if role == "assistant" else "dim"
            console.print(f"     [{style}]{i}: {role}: {content}[/]")

    # `/model` command shows current model name
    elif cmd == "/model":
        console.print(f"  [dim]{agent.llm.model}[/]")

    # `/tools` command lists available tools with descriptions
    elif cmd == "/tools":
        for name, tool in agent.tools.tools.items():
            console.print(f"  [yellow]{name}[/] - [dim]{tool['description']}[/]")

    # `/skills` command lists available skills with descriptions
    elif cmd == "/skills":
        for name, skill in agent.skills.skills.items():
            console.print(f"  [magenta]{name}[/] - [dim]{skill['description']}[/]")

    # Unknown command
    else:
        console.print(f"  [red]Unknown command: {cmd}[/] (type [bold]/help[/] for commands)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pink", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    model = os.getenv("MODEL", "ollama/gemma3:12b")
    display = Display(pink=args.pink)

    # Tools
    tools = Tools()
    tools.add_tool("calculator", calculator, "Adds two numbers: calculator(a: str, b: str)")
    tools.add_tool("get_weather", get_weather, "Gets weather: get_weather(location: str)")

    # Skills
    skills = Skills()
    file_analyzer_path = Path(illustrated_agents.__file__).parent / "skills" / "file_analyzer" / "SKILL.md"
    skills.load_from_file(file_analyzer_path)

    # Agent
    agent = TinyAgent(
        llm=LLM(model=model),
        memory=Memory(),
        tools=tools,
        planner=ReAct(max_steps=10),
        reflector=Reflector(interval=20),
        skills=skills,
        display=display,
    )

    # Display welcome message with model, tools, and skills
    tool_names = ", ".join(tools.tools.keys())
    skill_names = ", ".join(skills.skills.keys())
    console.print(FLAMINGO_LOGO if args.pink else LOGO)
    console.print(f"\n  [dim]Model:[/]  {model}")
    console.print(f"  [dim]Tools:[/]  {tool_names}")
    console.print(f"  [dim]Skills:[/] {skill_names}")
    console.print("  [dim]Type[/] /help [dim]for commands.[/]\n")

    while True:
        # User input
        try:
            w = console.width
            print(f"\033[48;5;237m \033[36m\u258e\033[97;1m >  {' ' * (w - 6)}\033[{w - 6}D", end="", flush=True)
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
            display._stop_thinking()
            console.print(f"\n  :flamingo: [bold magenta]ANSWER[/]    {result}\n" if args.pink else f"\n  :dolphin: [bold cyan]ANSWER[/]    {result}\n")
        except Exception as e:
            display._stop_thinking()
            console.print(f"  {label('ERROR', 'red')}[red]{e}[/]\n")


if __name__ == "__main__":
    main()
