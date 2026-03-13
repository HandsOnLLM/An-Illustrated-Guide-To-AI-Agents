"""TinyAgent display handler using Rich for formatted console output."""

import random
import re
import time
import threading

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.rule import Rule

console = Console()

NAME = """
██████ ██ ███  ██ ██  ██   ▄████▄  ▄████  ██████ ███  ██ ██████ 
  ██   ██ ██ ▀▄██  ▀██▀    ██▄▄██ ██  ▄▄▄ ██▄▄   ██ ▀▄██   ██   
  ██   ██ ██   ██   ██     ██  ██  ▀███▀  ██▄▄▄▄ ██   ██   ██    
"""  # ANSI Compact
# Dolphin color palette
_DK = "#3a5068"  # dark (back, fin, tail)
_DM = "#6a8498"  # medium (body transition, head)
_DL = "#a0b8c8"  # light (belly, snout)

LOGO = f"""
[bold {_DK}]                     ▓▓[/]
[bold {_DK}]                       ▓▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒[/]
[bold {_DL}]                   ▒▒▒▒▒▒[/][bold {_DK}]▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒▒▒▒▒[/]
[bold {_DL}]                ▒▒▒▒▒▒▒▒▒▒[/][bold {_DK}]▓▓▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒▒▒▒▒[/]
[bold {_DL}]             ▒▒▒▒▒▒▒▒▒▒▒▒▒[/][bold {_DK}]▓▓██▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒▒▒▒▓[/]
[bold {_DL}]           ▒▒▒▒▒▒▒▒▒▒▒▒▒[/][bold {_DK}]▓███████▓[/][bold {_DM}]▒▒▒▓▓▓▓▓▓▒▒▓▒[/]
[bold {_DL}]          ▒▒▒▒▒▒▒▒▒[/][bold {_DK}]▓▓▓█████████▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒▓▓▒▒▓▓[/]
[bold {_DL}]         ▒▒▒▒▒▒[/][bold {_DK}]▓▓▓█████████████▓▓▓▓▓▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▒▓▓[/]
[bold {_DL}]       ▒▒▒▒▒▒[/][bold {_DK}]▓███████████████████▓▓▓▓▓▓[/][bold {_DM}]▒▒▒▒▒▒▒▒▓[/]
[bold {_DL}]      ▒▒▒▒▒[/][bold {_DK}]▓███████████████████████▓▓▓▓▓[/][bold {_DM}]▒▒▒▒▒▒▒▓▓[/]
[bold {_DL}]     ▒▒▒▒[/][bold {_DK}]▓▓███████▓▓▓▓▓▓▓ █████▓[/][bold {_DM}]▒▒      ▓▓▓▒▒▒▒▒[/]
[bold {_DL}]     ▒▒▒[/][bold {_DK}]▓██████▓▓▓       ▓███▓[/][bold {_DM}]▒▒           ▓▓▒▒▒▒[/]
[bold {_DL}]     ▒▒[/][bold {_DK}]▓████▓▓▓        ▓██▓▓[/][bold {_DM}]▒▒                ▓▒[/]
[bold {_DL}]    ▒[/][bold {_DK}]▓▓████▓▓        ▓▓▓▓[/]
[bold {_DK}]    ▓▓████▓[/]
[bold {_DK}]    ▓████▓[/]
[bold {_DK}]   ▓▓███▓[/]
[bold {_DK}]▓██▓███▓[/]
[bold {_DK}]▓▓▓███▓[/]
[bold {_DK}]  ▓▓██▓▓[/]
[bold {_DK}]    ▓▓▓▓▒[/]
[bold {_DK}]      ▓▓▓▒[/]
[bold {_DK}]       ▓▓▒[/]
[bold {_DK}]        ▓▓[/]
[bold {_DK}]         ▓[/]
{NAME}"""  # https://www.asciiart.eu/image-to-ascii -- Book Cover -- Manually edited

# Flamingo color palette
_FH = "#f5c4bc"  # head
_FN = "#f0b0a8"  # neck
_FD = "#e8a098"  # lower neck
_FB = "#d4a090"  # beak base
_FK = "#424242"  # beak tip
_FE = "#000000"  # eye

FLAMINGO_LOGO = f"""
      [bold {_FH}]            ░░░░░░░░░░[/]
      [bold {_FH}]         ▒▒░░░░░░░░░░░░░[/]
      [bold {_FH}]        ▒▒▒▒▒▒▒▒░▒▒░░░░░░[/]
      [bold {_FH}]      ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░[/]
      [bold {_FH}]      ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒[/][bold {_FE}]██[/][bold {_FH}]▒▒▒[/]
      [bold {_FN}]     ▒▒▒▒▒▒[/][bold {_FB}]▓▓▓▓[/][bold {_FN}]▒▒▒▒▒▒▒▒▒▒▒▒[/]
      [bold {_FN}]    ▒▒▒▒▒▒▒[/][bold {_FB}]▓▓▓▓▓▓[/][bold {_FN}]▒▒▒▒▒▒▒░░░[/]
      [bold {_FN}]    ▒▒▒▒▒▒▒▒   [/][bold {_FB}]▓▓▓▓[/][bold {_FN}]▒▒▒▒▒▒▒░░[/]
      [bold {_FN}]    ▒▒▒▒▒▒▒▒      [/][bold {_FK}]▓▓▓▓[/][bold {_FN}]▒▒▒▒▒▒░[/]
      [bold {_FD}]    ▒▒▒▒▒▒▒▒          [/][bold {_FK}]▓▒▒▓██▓▓[/]
      [bold {_FD}]    ▒▒▒▒▒▒▒░░          [/][bold {_FK}]███████[/]
      [bold {_FD}]    ▒▒▒▒▒▒▒░░░░        [/][bold {_FK}]██████[/]
      [bold {_FD}]    ▓▓▒▒▒▒▒▒▒░░░░      [/][bold {_FK}]██████[/]
      [bold {_FD}]      ▓▒▒▒▒▒▒▒▒░░░░░   [/][bold {_FK}]█████[/]
      [bold {_FD}]       ▓▓▒▒▒▒▒▒▒▒▒░░░░ [/][bold {_FK}]████[/]
      [bold {_FD}]         ▓▓▒▒▒▒▒▒▒▒▒▒▒▒[/][bold {_FK}]██[/]
      [bold {_FD}]           ▓▓▒▒▒▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]             ▓▓▒▒▒▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]              ▓▓▓▒▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]               ▓▓▓▒▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]                ▓▓▓▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]                ▓▓▓▒▒▒▒▒▒▒▒▒[/]
      [bold {_FD}]                ▓▓▓▒▒▒▒▒▓▓▓▓[/]
{NAME}"""  # https://www.asciiart.eu/image-to-ascii -- Flamingo in Ch12 -- Manually edited


def label(name: str, style: str) -> str:
    """Format a fixed-width label for step output."""
    return f"[bold {style}]{name:<13}[/]"


# --- Display handler ---

THINKING_FRAMES = [
    "        ",
    " ~      ",
    " ~~     ",
    "~~~    ",
    "~~ ~~  ",
    "~  ~~ ~",
    "   ~~~ ",
    "     ~~",
    "        ",
]

THINKING_MESSAGES = [
    "Sonar pinging...",
    "Echolocating...",
    "Diving deep...",
    "Surfacing...",
    "Riding the current...",
    "Making a splash...",
    "Doing flips...",
    "Chasing fish...",
    "Blowing bubbles...",
    "Somersaulting...",
    "Fishing for answers...",
    "Navigating the depths...",
    "Scanning the ocean floor...",
    "Making waves...",
    "Deep dive...",
]

FLAMINGO_THINKING_MESSAGES = [
    "Standing on one leg...",
    "Preening feathers...",
    "Wading through data...",
    "Turning pink...",
    "Flocking together...",
    "Filter feeding...",
    "Stretching wings...",
    "Balancing act...",
    "Ruffling feathers...",
    "Doing the flamingo dance...",
    "Looking fabulous...",
    "Strutting around...",
    "Dipping beak...",
]


class Display:
    """Handles agent events with Rich formatting."""

    def __init__(self, pink=False):
        self._live = None
        self._animating = False
        self._pink = pink

    def __call__(self, event: str, data: str | dict = None) -> None:
        # Animate "thinking"
        if event == "thinking":
            self._animating = True
            self._live = Live(console=console, refresh_per_second=8, transient=True)
            self._live.start()
            self._thinking_msg = random.choice(FLAMINGO_THINKING_MESSAGES if self._pink else THINKING_MESSAGES)
            threading.Thread(target=self._animate_thinking, daemon=True).start()

        # Print THOUGHT
        elif event == "response":
            self._stop_thinking()
            thought = self._extract_thought(data)
            if thought:
                console.print(f"  {label('THOUGHT', 'dark_orange')}[dim italic]{thought}[/]\n")

        # Print ACTION
        elif event == "tool_call" and data:
            tool = data.get("tool")
            if tool != "final_answer":
                args = data.get("kwargs", {})
                args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                console.print(f"  {label('ACTION', 'yellow')}[yellow]{tool}({args_str})[/]")

        # Print OBSERVATION
        elif event == "observation":
            trimmed_observation = data[:250] + "\n[TRUNCATED]" if len(data) > 250 else data
            console.print(f"  {label('OBSERVATION', 'green')}{trimmed_observation}\n")
            console.print(Rule(style="dim"), end="\n\n")

    def _animate_thinking(self) -> None:
        """A wave animation."""
        i = 0
        while self._animating and self._live:
            frame = THINKING_FRAMES[i % len(THINKING_FRAMES)]
            self._live.update(Text(f"  {self._thinking_msg}  {frame}", style="dark_orange"))
            time.sleep(0.15)
            i += 1

    def _extract_thought(self, text: str) -> str | None:
        """Extract the thought from the agent's response."""
        match = re.search(r"THOUGHT:\s*(.+?)(?=ACTION:|$)", text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _stop_thinking(self) -> None:
        """Stop the thinking animation."""
        self._animating = False
        if self._live:
            self._live.stop()
            self._live = None
