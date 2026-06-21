"""
plot_chart/helpers/builder.py

Builds matplotlib figures from structured data dicts.
Each chart type has its own _draw_* function.
The caller (main.py) handles figure setup, styling, and saving.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm


# ── Colour helpers ─────────────────────────────────────────────────────────────

def _resolve_colors(colors: List[str], n: int) -> List[Any]:
    """
    Resolve a user-supplied colour list to exactly n colours.
    Falls back to the current axes colour cycle when the list is short.
    """
    if not colors:
        return [f"C{i}" for i in range(n)]
    if len(colors) >= n:
        return list(colors[:n])
    # cycle the provided colours
    return [colors[i % len(colors)] for i in range(n)]


def _parse_color(c: str) -> Any:
    """Parse a colour string — handles tuples written as strings like '(0.2,0.4,0.8)'."""
    c = c.strip()
    if c.startswith("(") and c.endswith(")"):
        try:
            return tuple(float(x) for x in c.strip("()").split(","))
        except ValueError:
            pass
    return c


def _apply_colors(colors: List[str]) -> List[Any]:
    return [_parse_color(c) for c in colors]


# ══════════════════════════════════════════════════════════════════════════════
# Chart drawers
# ══════════════════════════════════════════════════════════════════════════════

def draw_line(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    x      = data.get("x", [])
    ys     = data.get("y", [data.get("values", [])])
    if not isinstance(ys[0], (list, tuple, np.ndarray)):
        ys = [ys]
    labels = data.get("labels", [f"Series {i+1}" for i in range(len(ys))])
    clrs   = _apply_colors(_resolve_colors(colors, len(ys)))
    mk     = opts.get("marker", "none")
    mk     = None if mk == "none" else mk
    lw     = float(opts.get("line_width", 2.0))
    for i, y in enumerate(ys):
        ax.plot(x, y, label=labels[i] if i < len(labels) else f"S{i+1}",
                color=clrs[i], linewidth=lw,
                marker=mk, markerfacecolor=clrs[i])


def draw_area(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    x      = data.get("x", [])
    ys     = data.get("y", [data.get("values", [])])
    if not isinstance(ys[0], (list, tuple, np.ndarray)):
        ys = [ys]
    labels = data.get("labels", [f"Series {i+1}" for i in range(len(ys))])
    clrs   = _apply_colors(_resolve_colors(colors, len(ys)))
    alpha  = float(opts.get("alpha", 0.6))
    lw     = float(opts.get("line_width", 2.0))
    for i, y in enumerate(ys):
        lbl = labels[i] if i < len(labels) else f"S{i+1}"
        ax.fill_between(x, y, alpha=alpha, color=clrs[i], label=lbl)
        ax.plot(x, y, color=clrs[i], linewidth=lw)


def draw_step(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    x      = data.get("x", [])
    ys     = data.get("y", [data.get("values", [])])
    if not isinstance(ys[0], (list, tuple, np.ndarray)):
        ys = [ys]
    labels = data.get("labels", [f"Series {i+1}" for i in range(len(ys))])
    clrs   = _apply_colors(_resolve_colors(colors, len(ys)))
    lw     = float(opts.get("line_width", 2.0))
    for i, y in enumerate(ys):
        ax.step(x, y, label=labels[i] if i < len(labels) else f"S{i+1}",
                color=clrs[i], linewidth=lw, where="mid")


def draw_stem(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    x      = data.get("x", list(range(len(data.get("y", [[]])[0]))))
    ys     = data.get("y", [data.get("values", [])])
    if not isinstance(ys[0], (list, tuple, np.ndarray)):
        ys = [ys]
    clrs   = _apply_colors(_resolve_colors(colors, len(ys)))
    labels = data.get("labels", [f"Series {i+1}" for i in range(len(ys))])
    for i, y in enumerate(ys):
        mc = clrs[i]
        container = ax.stem(x, y, linefmt="-", markerfmt="o", basefmt=" ")
        container.markerline.set_color(mc)
        container.stemlines.set_color(mc)
        container.markerline.set_label(labels[i] if i < len(labels) else f"S{i+1}")


def draw_bar(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    cats   = data.get("categories", [])
    vals   = data.get("values", [])
    if not vals:
        return
    if not isinstance(vals[0], (list, tuple, np.ndarray)):
        vals = [vals]
    labels = data.get("labels", [f"Group {i+1}" for i in range(len(vals))])
    clrs   = _apply_colors(_resolve_colors(colors, len(vals)))
    alpha  = float(opts.get("alpha", 0.85))
    n_groups = len(vals)
    x = np.arange(len(cats))
    width = 0.8 / max(n_groups, 1)
    for i, v in enumerate(vals):
        offset = (i - n_groups / 2 + 0.5) * width
        ax.bar(x + offset, v, width, label=labels[i] if i < len(labels) else f"G{i+1}",
               color=clrs[i], alpha=alpha)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=30 if len(cats) > 6 else 0, ha="right")


def draw_barh(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    cats   = data.get("categories", [])
    vals   = data.get("values", [])
    if not vals:
        return
    if not isinstance(vals[0], (list, tuple, np.ndarray)):
        vals = [vals]
    labels = data.get("labels", [f"Group {i+1}" for i in range(len(vals))])
    clrs   = _apply_colors(_resolve_colors(colors, len(vals)))
    alpha  = float(opts.get("alpha", 0.85))
    n_groups = len(vals)
    y = np.arange(len(cats))
    height = 0.8 / max(n_groups, 1)
    for i, v in enumerate(vals):
        offset = (i - n_groups / 2 + 0.5) * height
        ax.barh(y + offset, v, height, label=labels[i] if i < len(labels) else f"G{i+1}",
                color=clrs[i], alpha=alpha)
    ax.set_yticks(y)
    ax.set_yticklabels(cats)


def draw_scatter(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    series = data.get("series", [])
    if not series and "x" in data:
        series = [{"x": data["x"], "y": data["y"],
                   "label": data.get("label", "Data")}]
    clrs = _apply_colors(_resolve_colors(colors, len(series)))
    alpha = float(opts.get("alpha", 0.85))
    for i, s in enumerate(series):
        sz = s.get("size", 60)
        ax.scatter(s["x"], s["y"], label=s.get("label", f"S{i+1}"),
                   color=clrs[i], s=sz, alpha=alpha)


def draw_pie(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    labels  = data.get("labels", [])
    values  = data.get("values", [])
    explode = data.get("explode", [0] * len(values))
    clrs    = _apply_colors(_resolve_colors(colors, len(values))) if colors else None
    ax.pie(values, labels=labels, explode=explode,
           colors=clrs, autopct="%1.1f%%",
           startangle=90, pctdistance=0.8,
           wedgeprops={"linewidth": 1.2, "edgecolor": "white"})
    ax.axis("equal")


def draw_histogram(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    datasets = data.get("values", [])
    if not datasets:
        return
    if not isinstance(datasets[0], (list, tuple, np.ndarray)):
        datasets = [datasets]
    labels = data.get("labels", [f"Data {i+1}" for i in range(len(datasets))])
    bins   = data.get("bins", 20)
    clrs   = _apply_colors(_resolve_colors(colors, len(datasets)))
    alpha  = float(opts.get("alpha", 0.7))
    for i, d in enumerate(datasets):
        ax.hist(d, bins=bins, label=labels[i] if i < len(labels) else f"D{i+1}",
                color=clrs[i], alpha=alpha, edgecolor="white", linewidth=0.5)


def draw_box(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    datasets = data.get("data", [])
    labels   = data.get("labels", [f"Group {i+1}" for i in range(len(datasets))])
    clrs     = _apply_colors(_resolve_colors(colors, len(datasets)))
    bp = ax.boxplot(datasets, labels=labels, patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2})
    for patch, clr in zip(bp["boxes"], clrs):
        patch.set_facecolor(clr)
        patch.set_alpha(float(opts.get("alpha", 0.8)))


def draw_heatmap(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    matrix    = np.array(data.get("matrix", [[0]]))
    row_labels = data.get("row_labels", [str(i) for i in range(matrix.shape[0])])
    col_labels = data.get("col_labels", [str(j) for j in range(matrix.shape[1])])
    annotate   = data.get("annotate", True)
    cmap       = colors[0] if colors else "YlOrRd"
    im = ax.imshow(matrix, cmap=cmap, aspect="auto")
    ax.figure.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks(range(len(col_labels)))
    ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    if annotate:
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2g}",
                        ha="center", va="center", fontsize=9,
                        color="white" if matrix[i, j] > (matrix.max() + matrix.min()) / 2 else "black")


def draw_errorbar(ax: plt.Axes, data: Dict, colors: List, opts: Dict) -> None:
    x    = data.get("x", [])
    y    = data.get("y", [])
    yerr = data.get("yerr", None)
    xerr = data.get("xerr", None)
    lbl  = data.get("label", "Data")
    clrs = _apply_colors(_resolve_colors(colors, 1))
    lw   = float(opts.get("line_width", 2.0))
    ax.errorbar(x, y, yerr=yerr, xerr=xerr, label=lbl,
                color=clrs[0], linewidth=lw,
                capsize=5, capthick=2, elinewidth=1.5,
                marker="o", markersize=6)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

_DRAWERS = {
    "line":      draw_line,
    "area":      draw_area,
    "step":      draw_step,
    "stem":      draw_stem,
    "bar":       draw_bar,
    "barh":      draw_barh,
    "scatter":   draw_scatter,
    "pie":       draw_pie,
    "histogram": draw_histogram,
    "box":       draw_box,
    "heatmap":   draw_heatmap,
    "errorbar":  draw_errorbar,
}


def draw(chart_type: str, ax: plt.Axes, data: Dict,
         colors: List, opts: Dict) -> None:
    """Dispatch to the right draw function."""
    fn = _DRAWERS.get(chart_type)
    if fn is None:
        raise ValueError(
            f"Unknown chart type '{chart_type}'. "
            f"Supported: {sorted(_DRAWERS.keys())}."
        )
    fn(ax, data, colors, opts)
