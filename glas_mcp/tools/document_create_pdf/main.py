import asyncio
import base64
import os
from typing import Any, Dict

from glas_mcp.tools.base import BaseTool


class DocumentCreatePdfTool(BaseTool):
    """
    MCP tool that renders HTML + CSS into a PDF using WeasyPrint.
    """

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        from glas_mcp.tools.document_create_pdf.helpers.html_utils import ensure_html_document, inject_css
        html_content: str = arguments.get("html_content", "")
        css: str = arguments.get("css", "")
        filename: str = arguments.get("filename", "document.pdf")
        output_dir: str = arguments.get("output_dir", "./generated_pdfs/")
        return_base64: bool = arguments.get("return_base64", True)

        if not html_content.strip():
            return {"error": "'html_content' is required and must not be empty."}

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            return {"error": f"Could not create output directory '{output_dir}': {e}"}

        output_path = os.path.join(output_dir, filename)

        html = ensure_html_document(html_content)
        html = inject_css(html, css)

        try:
            pdf_bytes: bytes = await asyncio.to_thread(
                self._render_pdf, html
            )
        except Exception as e:
            return {"error": f"WeasyPrint rendering failed: {e}"}

        try:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
        except OSError as e:
            return {"error": f"Could not write PDF to '{output_path}': {e}"}

        result: Dict[str, Any] = {
            "success": True,
            "file_path": os.path.abspath(output_path),
            "filename": filename,
            "size_bytes": len(pdf_bytes),
        }

        if return_base64:
            result["base64"] = base64.b64encode(pdf_bytes).decode("utf-8")

        return result

    @staticmethod
    def _render_pdf(html: str) -> bytes:
        """
        Synchronous WeasyPrint render — called inside a thread so it
        does not block the async event loop.
        """
        import weasyprint
        doc = weasyprint.HTML(string=html)
        return doc.write_pdf()
