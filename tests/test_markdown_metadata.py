"""Tests for pdf_markdown.markdown_metadata."""

import json

from pdf_markdown.markdown_metadata import embed_metadata, extract_metadata


def test_embed_metadata_basic() -> None:
    meta = {"source_file": "report.pdf", "author": "Jane Doe"}
    block = embed_metadata(meta)
    assert "<!-- pdf-markdown:metadata" in block
    assert "report.pdf" in block
    assert "Jane Doe" in block
    assert block.endswith("\n\n")


def test_embed_metadata_omits_empty_values() -> None:
    meta = {"source_file": "x.pdf", "author": "", "title": "  "}
    block = embed_metadata(meta)
    parsed = json.loads(block.split("\n")[1])
    assert parsed == {"source_file": "x.pdf"}


def test_embed_metadata_empty_dict_returns_empty_string() -> None:
    assert embed_metadata({}) == ""
    assert embed_metadata({"a": "", "b": ""}) == ""


def test_extract_metadata_roundtrip() -> None:
    meta = {"source_file": "census.pdf", "author": "NBS"}
    body = "# Census 1880\n\nContent here."
    full = embed_metadata(meta) + body
    extracted, remaining = extract_metadata(full)
    assert extracted == meta
    assert remaining == body


def test_extract_metadata_no_block_returns_none_and_original() -> None:
    md = "# Just content\n\nNo metadata."
    meta, body = extract_metadata(md)
    assert meta is None
    assert body == md


def test_extract_metadata_invalid_json_returns_none() -> None:
    md = "<!-- pdf-markdown:metadata\n{invalid json}\n-->\n\n# Hi"
    meta, body = extract_metadata(md)
    assert meta is None
    assert body == "# Hi"


def test_extract_metadata_non_dict_json_returns_none() -> None:
    md = '<!-- pdf-markdown:metadata\n["a", "b"]\n-->\n\n# Hi'
    meta, body = extract_metadata(md)
    assert meta is None
    assert "# Hi" in body
