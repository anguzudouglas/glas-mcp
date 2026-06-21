# Skill: document_create_docx

**Tool:** `document_create_docx`  
**Version:** 1.0.0

## Purpose
Generate a Microsoft Word (.docx) document from HTML content. Uses htmldocx to convert HTML headings, paragraphs, lists, and tables into native Word elements.

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `html_content` | string | **required** | HTML to convert |
| `filename` | string | `"document.docx"` | Output filename |
| `title` | string | `""` | Document metadata title |
| `author` | string | `""` | Document metadata author |

## Supported HTML Elements

| HTML | Word Equivalent |
|------|----------------|
| `<h1>` | Heading 1 |
| `<h2>` | Heading 2 |
| `<h3>` | Heading 3 |
| `<p>` | Normal paragraph |
| `<strong>`, `<b>` | Bold |
| `<em>`, `<i>` | Italic |
| `<ul>`, `<li>` | Bulleted list |
| `<ol>`, `<li>` | Numbered list |
| `<table>`, `<tr>`, `<td>`, `<th>` | Word table |
| `<br>` | Line break |
| `<hr>` | Horizontal rule |

## Template

```html
<!DOCTYPE html>
<html>
<body>

<h1>Document Title</h1>
<p><strong>Author:</strong> Anguzudouglas | <strong>Date:</strong> January 2025</p>
<hr>

<h2>1. Introduction</h2>
<p>Opening paragraph with context and purpose of this document.</p>

<h2>2. Key Points</h2>
<ul>
  <li><strong>Point one:</strong> Description of the first key point.</li>
  <li><strong>Point two:</strong> Description of the second key point.</li>
  <li><strong>Point three:</strong> Description of the third key point.</li>
</ul>

<h2>3. Data Summary</h2>
<table>
  <tr><th>Category</th><th>Q1</th><th>Q2</th><th>Notes</th></tr>
  <tr><td>Revenue</td><td>$120K</td><td>$145K</td><td>↑ 20.8%</td></tr>
  <tr><td>Expenses</td><td>$80K</td><td>$90K</td><td>↑ 12.5%</td></tr>
</table>

<h2>4. Recommendations</h2>
<ol>
  <li>First recommended action with rationale.</li>
  <li>Second recommended action with rationale.</li>
</ol>

<h2>5. Conclusion</h2>
<p>Summary statement and next steps.</p>

</body>
</html>
```

## Quality Rules

1. **Use semantic headings (h1–h3)** — they map directly to Word's built-in heading styles, enabling automatic Table of Contents.
2. **Tables must have `<tr><th>` headers** — the first row becomes the header row in Word.
3. **Avoid CSS styles** — htmldocx does not process CSS; use HTML structure only.
4. **Keep tables narrow** — Word auto-sizes columns; avoid too many columns (max 6–7 for readability).
5. **Use `<ul>/<ol>` for lists** — do not fake lists with dashes in `<p>` tags.
6. **Do not nest tables** — nested tables are not supported.

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | `true` / `false` |
| `filename` | Final filename |
| `path` | Server-side path |
| `size_bytes` | File size |
