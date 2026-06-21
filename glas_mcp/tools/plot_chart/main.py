"""
glas_mcp/tools/plot_chart/main.py

MCP tool: plot_chart
Renders a matplotlib chart from structured data and returns a base64-encoded
PNG (or SVG). The LLM has full control over colours, styles, annotations,
axes scales, labels, and can inject custom matplotlib code for advanced layouts.
"""
from __future__ import annotations

import asyncio
import base64
import io
import traceback
from typing import Any, Dict, List

from glas_mcp.tools.base import BaseTool

_VALID_CHART_TYPES = {
    "line", "bar", "barh", "scatter", "pie",
    "histogram", "box", "area", "heatmap", "step", "stem", "errorbar",
}
_VALID_OUTPUT_FMTS = {"png", "svg"}


class PlotChartTool(BaseTool):
    """
    MCP tool that generates a matplotlib chart and returns it as base64.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        from glas_mcp.tools.plot_chart.helpers.builder import draw
        # ── Input validation ────────────────────────────────────────────────
        if not isinstance(arguments, dict):
            return {"error": "Arguments must be a JSON object."}

        chart_type: str = str(arguments.get("chart_type", "")).strip().lower()
        if not chart_type:
            return {"error": "'chart_type' is required."}
        if chart_type not in _VALID_CHART_TYPES:
            return {
                "error": (
                    f"Unknown chart_type '{chart_type}'. "
                    f"Supported: {sorted(_VALID_CHART_TYPES)}."
                )
            }

        data: Dict = arguments.get("data", {})
        if not isinstance(data, dict) or not data:
            return {"error": "'data' is required and must be a non-empty object."}

        title: str           = str(arguments.get("title", "")).strip()
        xlabel: str          = str(arguments.get("xlabel", "")).strip()
        ylabel: str          = str(arguments.get("ylabel", "")).strip()
        colors: List[str]    = list(arguments.get("colors", []))
        style: str           = str(arguments.get("style", "default")).strip()
        figsize: List        = list(arguments.get("figsize", [10, 6]))
        dpi: int             = max(50, min(int(arguments.get("dpi", 150)), 600))
        show_grid: bool      = bool(arguments.get("grid", True))
        grid_axis: str       = str(arguments.get("grid_axis", "both"))
        show_legend: bool    = bool(arguments.get("legend", True))
        legend_loc: str      = str(arguments.get("legend_location", "best"))
        font_size: int       = int(arguments.get("font_size", 12))
        title_font: int      = int(arguments.get("title_font_size", 0)) or font_size + 2
        line_width: float    = float(arguments.get("line_width", 2.0))
        marker: str          = str(arguments.get("marker", "none"))
        alpha: float         = float(arguments.get("alpha", 0.85))
        xscale: str          = str(arguments.get("xscale", "linear"))
        yscale: str          = str(arguments.get("yscale", "linear"))
        xlim: List           = list(arguments.get("xlim", []))
        ylim: List           = list(arguments.get("ylim", []))
        tight: bool          = bool(arguments.get("tight_layout", True))
        bg_color: str        = str(arguments.get("background_color", "white")).strip()
        output_fmt: str      = str(arguments.get("output_format", "png")).strip().lower()
        custom_code: str     = str(arguments.get("custom_code", "")).strip()

        if output_fmt not in _VALID_OUTPUT_FMTS:
            return {
                "error": f"Invalid output_format '{output_fmt}'. Must be 'png' or 'svg'."
            }

        if len(figsize) < 2:
            figsize = [10, 6]

        # Validate style
        available_styles = plt.style.available
        if style not in available_styles and style != "default":
            style = "default"

        # Bundle opts for builder functions
        opts = {
            "line_width": line_width,
            "marker":     marker,
            "alpha":      alpha,
        }

        # ── Render in thread (matplotlib is not async-safe) ─────────────────
        try:
            image_bytes, meta = await asyncio.to_thread(
                self._render,
                chart_type, data, colors, opts,
                title, xlabel, ylabel,
                style, figsize, dpi,
                show_grid, grid_axis,
                show_legend, legend_loc,
                font_size, title_font,
                xscale, yscale, xlim, ylim,
                tight, bg_color,
                output_fmt, custom_code,
            )
        except Exception as exc:
            return {
                "error": f"Chart rendering failed: {exc}",
                "traceback": traceback.format_exc(),
                "hint": (
                    "Check that 'data' matches the expected structure for "
                    f"chart_type='{chart_type}'. See tool description for examples."
                ),
            }

        b64 = base64.b64encode(image_bytes).decode("utf-8")

        return {
            "success":       True,
            "chart_type":    chart_type,
            "output_format": output_fmt,
            "image_base64":  b64,
            "image_size_bytes": len(image_bytes),
            "width_px":      meta["width_px"],
            "height_px":     meta["height_px"],
            "dpi":           dpi,
            "style_used":    style,
        }

    # ── Private render (synchronous — runs in thread pool) ──────────────────

    @staticmethod
    def _render(
        chart_type, data, colors, opts,
        title, xlabel, ylabel,
        style, figsize, dpi,
        show_grid, grid_axis,
        show_legend, legend_loc,
        font_size, title_font,
        xscale, yscale, xlim, ylim,
        tight, bg_color,
        output_fmt, custom_code,
    ):
        # Apply style
        with plt.style.context(style if style != "default" else "default"):
            plt.rcParams.update({"font.size": font_size})

            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)

            # Draw the chart
            draw(chart_type, ax, data, colors, opts)

            # ── Decorations ──────────────────────────────────────────────
            if title:
                ax.set_title(title, fontsize=title_font, fontweight="bold", pad=12)
            if xlabel:
                ax.set_xlabel(xlabel, fontsize=font_size)
            if ylabel:
                ax.set_ylabel(ylabel, fontsize=font_size)

            # Grid (not applicable to pie / heatmap)
            if show_grid and chart_type not in ("pie", "heatmap"):
                ax.grid(True, axis=grid_axis, linestyle="--",
                        linewidth=0.6, alpha=0.7)

            # Legend
            handles, labels = ax.get_legend_handles_labels()
            if show_legend and handles and chart_type != "pie":
                ax.legend(loc=legend_loc, fontsize=max(font_size - 2, 8),
                          framealpha=0.85)

            # Axis scales
            if chart_type not in ("pie", "heatmap"):
                ax.set_xscale(xscale)
                ax.set_yscale(yscale)
                if len(xlim) == 2:
                    ax.set_xlim(xlim)
                if len(ylim) == 2:
                    ax.set_ylim(ylim)

            # ── Custom code injection ─────────────────────────────────────
            if custom_code.strip():
                _safe_exec_custom(custom_code, fig=fig, ax=ax, plt=plt, np=np)

            if tight:
                try:
                    plt.tight_layout()
                except Exception:
                    pass

            # ── Save to buffer ────────────────────────────────────────────
            buf = io.BytesIO()
            fmt = output_fmt if output_fmt == "svg" else "png"
            fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight",
                        facecolor=bg_color)
            plt.close(fig)

            buf.seek(0)
            image_bytes = buf.read()
            width_px  = int(figsize[0] * dpi)
            height_px = int(figsize[1] * dpi)

        return image_bytes, {"width_px": width_px, "height_px": height_px}


def _safe_exec_custom(code: str, **ctx) -> None:
    """
    Execute custom_code in a restricted namespace.
    Only the variables passed in ctx are available (fig, ax, plt, np).
    Dangerous builtins are removed.
    """
    import builtins
    safe_builtins = {
        k: v for k, v in vars(builtins).items()
        if k not in ("open", "exec", "eval", "compile",
                     "__import__", "input", "breakpoint")
    }
    namespace = {**ctx, "__builtins__": safe_builtins}
    exec(code, namespace)  # noqa: S102
