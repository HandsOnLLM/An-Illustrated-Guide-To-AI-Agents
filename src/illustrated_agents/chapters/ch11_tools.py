"""Code tools for the Coding Agent."""

import subprocess
import sys
from pathlib import Path

from illustrated_agents.tools import Tools
from illustrated_agents.chapters.ch11 import XMLTools


def create_code_tools(workspace: str = ".") -> Tools:
    """Create coding tools scoped to a workspace directory."""
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)

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
            output = result.stdout + result.stderr
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30s limit)."

    tools = XMLTools()
    tools.add_tool("read_file", read_file, "Read a file: read_file(path: str)")
    tools.add_tool("write_file", write_file, "Write a file: write_file(path: str, content: str)")
    tools.add_tool("list_files", list_files, "List files: list_files(directory: str)")
    tools.add_tool("execute_python", execute_python, "Run Python code: execute_python(code: str)")
    return tools
