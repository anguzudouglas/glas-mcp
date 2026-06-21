def inject_css(html: str, css: str) -> str:
    """
    Injects extra CSS into an HTML string.
    - If a </head> tag is present, the <style> block is inserted before it.
    - Otherwise the style block is prepended to the document.
    """
    if not css.strip():
        return html

    style_block = f"<style>\n{css}\n</style>"

    if "</head>" in html:
        return html.replace("</head>", f"{style_block}\n</head>", 1)

    return f"{style_block}\n{html}"


def ensure_html_document(html: str) -> str:
    """
    Wraps a bare HTML fragment in a minimal HTML5 document shell
    if no <html> tag is detected, so WeasyPrint always receives a
    well-formed document.
    """
    if "<html" in html.lower():
        return html

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
{html}
</body>
</html>"""
