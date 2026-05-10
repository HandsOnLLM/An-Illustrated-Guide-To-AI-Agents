import random
import subprocess
import sys
from pathlib import Path
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from illustrated_agents import Skills


# --- Simple Tools ---


def get_weather(location: str) -> str:
    temperature = random.randint(10, 30)
    status = random.choice(["Sunny", "Cloudy", "Rainy"])
    return f"Weather in {location}: {status}, {temperature}℃"


def calculator(a: str, b: str) -> float:
    """Add two numbers."""
    return float(a) + float(b)


def add(a: str, b: str) -> float:
    """Add two numbers."""
    return float(a) + float(b)


def subtract(a: str, b: str) -> float:
    """Subtract two numbers."""
    return float(a) - float(b)


def multiply(a: str, b: str) -> float:
    """Multiply two numbers."""
    return float(a) * float(b)


# --- Code Tools (workspace-scoped) ---


def _build_code_tools(workspace: str = ".") -> dict:
    """Build code tool functions scoped to a workspace. Returns {name: (func, description)}."""
    root = Path(workspace).resolve()

    def _safe_path(path: str) -> Path:
        """Resolve path within workspace, reject traversal."""
        resolved = (root / path).resolve()
        if not str(resolved).startswith(str(root)):
            raise ValueError(f"Path '{path}' is outside the workspace.")
        return resolved

    def read_file(path: str) -> str:
        """Read a file's contents."""
        target = _safe_path(path)
        if not target.exists():
            return f"Error: '{path}' not found."
        return target.read_text(encoding="utf-8")

    def read_lines(path: str, start: str = "1", end: str = "50") -> str:
        """Read specific lines from a file (1-indexed, inclusive)."""
        target = _safe_path(path)
        if not target.exists():
            return f"Error: '{path}' not found."
        start, end = int(start), int(end)
        lines = target.read_text(encoding="utf-8").splitlines()
        selected = lines[max(0, start - 1) : end]
        numbered = [
            f"{i}: {line}" for i, line in enumerate(selected, start=max(1, start))
        ]
        return "\n".join(numbered) or "(empty range)"

    def write_file(path: str, content: str) -> str:
        """Write content to a file."""
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written to '{path}'."

    def list_files(directory: str = ".") -> str:
        """List files in a directory."""
        target = _safe_path(directory)
        if not target.is_dir():
            return f"Error: '{directory}' is not a directory."
        entries = sorted(target.iterdir())
        return (
            "\n".join(p.name + ("/" if p.is_dir() else "") for p in entries)
            or "(empty)"
        )

    def find_files(pattern: str) -> str:
        """Find files matching a glob pattern (e.g., '*.py')."""
        matches = sorted(p for p in root.rglob(pattern) if p.is_file())
        results = [
            str(p.relative_to(root))
            for p in matches
            if str(p.resolve()).startswith(str(root))
        ]
        return "\n".join(results[:30]) or "No files found."

    def search_file(query: str, path: str) -> str:
        """Search for text in a file, returning matching lines."""
        target = _safe_path(path)
        if not target.is_file():
            return f"Error: '{path}' is not a file."
        matches = []
        try:
            for i, line in enumerate(
                target.read_text(encoding="utf-8").splitlines(), 1
            ):
                if query in line:
                    matches.append(f"{i}: {line.strip()}")
                    if len(matches) >= 20:
                        return "\n".join(matches) + "\n(truncated)"
        except (UnicodeDecodeError, PermissionError) as e:
            return f"Error reading '{path}': {e}"
        return "\n".join(matches) or "No matches found."

    def execute_python(code: str) -> str:
        """Execute Python code and return output."""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(root),
            )
            if result.returncode != 0:
                return f"Exit code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}".strip()
            return result.stdout.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30s limit)."

    def show_python(code: str):
        """Print syntax-highlighted Python code."""
        print(highlight(code, PythonLexer(), TerminalFormatter()))
        return "Shown code with syntax highlighting."

    return {
        "read_file": (read_file, "Read a file: read_file(path: str)"),
        "read_lines": (
            read_lines,
            "Read line range: read_lines(path: str, start: int, end: int)",
        ),
        "list_files": (list_files, "List files: list_files(directory: str)"),
        "find_files": (
            find_files,
            "Find files by pattern: find_files(pattern: str)",
        ),
        "search_file": (
            search_file,
            "Search for text in a file: search_file(query: str, path: str)",
        ),
        "write_file": (
            write_file,
            "Write a file: write_file(path: str, content: str)",
        ),
        "execute_python": (
            execute_python,
            "Run Python code: execute_python(code: str)",
        ),
        "show_python": (
            show_python,
            "Display Python code with syntax highlighting: show_python(code: str)",
        ),
    }


def create_native_code_tools(workspace: str = ".") -> Skills:
    """Create coding tools with native function calling (schemas auto-generated)."""
    tools = Skills(requires_approval={"execute_python", "write_file"})
    for name, (func, desc) in _build_code_tools(workspace).items():
        tools.add_tool(name, func, desc)
    return tools
