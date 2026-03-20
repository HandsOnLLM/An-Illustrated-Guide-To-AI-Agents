"""A collection of tools for TinyAgent.

Simple tools are plain functions that can be registered directly.
Code tools require a workspace for filesystem safety.
"""

import subprocess
import sys
from pathlib import Path

from illustrated_agents.chapters.ch11 import XMLTools


# --- Simple Tools ---


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


def get_weather(location: str) -> str:
    """Get weather for a location (mock)."""
    return f"Weather in {location}: Sunny, 72°F"


# --- Code Tools (workspace-scoped) ---


def create_code_tools(workspace: str = ".") -> XMLTools:
    """Create coding tools scoped to a workspace directory."""
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
        numbered = [f"{i}: {line}" for i, line in enumerate(selected, start=max(1, start))]
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
        return "\n".join(p.name + ("/" if p.is_dir() else "") for p in entries) or "(empty)"

    def find_files(pattern: str) -> str:
        """Find files matching a glob pattern (e.g., '*.py')."""
        matches = sorted(p for p in root.rglob(pattern) if p.is_file())
        results = [str(p.relative_to(root)) for p in matches if str(p.resolve()).startswith(str(root))]
        return "\n".join(results[:30]) or "No files found."

    def search_files(query: str, directory: str = ".") -> str:
        """Search for text across files, returning matching lines."""
        target = _safe_path(directory)
        matches = []
        for file in sorted(target.rglob("*")):
            if not file.is_file():
                continue
            try:
                for i, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
                    if query in line:
                        rel = file.relative_to(root)
                        matches.append(f"{rel}:{i}: {line.strip()}")
                        if len(matches) >= 20:
                            return "\n".join(matches) + "\n(truncated)"
            except (UnicodeDecodeError, PermissionError):
                continue
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

    tools = XMLTools(requires_approval=["execute_python", "write_file"])
    tools.add_tool("read_file", read_file, "Read a file: read_file(path: str)")
    tools.add_tool("read_lines", read_lines, "Read line range: read_lines(path: str, start: int, end: int)")
    tools.add_tool("list_files", list_files, "List files: list_files(directory: str)")
    tools.add_tool("find_files", find_files, "Find files by pattern: find_files(pattern: str)")
    tools.add_tool("search_files", search_files, "Search text in files: search_files(query: str, directory: str)")
    tools.add_tool("write_file", write_file, "Write a file: write_file(path: str, content: str)")
    tools.add_tool("execute_python", execute_python, "Run Python code: execute_python(code: str)")
    return tools
