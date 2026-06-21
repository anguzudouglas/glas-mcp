# Skill: document_create_pptx

**Tool:** `document_create_pptx`  
**Version:** 1.0.0

## Purpose
Generate a PowerPoint presentation (.pptx) from structured slide definitions. Supports title slides, bullet-point slides, image slides, and two-column layouts using python-pptx.

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `slides` | array | **required** | Array of slide definitions |
| `filename` | string | `"presentation.pptx"` | Output filename |
| `theme_color` | string | `"#003f5c"` | Hex color for title bar and accents |
| `font_family` | string | `"Calibri"` | Slide body font |

## Slide Definition Structure

```json
{
  "layout": "title | content | two_column | blank | image",
  "title": "Slide Title",
  "subtitle": "Optional subtitle (title slide only)",
  "bullets": ["Point one", "Point two", "  Sub-point (indent with spaces)"],
  "body": "Free-form text for content slides",
  "image_base64": "...",
  "image_caption": "Figure 1: Caption text",
  "left_column": ["Left bullet 1", "Left bullet 2"],
  "right_column": ["Right bullet 1", "Right bullet 2"],
  "notes": "Speaker notes for this slide"
}
```

## Layout Types

| Layout | Fields Used | Best For |
|--------|-------------|----------|
| `title` | `title`, `subtitle` | Opening slide |
| `content` | `title`, `bullets` or `body` | Standard text slide |
| `two_column` | `title`, `left_column`, `right_column` | Comparison slides |
| `image` | `title`, `image_base64`, `image_caption` | Chart/diagram slides |
| `blank` | `title`, `body` | Custom content |

## Full Presentation Example

```json
{
  "filename": "q4_review.pptx",
  "theme_color": "#003f5c",
  "slides": [
    {
      "layout": "title",
      "title": "Q4 2024 Business Review",
      "subtitle": "Quarterly Performance Report — Anguzudouglas"
    },
    {
      "layout": "content",
      "title": "Agenda",
      "bullets": [
        "1. Executive Summary",
        "2. Revenue Performance",
        "3. Key Achievements",
        "4. Challenges & Mitigation",
        "5. Q1 2025 Outlook"
      ]
    },
    {
      "layout": "content",
      "title": "Key Performance Metrics",
      "bullets": [
        "Revenue: $700K (+18% YoY)",
        "  Q4 alone: $175K (best quarter ever)",
        "Active Users: 45,000 (+32% YoY)",
        "Churn Rate: 2.1% (improved from 3.4%)",
        "NPS Score: 72 (industry avg: 45)"
      ],
      "notes": "Emphasize the churn improvement — it was a major initiative this year"
    },
    {
      "layout": "two_column",
      "title": "Strengths vs Areas for Improvement",
      "left_column": [
        "✅ Strong revenue growth",
        "✅ Low churn rate",
        "✅ High NPS score",
        "✅ New enterprise clients"
      ],
      "right_column": [
        "⚠️ APAC market penetration",
        "⚠️ Support ticket volume",
        "⚠️ Mobile app retention",
        "⚠️ Hiring pipeline"
      ]
    }
  ]
}
```

## Bullet Point Formatting

- Indent sub-bullets with 2–4 leading spaces: `"  Sub-point"`
- Use Unicode symbols for visual hierarchy: `✅ ⚠️ 🎯 📊 💡 →`
- Keep bullets to 6–7 words max — this is a slide, not an essay
- Maximum 6 bullets per slide for readability

## Quality Rules

1. **First slide must be `layout: "title"`** — sets the tone and branding.
2. **Add an Agenda slide** for presentations with > 4 slides.
3. **One idea per slide** — if you need to say 10 things, make 10 slides.
4. **Speaker notes go in `notes`** — the slide itself should be a summary, not a transcript.
5. **Use `two_column`** for before/after, pros/cons, or comparison slides.
6. **Image slides:** generate the chart with `plot_chart` first, then pass `image_base64` to the slide.
7. **`theme_color`** is applied to title backgrounds — choose brand colors.

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | `true` / `false` |
| `filename` | Final filename |
| `path` | Server-side path |
| `size_bytes` | File size |
| `slide_count` | Number of slides created |
