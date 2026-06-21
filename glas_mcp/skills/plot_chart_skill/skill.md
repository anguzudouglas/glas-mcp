# Skill: plot_chart

**Tool:** `plot_chart`  
**Version:** 1.0.0

## Purpose
Generate any matplotlib chart and return it as a base64-encoded PNG or SVG image. Full control over type, data, colors, styles, labels, annotations, and axes.

## Supported Chart Types

| Type | Best For |
|------|----------|
| `line` | Trends over time, continuous data |
| `bar` | Comparing categories, grouped comparison |
| `barh` | Horizontal bars, long category names |
| `scatter` | Correlation, distribution, clusters |
| `pie` | Part-of-whole (use sparingly, max 7 slices) |
| `histogram` | Distribution of a dataset |
| `box` | Statistical distribution, quartiles, outliers |
| `area` | Cumulative trends, stacked comparisons |
| `heatmap` | Matrices, correlations, confusion matrices |
| `step` | Discrete data, step functions, histograms |
| `stem` | Discrete signals, impulse responses |
| `errorbar` | Measurements with uncertainty |

## Data Structure by Type

### line / area / step / stem
```json
{
  "x": [1, 2, 3, 4, 5],
  "y": [[10, 14, 13, 17, 20], [5, 8, 10, 12, 15]],
  "labels": ["Revenue", "Costs"]
}
```

### bar / barh
```json
{
  "categories": ["Q1", "Q2", "Q3", "Q4"],
  "values": [[120, 145, 160, 175], [90, 110, 105, 130]],
  "labels": ["Product A", "Product B"]
}
```

### scatter
```json
{
  "series": [
    {"x": [1,2,3], "y": [4,5,6], "label": "Group A", "size": [50,80,100]},
    {"x": [2,3,4], "y": [7,5,8], "label": "Group B"}
  ]
}
```

### pie
```json
{
  "labels": ["Alpha", "Beta", "Gamma"],
  "values": [40, 35, 25],
  "explode": [0.05, 0, 0]
}
```

### histogram
```json
{
  "values": [[1,2,3,4,5,5,5,6,7,8,8,9]],
  "labels": ["Distribution"],
  "bins": 20
}
```

### box
```json
{
  "data": [[1,2,3,4,5,6,7], [3,4,5,6,7,8,9]],
  "labels": ["Before", "After"]
}
```

### heatmap
```json
{
  "matrix": [[0.9, 0.1], [0.05, 0.95]],
  "row_labels": ["Actual A", "Actual B"],
  "col_labels": ["Pred A", "Pred B"],
  "annotate": true
}
```

### errorbar
```json
{
  "x": [1, 2, 3, 4],
  "y": [10, 12, 9, 14],
  "yerr": [0.5, 0.8, 0.4, 1.0],
  "label": "Measurements"
}
```

## Style Guide

### Recommended Styles
| Use Case | Style |
|----------|-------|
| Presentations / slides | `dark_background` |
| Academic / papers | `seaborn-v0_8` or `bmh` |
| Business dashboards | `ggplot` |
| Minimal / clean | `default` |
| Colorblind-safe | `tableau-colorblind10` |

### Color Palettes
```
Cool blues:    ["#003f5c","#2f4b7c","#665191","#a05195","#d45087","#f95d6a"]
Traffic light: ["#2ECC71","#F39C12","#E74C3C"]
Gradient:      ["#08306b","#2171b5","#6baed6","#bdd7e7","#eff3ff"]
Pastel:        ["#AEC6CF","#FFD1DC","#B5EAD7","#FFDAC1","#E2B4BD"]
High contrast: ["#000000","#E69F00","#56B4E9","#009E73","#F0E442","#0072B2"]
```

### Annotation Examples (custom_code)
```python
# Horizontal reference line
ax.axhline(y=100, color='red', linestyle='--', linewidth=1.5, label='Target')

# Annotate a specific point
ax.annotate('Peak', xy=(3, 25), xytext=(4, 22),
            arrowprops=dict(arrowstyle='->', color='black'), fontsize=10)

# Shade a region
ax.axvspan(2, 4, alpha=0.1, color='yellow', label='Q2')

# Add a text box
ax.text(0.05, 0.95, 'n=100', transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
```

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | `true` / `false` |
| `image_base64` | Base64-encoded PNG or SVG |
| `output_format` | `"png"` or `"svg"` |
| `image_size_bytes` | Size of the encoded image |
| `width_px` / `height_px` | Final dimensions |
| `dpi` | Rendered DPI |
| `style_used` | Matplotlib style applied |

## Displaying the Image

The `image_base64` value is a standard base64 string. Decode it to display:
- **Web:** `<img src="data:image/png;base64,{image_base64}">`
- **Python:** `base64.b64decode(result["image_base64"])`

## Quality Rules

1. **Always set a `title`** — it makes the chart self-explanatory.
2. **Set `xlabel` and `ylabel`** unless the chart type makes them obvious (pie).
3. **Pie charts: max 7 slices.** More than that → use a bar chart.
4. **For time series:** put time/date on x-axis, units on y-axis.
5. **For comparisons:** `bar` is clearer than `line`; `barh` is clearer when categories have long names.
6. **High DPI for reports:** set `dpi: 200–300`.
7. **SVG for web/interactive:** set `output_format: "svg"` for scalable output.
8. **Dark presentations:** set `style: "dark_background"`, use bright accent colors.
