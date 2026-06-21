# Skill: document_create_xlsx

**Tool:** `document_create_xlsx`  
**Version:** 1.0.0

## Purpose
Generate Excel (.xlsx) spreadsheets from structured data. Supports multiple sheets, cell formatting, formulas, column widths, and frozen panes using openpyxl.

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `sheets` | array | **required** | Array of sheet definitions |
| `filename` | string | `"spreadsheet.xlsx"` | Output filename |

## Sheet Definition Structure

```json
{
  "sheets": [
    {
      "name": "Sheet name",
      "headers": ["Col A", "Col B", "Col C"],
      "rows": [
        ["value1", 123, "=B2*1.1"],
        ["value2", 456, "=B3*1.1"]
      ],
      "freeze_panes": "A2",
      "col_widths": {"A": 20, "B": 15, "C": 18}
    }
  ]
}
```

## Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Sheet tab name (max 31 chars) |
| `headers` | Yes | Column header row (styled bold/colored automatically) |
| `rows` | Yes | Data rows — can contain strings, numbers, or Excel formulas |
| `freeze_panes` | No | Cell address to freeze above/left of (e.g. `"A2"` freezes header row) |
| `col_widths` | No | Dict of column letter → width in characters |

## Excel Formula Examples

| Formula | Purpose |
|---------|---------|
| `"=SUM(B2:B100)"` | Sum a column range |
| `"=AVERAGE(B2:B100)"` | Average |
| `"=B2*1.1"` | 10% markup |
| `"=IF(C2>1000,\"High\",\"Low\")"` | Conditional |
| `"=VLOOKUP(A2,Sheet2!A:B,2,0)"` | Cross-sheet lookup |
| `"=TEXT(B2,\"$#,##0.00\")"` | Number formatting |

## Multi-Sheet Example

```json
{
  "filename": "financial_report.xlsx",
  "sheets": [
    {
      "name": "Summary",
      "headers": ["Metric", "Q1", "Q2", "Q3", "Q4", "Total"],
      "rows": [
        ["Revenue",  120000, 145000, 160000, 175000, "=SUM(B2:E2)"],
        ["Expenses",  80000,  90000,  95000, 100000, "=SUM(B3:E3)"],
        ["Profit",   "=B2-B3", "=C2-C3", "=D2-D3", "=E2-E3", "=F2-F3"]
      ],
      "freeze_panes": "A2",
      "col_widths": {"A": 18, "B": 12, "C": 12, "D": 12, "E": 12, "F": 14}
    },
    {
      "name": "Raw Data",
      "headers": ["Date", "Product", "Units", "Unit Price", "Revenue"],
      "rows": [
        ["2024-01-15", "Widget A", 500, 24.99, "=C2*D2"],
        ["2024-01-16", "Widget B", 320, 39.99, "=C3*D3"]
      ],
      "freeze_panes": "A2",
      "col_widths": {"A": 14, "B": 16, "C": 10, "D": 12, "E": 14}
    }
  ]
}
```

## Quality Rules

1. **Always freeze the header row** with `"freeze_panes": "A2"` — makes large sheets usable.
2. **Use formulas for computed columns** rather than pre-computing in Python — makes the spreadsheet interactive.
3. **Set `col_widths`** — default column width is often too narrow to read the content.
4. **Sheet names max 31 characters** and cannot contain: `\ / * ? : [ ]`.
5. **Numbers should be numbers** (not strings) so Excel can sort and chart them.
6. **Add a Summary sheet** for multi-sheet workbooks with cross-sheet `SUM` / `AVERAGE` formulas.

## Output Fields

| Field | Description |
|-------|-------------|
| `success` | `true` / `false` |
| `filename` | Final filename |
| `path` | Server-side path |
| `size_bytes` | File size |
| `sheet_count` | Number of sheets created |
