from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag


def parse_slides(html: str) -> List[Dict[str, Any]]:
    """
    Convert HTML into a list of slide dicts. Slide boundaries are detected by:
      1. <section> tags  (preferred — explicit slide per section)
      2. <h1> or <h2>   (fallback — new slide on each top-level heading)

    Each slide dict:
      {
        "title":   str,
        "bullets": List[str],
        "body":    str,          # plain paragraph text (joined)
        "table":   Optional[Dict]  # {"headers": [...], "rows": [[...]]}
      }
    """
    soup = BeautifulSoup(html, "html.parser")

    sections = soup.find_all("section")
    if sections:
        return [_parse_section(s) for s in sections]

    return _parse_heading_based(soup)


def _parse_section(section: Tag) -> Dict[str, Any]:
    title = ""
    for tag in ("h1", "h2", "h3"):
        el = section.find(tag)
        if el:
            title = el.get_text(strip=True)
            el.decompose()
            break

    return _extract_content(section, title)


def _parse_heading_based(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    slides: List[Dict[str, Any]] = []
    current_title = ""
    current_nodes: List[Tag] = []

    for el in soup.find_all(True):
        if el.parent.name in ("head", "html", "[document]"):
            continue
        if el.name in ("h1", "h2"):
            if current_nodes or current_title:
                slides.append(_build_slide(current_title, current_nodes))
            current_title = el.get_text(strip=True)
            current_nodes = []
        elif el.name in ("p", "ul", "ol", "table") and el.parent == soup:
            current_nodes.append(el)

    if current_title or current_nodes:
        slides.append(_build_slide(current_title, current_nodes))

    return slides or [{"title": "", "bullets": [], "body": "", "table": None}]


def _build_slide(title: str, nodes: List[Tag]) -> Dict[str, Any]:
    bullets: List[str] = []
    paragraphs: List[str] = []
    table = None

    for node in nodes:
        if node.name in ("ul", "ol"):
            bullets.extend(
                li.get_text(strip=True)
                for li in node.find_all("li")
                if li.get_text(strip=True)
            )
        elif node.name == "p":
            text = node.get_text(strip=True)
            if text:
                paragraphs.append(text)
        elif node.name == "table":
            table = _extract_table(node)

    return {
        "title": title,
        "bullets": bullets,
        "body": "\n".join(paragraphs),
        "table": table,
    }


def _extract_content(container: Tag, title: str) -> Dict[str, Any]:
    nodes = [el for el in container.find_all(True) if el.name in ("p", "ul", "ol", "table")]
    return _build_slide(title, nodes)


def _extract_table(table: Tag) -> Dict[str, Any]:
    headers: List[str] = []
    rows: List[List[str]] = []

    thead = table.find("thead")
    if thead:
        tr = thead.find("tr")
        if tr:
            headers = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]

    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if any(cells):
            rows.append(cells)

    return {"headers": headers, "rows": rows}
