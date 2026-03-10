"""Embed and extract PDF metadata in Markdown files.

Metadata is stored as JSON inside an HTML comment at the top of the file,
invisible when rendered but visible when editing the raw Markdown.
"""

import json
import re

__all__ = ["embed_metadata", "extract_metadata"]

_METADATA_PATTERN = re.compile(
    r"^<!--\s*pdf-markdown:metadata\s*\n(.*?)\n-->\s*\n*",
    re.DOTALL,
)


def embed_metadata(metadata: dict[str, str]) -> str:
    """Format metadata for embedding at the top of a Markdown file.

    The result is an HTML comment block, invisible when the Markdown is
    rendered. Use it to prepend to Markdown content before writing.

    Args:
        metadata: Dict of string key-value pairs (e.g. source_file, author,
            title, creationDate). Empty values are omitted from the output.

    Returns:
        A string to prepend to Markdown, including a trailing newline.

    Example:
        >>> embed_metadata({"source_file": "report.pdf", "author": "Jane"})
        '<!-- pdf-markdown:metadata\\n{"author": "Jane", "source_file": "report.pdf"}\\n-->\\n\\n'
    """
    filtered = {k: v for k, v in metadata.items() if v and str(v).strip()}
    if not filtered:
        return ""
    payload = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
    return f"<!-- pdf-markdown:metadata\n{payload}\n-->\n\n"


def extract_metadata(markdown: str) -> tuple[dict[str, str] | None, str]:
    """Extract embedded metadata from Markdown and return the remaining body.

    If no pdf-markdown metadata block is found, returns (None, original_markdown).

    Args:
        markdown: Full Markdown content, possibly with a metadata block at top.

    Returns:
        Tuple of (metadata_dict or None, body_without_metadata).

    Example:
        >>> s = '<!-- pdf-markdown:metadata\\n{"source_file": "x.pdf"}\\n-->\\n\\n# Hi'
        >>> meta, body = extract_metadata(s)
        >>> meta
        {'source_file': 'x.pdf'}
        >>> body
        '# Hi'
    """
    match = _METADATA_PATTERN.match(markdown)
    if not match:
        return None, markdown

    try:
        data = json.loads(match.group(1))
        metadata = {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        metadata = None

    body = markdown[match.end() :]
    return metadata, body
