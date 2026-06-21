import asyncio
import base64
import io
import os
from typing import Any, Dict

from glas_mcp.tools.base import BaseTool

_SUPPORTED_TAGS = frozenset([
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "b", "strong", "i", "em", "u",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td",
    "br", "hr",
])


class DocumentCreateDocxTool(BaseTool):
    """
    MCP tool that converts HTML into a DOCX file using python-docx + htmldocx.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        from docx import Document
        from docx.shared import Pt
        from htmldocx import HtmlToDocx
        from glas_mcp.tools.document_create_docx.helpers.html_cleaner import sanitize_for_htmldocx
        # ── Input validation ────────────────────────────────────────────────
        if not isinstance(arguments, dict):
            return {"error": "Arguments must be a JSON object."}

        html_content: str = arguments.get("html_content", "")
        if not isinstance(html_content, str) or not html_content.strip():
            return {"error": "'html_content' is required and must be a non-empty string."}

        title: str = str(arguments.get("title", "")).strip()
        filename: str = str(arguments.get("filename", "document.docx")).strip()
        output_dir: str = str(arguments.get("output_dir", "./generated_docs/")).strip()
        return_base64: bool = bool(arguments.get("return_base64", True))

        if not filename:
            filename = "document.docx"
        if not filename.lower().endswith(".docx"):
            filename += ".docx"

        if not output_dir:
            output_dir = "./generated_docs/"

        # ── Create output directory ─────────────────────────────────────────
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            return {"error": f"Cannot create output directory '{output_dir}': {exc}"}

        output_path = os.path.join(output_dir, filename)

        # ── Build document ──────────────────────────────────────────────────
        try:
            docx_bytes = await asyncio.to_thread(
                self._build_docx, html_content, title
            )
        except Exception as exc:
            return {
                "error": f"DOCX generation failed: {exc}",
                "hint": (
                    "Ensure html_content contains valid HTML. "
                    "Supported tags: headings (h1–h6), p, b/strong, i/em, u, "
                    "ul/ol/li, table/thead/tbody/tr/th/td."
                ),
            }

        # ── Write to disk ───────────────────────────────────────────────────
        try:
            with open(output_path, "wb") as fh:
                fh.write(docx_bytes)
        except OSError as exc:
            return {"error": f"Cannot write DOCX to '{output_path}': {exc}"}

        result: Dict[str, Any] = {
            "success": True,
            "file_path": os.path.abspath(output_path),
            "filename": filename,
            "size_bytes": len(docx_bytes),
        }
        if return_base64:
            result["base64"] = base64.b64encode(docx_bytes).decode("utf-8")

        return result

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _build_docx(html: str, title: str) -> bytes:
        doc = Document()

        if title:
            heading = doc.add_heading(title, level=0)
            heading.runs[0].font.size = Pt(24)

        clean_html = sanitize_for_htmldocx(html)

        parser = HtmlToDocx()
        parser.add_html_to_document(clean_html, doc)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
