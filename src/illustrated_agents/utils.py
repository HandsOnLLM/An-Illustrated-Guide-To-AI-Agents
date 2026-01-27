import inspect
import difflib
import textwrap
from pygments import highlight
from pygments.lexers import DiffLexer
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


class DiffViewer:
    """
    Show a GitHub-style, syntax-highlighted diff of two imported classes
    directly inside a Jupyter notebook cell.
    """

    def __init__(
        self, old_cls, new_cls, old_name="Old", new_name="New", style="github-dark"
    ):
        self.old_cls = old_cls
        self.new_cls = new_cls
        self.old_name = old_name
        self.new_name = new_name
        self.style = style

    def _repr_html_(self):
        # 1. Extract and normalize source
        old_src = textwrap.dedent(inspect.getsource(self.old_cls))
        new_src = textwrap.dedent(inspect.getsource(self.new_cls))

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
        formatter = HtmlFormatter(style=self.style)
        css = formatter.get_style_defs(".highlight")

        # 4. Highlight
        html = highlight(diff, DiffLexer(), formatter)

        # 5. Inject CSS so it renders nicely inline
        return f"""
    <style>
    {css}
    .highlight {{
        font-size: 14px;
        line-height: 1.4;
        border-radius: 8px;
        padding: 12px;
        overflow-x: auto;
    }}
    </style>
    {html}
    """


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
        self.annotations = {
            (k, k) if isinstance(k, int) else tuple(k): v
            for k, v in (annotations or {}).items()
        }

    def _get_source(self):
        """Extract source code, optionally for a specific method or property."""
        if type(self.source) is property:
            src = inspect.getsource(self.source.fget)
        else:
            src = inspect.getsource(self.source)
        return textwrap.dedent(src)

    def _repr_html_(self):
        src = self._get_source()
        hl_lines = [
            ln for start, end in self.annotations for ln in range(start, end + 1)
        ]

        fmt = HtmlFormatter(
            style=self.style, linenos="inline", cssclass="ca", hl_lines=hl_lines
        )
        code = highlight(src, PythonLexer(), fmt)
        bg = fmt.style.background_color

        # Build annotation divs with connector lines
        notes = "".join(
            f'<div style="position:absolute;top:{(start - 1) * 1.5}rem;height:{(end - start + 1) * 1.5}rem;'
            f'display:flex;align-items:center;font-size:14px;padding-left:16px;padding-right:16px">'
            f'<span style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#f1c40f;border-radius:2px"></span>'
            f'<span style="color:#ddd;line-height:1.4">{text}</span></div>'
            for (start, end), text in sorted(self.annotations.items())
        )

        return f"""<style>
{fmt.get_style_defs(".ca")}
.ca pre{{margin:0;line-height:1.5rem}}
.ca .hll{{background:#3d4626!important;display:block;width:100%}}
.ca .linenos{{background:transparent!important}}
</style>
<div style="display:inline-flex;background:{bg};border-radius:8px;border:1px solid #444;margin:10px 0;font-family:monospace">
<div style="flex:3;overflow-x:auto">{code}</div>
<div style="flex:1;min-width:500px;position:relative;background:rgba(255,255,255,.03);border-left:1px solid #555;color:#ccc;font-family:system-ui,sans-serif">{notes}</div>
</div>"""

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._repr_html_())
