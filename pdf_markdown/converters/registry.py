"""Converter registry — resolve converter by name from env or CLI."""

from pdf_markdown.converters.base import Converter
from pdf_markdown.converters.marker_converter import MarkerConverter
from pdf_markdown.converters.pymupdf4llm_converter import PyMuPDF4LLMConverter

_REGISTRY: dict[str, Converter] = {
    "marker": MarkerConverter(),
    "pymupdf4llm": PyMuPDF4LLMConverter(),
}

DEFAULT_CONVERTER = "marker"


def get_converter(name: str | None = None) -> Converter:
    """Get converter by name. Falls back to default if name is empty or unknown."""
    key = (name or "").strip().lower()
    if not key or key not in _REGISTRY:
        return _REGISTRY[DEFAULT_CONVERTER]
    return _REGISTRY[key]


def list_converters() -> list[tuple[str, str, bool]]:
    """Return list of (name, description, lightweight) for each available converter."""
    return [(c.name, c.description, c.lightweight) for c in _REGISTRY.values()]
