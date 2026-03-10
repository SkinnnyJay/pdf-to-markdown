"""pdf-markdown — convert PDFs to Markdown using Marker, with image fallback.

Public API
----------
The package can be used as a library as well as a CLI::

    from pdf_markdown.discovery import collect_pdfs_from_folder
    from pdf_markdown.markdown_metadata import embed_metadata, extract_metadata
    from pdf_markdown.models import ConversionResult
    from pdf_markdown.pdf_metadata import get_pdf_metadata
    from pdf_markdown.validation import validate_output_tree
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
