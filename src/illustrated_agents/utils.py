import json
import html
import inspect
import difflib
import textwrap
import uuid

try:
    from pygments import highlight
    from pygments.lexers import DiffLexer, JsonLexer, PythonLexer
    from pygments.formatters import HtmlFormatter
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.console import Console

    HAS_NOTEBOOK_DEPS = True
except ImportError:
    HAS_NOTEBOOK_DEPS = False


class Renderable:
    """Base for display helpers used in notebook environments (Jupyter, Marimo, etc.).

    Constructors are dependency-free; only rendering requires `rich` and `pygments`.
    Subclasses override `_render_html`.
    """

    def _repr_html_(self):
        if not HAS_NOTEBOOK_DEPS:
            return (
                f"<i>{type(self).__name__}: install `rich` and `pygments` "
                f"to render this object.</i>"
            )
        return self._render_html()

    def _render_html(self) -> str:
        raise NotImplementedError


def _get_source(source):
    """Extract source code, optionally for a specific method or property."""
    if type(source) is property:
        src = inspect.getsource(source.fget)
    else:
        src = inspect.getsource(source)
    return textwrap.dedent(src)


class DiffViewer(Renderable):
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

    def _render_html(self):
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


class CodeAnnotator(Renderable):
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
        self.annotations = {
            (k, k) if isinstance(k, int) else tuple(k): v for k, v in (annotations or {}).items()
        }

    def _render_html(self):
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
        if not HAS_NOTEBOOK_DEPS:
            return f"{type(self).__name__}: install `rich` to render."
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


class TrajectoryViewer(Renderable):
    STYLE = """
    .trajectory details { margin: 6px 0; border: 1px solid #e4e4e7; border-radius: 6px; }
    .trajectory summary { cursor: pointer; padding: 8px 12px; font-weight: 500; background: #fafafa; }
    .trajectory summary .kind { color: #71717a; font-weight: 400; margin-left: 6px; }
    .trajectory .run > summary { background: #eef2ff; }
    .trajectory .steps { margin-left: 20px; }
    .trajectory .field { padding: 8px 12px; }
    .trajectory .label { color: #52525b; font-size: 0.8em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
    .trajectory pre { margin: 0; white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 0.9em; }
    .trajectory .highlight { background: transparent; font-size: 0.9em; }
    """

    def __init__(self, trajectory):
        self.trajectory = trajectory

    def _format(self, value):
        if isinstance(value, (dict, list)):
            code = json.dumps(value, indent=2, default=str)
            highlighted = highlight(code, JsonLexer(), HtmlFormatter(nowrap=True))
            return f"<div class='highlight'>{highlighted}</div>"
        return f"<pre>{html.escape(str(value))}</pre>"

    def _render_step(self, step_index, step):
        if step.answer:
            kind = "Final answer"
        elif step.action:
            kind = step.action.get("name", "action")
        else:
            kind = "Thinking"
        fields = "\n".join(
            f"<div class='field'><div class='label'>{label}</div>{self._format(value)}</div>"
            for label, value in vars(step).items()
            if value
        )
        return f"<details><summary>Step {step_index} <span class='kind'>· {kind}</span></summary>{fields}</details>"

    def _render_run(self, run_index, run):
        query = f"<details class='run'><summary>Run {run_index} <span class='kind'>· User query</span></summary><div class='field'>{self._format(run['query'])}</div></details>"
        steps = "\n".join(
            self._render_step(step_index, step) for step_index, step in enumerate(run["steps"], start=1)
        )
        return f"{query}<div class='steps'>{steps}</div>"

    def _render_html(self):
        pygments_css = HtmlFormatter().get_style_defs(".highlight")
        runs = "\n".join(
            self._render_run(run_index, run) for run_index, run in enumerate(self.trajectory.runs, start=1)
        )
        return f"<style>{pygments_css}{self.STYLE}</style><div class='trajectory'>{runs}</div>"


class Exercise(Renderable):
    """Collapsible exercise with hint and solution for Jupyter notebooks.

    Usage:
        Exercise(
            task="Change max_steps to 1 and run the agent. What happens?",
            hint="The agent needs at least 2 steps for a tool call.",
            solution="With max_steps=1, the agent can't see the observation."
        )
    """

    def __init__(self, task, hint=None, solution=None):
        self.task = task
        self.hint = hint
        self.solution = solution

    def _render_html(self):
        uid = f"ex-{uuid.uuid4().hex[:8]}"
        bg = "#0d1117"

        sections = ""
        if self.hint:
            sections += (
                f'<details class="ex-section"><summary>Hint</summary>'
                f'<div class="ex-body">{html.escape(self.hint)}</div></details>'
            )
        if self.solution:
            sections += (
                f'<details class="ex-section"><summary>Solution</summary>'
                f'<div class="ex-body">{html.escape(self.solution)}</div></details>'
            )

        return f"""<style>
.{uid}{{background:{bg};border:1px solid #f1c40f44;border-left:3px solid #f1c40f;border-radius:6px;padding:16px 20px;margin:10px 0;font-family:system-ui,-apple-system,sans-serif;color:#e6edf3;font-size:14px;line-height:1.6}}
.{uid} .ex-title{{color:#f1c40f;font-weight:600;font-size:13px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px}}
.{uid} .ex-task{{margin-bottom:14px;white-space:pre-line}}
.{uid} .ex-section{{margin:4px 0}}
.{uid} .ex-section>summary{{cursor:pointer;color:#8b949e;font-size:13px;padding:4px 0}}
.{uid} .ex-section>summary:hover{{color:#c9d1d9}}
.{uid} .ex-body{{color:#c9d1d9;font-size:13px;padding:8px 0 4px 20px;line-height:1.6;white-space:pre-line}}
</style>
<div class="{uid}">
<div class="ex-title">Exercise</div>
<div class="ex-task">{html.escape(self.task)}</div>
{sections}
</div>"""


class ComparisonViewer(Renderable):
    """Side-by-side comparison of multiple implementations.

    Usage:
        ComparisonViewer([
            ("Prompt-based", ch5.TinyAgent._execute_action),
            ("Native",       ch5_native.TinyAgent._execute_action),
        ])
    """

    def __init__(self, sources, style="github-dark"):
        self.sources = sources  # [(label, source), ...]
        self.style = style

    def _render_html(self):
        uid = f"cv-{uuid.uuid4().hex[:8]}"
        fmt = HtmlFormatter(style=self.style, linenos="inline", cssclass=uid)
        bg = fmt.style.background_color

        columns = ""
        for label, source in self.sources:
            src = _get_source(source)
            code = highlight(src, PythonLexer(), fmt)
            code = code.replace("<pre><span></span>", "<pre>")
            columns += (
                f'<div class="{uid}-col">'
                f'<div class="{uid}-label">{html.escape(label)}</div>'
                f'<div class="{uid}-code">{code}</div></div>'
            )

        return f"""<style>
{fmt.get_style_defs(f".{uid}")}
.{uid}-wrap{{display:flex;gap:0;background:{bg};border-radius:8px;border:1px solid #444;margin:10px 0;overflow-x:auto}}
.{uid}-col{{flex:1;min-width:0;border-right:1px solid #30363d}}
.{uid}-col:last-child{{border-right:none}}
.{uid}-label{{color:#8b949e;font-size:13px;font-family:system-ui,-apple-system,sans-serif;padding:8px 12px;border-bottom:1px solid #30363d;font-weight:600}}
.{uid}-code{{overflow-x:auto}}
.{uid}{{background:{bg}!important;color:#e6edf3!important;font-size:13px}}
.{uid} pre{{margin:0;padding:8px;line-height:1.5em!important;background:{bg}!important;color:#e6edf3!important}}
.{uid} .linenos{{background:{bg}!important;color:#e6edf3!important}}
</style>
<div class="{uid}-wrap">{columns}</div>"""


class EvolutionViewer(Renderable):
    """Show how a function/method evolves across chapters.

    New and changed lines are highlighted at each stage.

    Usage:
        EvolutionViewer([
            ("Chapter 1", ch1.TinyAgent._step),
            ("Chapter 4", ch4.TinyAgent._step),
            ("Chapter 5", ch5.TinyAgent._step),
        ])
    """

    def __init__(self, stages, style="github-dark"):
        self.stages = stages  # [(label, source), ...]
        self.style = style

    def _render_html(self):
        uid = f"ev-{uuid.uuid4().hex[:8]}"
        bg = HtmlFormatter(style=self.style).style.background_color
        prev_lines = None
        blocks = []

        for label, source in self.stages:
            src = _get_source(source)
            curr_lines = src.splitlines()

            # Diff against previous version to find new/changed lines
            hl_lines = []
            if prev_lines is not None:
                matcher = difflib.SequenceMatcher(None, prev_lines, curr_lines)
                for tag, _, _, j1, j2 in matcher.get_opcodes():
                    if tag in ("insert", "replace"):
                        hl_lines.extend(range(j1 + 1, j2 + 1))

            fmt = HtmlFormatter(style=self.style, linenos="inline", cssclass=uid, hl_lines=hl_lines)
            code = highlight(src, PythonLexer(), fmt)
            code = code.replace("<pre><span></span>", "<pre>")

            blocks.append(
                f'<div class="{uid}-stage">'
                f'<div class="{uid}-label">{html.escape(label)}</div>'
                f'<div class="{uid}-code">{code}</div></div>'
            )
            prev_lines = curr_lines

        connector = f'<div class="{uid}-conn">&#9660;</div>'
        body = connector.join(blocks)

        return f"""<style>
{fmt.get_style_defs(f".{uid}")}
.{uid}-wrap{{margin:10px 0}}
.{uid}-stage{{background:{bg};border:1px solid #444;border-radius:8px;overflow:hidden}}
.{uid}-label{{color:#8b949e;font-size:13px;font-family:system-ui,-apple-system,sans-serif;padding:8px 12px;border-bottom:1px solid #30363d;font-weight:600}}
.{uid}-code{{overflow-x:auto}}
.{uid}-conn{{text-align:center;color:#30363d;font-size:18px;padding:4px 0}}
.{uid}{{background:{bg}!important;color:#e6edf3!important;font-size:13px}}
.{uid} pre{{margin:0;padding:8px;line-height:1.5em!important;background:{bg}!important;color:#e6edf3!important}}
.{uid} .hll{{background:#3d4626!important;display:block;width:100%}}
.{uid} .linenos{{background:{bg}!important;color:#e6edf3!important}}
</style>
<div class="{uid}-wrap">{body}</div>"""
