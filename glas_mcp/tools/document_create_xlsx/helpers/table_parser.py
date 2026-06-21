from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag


def parse_tables(html: str) -> List[Dict[str, Any]]:
    """
    Extract all <table> elements from HTML and return a list of table dicts.

    Each dict has:
      - sheet_name (str): from <caption>, nearest preceding h1-h3, or "Sheet N"
      - headers (List[str]): column names from <thead> or first <tr>
      - rows (List[List[str]]): data rows from <tbody> or remaining <tr>s
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    if not tables:
        return []

    result = []
    for idx, table in enumerate(tables, start=1):
        sheet_name = _resolve_sheet_name(table, idx)
        headers, rows = _extract_headers_and_rows(table)
        result.append({
            "sheet_name": _sanitize_sheet_name(sheet_name),
            "headers": headers,
            "rows": rows,
        })
    return result


def _resolve_sheet_name(table: Tag, idx: int) -> str:
    caption = table.find("caption")
    if caption and caption.get_text(strip=True):
        return caption.get_text(strip=True)

    for sibling in table.previous_siblings:
        if isinstance(sibling, Tag) and sibling.name in ("h1", "h2", "h3"):
            text = sibling.get_text(strip=True)
            if text:
                return text
        if isinstance(sibling, Tag):
            break

    return f"Sheet {idx}"


def _extract_headers_and_rows(table: Tag):
    thead = table.find("thead")
    tbody = table.find("tbody")

    headers: List[str] = []
    rows: List[List[str]] = []

    if thead:
        header_row = thead.find("tr")
        if header_row:
            headers = [
                cell.get_text(strip=True)
                for cell in header_row.find_all(["th", "td"])
            ]

    body_source = tbody if tbody else table
    data_rows = body_source.find_all("tr")

    if not headers and data_rows:
        first_row = data_rows[0]
        headers = [cell.get_text(strip=True) for cell in first_row.find_all(["th", "td"])]
        data_rows = data_rows[1:]

    for tr in data_rows:
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
        if any(cells):
            rows.append(cells)

    return headers, rows


def _sanitize_sheet_name(name: str) -> str:
    invalid = r"\/*?:[]"
    for ch in invalid:
        name = name.replace(ch, "")
    return name[:31] or "Sheet"
