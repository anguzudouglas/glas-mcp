import re


# Tags htmldocx cannot handle — strip the tag but keep inner text
_UNSUPPORTED_INLINE = re.compile(
    r"<(span|div|section|article|header|footer|nav|aside|figure|figcaption)"
    r"(\s[^>]*)?>",
    re.IGNORECASE,
)
_UNSUPPORTED_INLINE_CLOSE = re.compile(
    r"</(span|div|section|article|header|footer|nav|aside|figure|figcaption)>",
    re.IGNORECASE,
)


def sanitize_for_htmldocx(html: str) -> str:
    """
    Lightweight cleanup so htmldocx doesn't choke on unsupported tags.
    - Strips wrapper/layout tags but keeps their inner content.
    - Normalises newlines.
    """
    html = _UNSUPPORTED_INLINE.sub("", html)
    html = _UNSUPPORTED_INLINE_CLOSE.sub("", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()
