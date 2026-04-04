import inspect
import difflib
import textwrap
import uuid
from pygments import highlight
from pygments.lexers import DiffLexer
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from rich.tree import Tree
from rich.panel import Panel
from rich.console import Console


TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


def function_to_dict(func) -> dict:
    """Convert a Python function to an OpenAI-style function schema."""
    sig = inspect.signature(func)
    properties = {}
    required = []
    for name, param in sig.parameters.items():
        properties[name] = {"type": TYPE_MAP.get(param.annotation, "string")}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    return {
        "name": func.__name__,
        "description": inspect.getdoc(func) or "",
        "parameters": {"type": "object", "properties": properties, "required": required},
    }


def _get_source(source):
    """Extract source code, optionally for a specific method or property."""
    if type(source) is property:
        src = inspect.getsource(source.fget)
    else:
        src = inspect.getsource(source)
    return textwrap.dedent(src)


class DiffViewer:
    """
    Show a GitHub-style, syntax-highlighted diff of two imported classes
    directly inside a Jupyter notebook cell.
    """

    def __init__(self, old_cls, new_cls, old_name="Old", new_name="New", style="github-dark"):
        self.old_cls = old_cls
        self.new_cls = new_cls
        self.old_name = old_name
        self.new_name = new_name
        self.style = style

    def _repr_html_(self):
        # 1. Extract and normalize source
        old_src = _get_source(self.old_cls)
        new_src = _get_source(self.new_cls)

        # 2. Generate unified diff
        diff = "\n".join(
            difflib.unified_diff(
                old_src.splitlines(),
                new_src.splitlines(),
                fromfile=self.old_name,
                tofile=self.new_name,
                lineterm="",
            )
        )

        # 3. Pygments formatter (Diff + Python-aware styling)
        uid = f"dv-{uuid.uuid4().hex[:8]}"
        formatter = HtmlFormatter(style=self.style, cssclass=uid)
        bg = formatter.style.background_color

        # 4. Highlight
        html = highlight(diff, DiffLexer(), formatter)

        # 5. Inject CSS so it renders nicely inline
        return f"""<style>
{formatter.get_style_defs(f".{uid}")}
.{uid}{{background:{bg}!important;color:#e6edf3!important;font-size:14px;line-height:1.4;border-radius:8px;padding:12px;overflow-x:auto}}
.{uid} pre{{background:{bg}!important;color:#e6edf3!important;margin:0}}
.{uid} code{{background:{bg}!important;color:#e6edf3!important}}
</style>
{html}"""


class CodeAnnotator:
    """
    Annotate Python source code with comments displayed alongside.
    """

    def __init__(
        self,
        source,
        annotations: dict[tuple | str, str] = None,
        style="github-dark",
        property: str = None,
    ):
        self.source = source
        self.property = property
        self.style = style
        self.annotations = {(k, k) if isinstance(k, int) else tuple(k): v for k, v in (annotations or {}).items()}

    def _repr_html_(self):
        src = _get_source(self.source)
        hl_lines = [ln for start, end in self.annotations for ln in range(start, end + 1)]

        uid = f"ca-{uuid.uuid4().hex[:8]}"
        fmt = HtmlFormatter(style=self.style, linenos="inline", cssclass=uid, hl_lines=hl_lines)
        code = highlight(src, PythonLexer(), fmt)
        bg = fmt.style.background_color

        # Remove the empty <span></span> that Pygments adds at the start of the pre
        # This can cause alignment issues in some notebook environments
        code = code.replace("<pre><span></span>", "<pre>")

        # Build annotation divs with connector lines
        notes = "".join(
            f'<div style="position:absolute;top:{(start - 1) * 1.5}em;height:{(end - start + 1) * 1.5}em;'
            f'display:flex;align-items:center;font-size:14px;padding-left:16px;padding-right:16px">'
            f'<span style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#f1c40f;border-radius:2px"></span>'
            f'<span style="color:#ddd;line-height:1.4">{text}</span></div>'
            for (start, end), text in sorted(self.annotations.items())
        )

        # Override the global `pre { line-height: 125%; }` that Pygments generates
        # Use !important to ensure our line-height takes precedence in all environments
        return f"""<style>
pre{{line-height:1.5em!important}}
{fmt.get_style_defs(f".{uid}")}
.{uid}{{background:{bg}!important;color:#e6edf3!important;font-size:14px}}
.{uid} pre{{margin:0;padding:0;line-height:1.5em!important;background:{bg}!important;color:#e6edf3!important}}
.{uid} code{{background:{bg}!important;color:#e6edf3!important}}
.{uid} .hll{{background:#3d4626!important;display:block;width:100%}}
.{uid} .linenos{{background:{bg}!important;color:#e6edf3!important}}
</style>
<div style="display:inline-flex;align-items:flex-start;background:{bg};border-radius:8px;border:1px solid #444;margin:10px 0;font-family:monospace;font-size:14px;line-height:1.5em">
<div style="flex:3;overflow-x:auto;background:{bg}">{code}</div>
<div style="flex:1;min-width:500px;position:relative;background:{bg};border-left:1px solid #555;color:#ccc;font-family:system-ui,sans-serif;font-size:14px">{notes}</div>
</div>"""

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._repr_html_())


class ChapterOverview:
    """Display chapter summary as a rich Panel + Tree in Jupyter."""

    def __init__(self, modules):
        self.modules = modules

    def __repr__(self):
        tree = Tree("[bold]TinyAgent[/]")
        max_len = max(len(m[0]) for m in self.modules)

        for name, status, desc in self.modules:
            padded = name.ljust(max_len)
            if status == "new":
                tree.add(f"[bold green]{padded}[/] [dim]← [/][bold]New [dim]({desc})[/]")
            elif status == "updated":
                tree.add(f"[bold orange]{padded}[/] [dim]← [/][bold]Updated [dim]({desc})[/]")
            else:
                tree.add(f"[dim]{padded}[/]")

        panel = Panel(tree, title="What We Built", border_style="dim")
        Console(force_terminal=True).print(panel)
        return ""
