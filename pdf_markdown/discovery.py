"""PDF discovery helpers — resolve PDFs from folder trees or explicit paths."""

from pathlib import Path


def collect_pdfs_from_folder(folder: Path) -> list[tuple[str, Path]]:
    """Return ``(group, pdf_path)`` pairs for every PDF found directly inside
    ``<folder>/<group>/`` subdirectories.

    A *group* is any immediate subdirectory name (e.g. ``"1880"``, ``"invoices"``).
    PDFs nested more than one level deep are intentionally skipped so the mapping
    remains unambiguous.

    Args:
        folder: Root directory that contains named group sub-folders.

    Returns:
        Sorted list of ``(group_name, path)`` tuples.
    """
    results: list[tuple[str, Path]] = []
    for group_dir in sorted(folder.iterdir()):
        if not group_dir.is_dir():
            continue
        results.extend((group_dir.name, pdf) for pdf in sorted(group_dir.glob("*.pdf")))
    return results


def collect_pdfs_from_groups(
    folder: Path,
    groups: list[str],
) -> list[tuple[str, Path]]:
    """Same as :func:`collect_pdfs_from_folder` but restricted to *groups*.

    Args:
        folder: Root directory.
        groups: Sub-folder names to include.

    Returns:
        Sorted list of ``(group_name, path)`` tuples for the requested groups.

    Raises:
        FileNotFoundError: If any requested group sub-folder does not exist.
    """
    results: list[tuple[str, Path]] = []
    for group in groups:
        group_dir = folder / group
        if not group_dir.is_dir():
            raise FileNotFoundError(
                f"Group folder not found: {group_dir}. Check --source and --groups arguments.",
            )
        results.extend((group, pdf) for pdf in sorted(group_dir.glob("*.pdf")))
    return results


def collect_pdfs_from_inputs(inputs: list[Path]) -> list[tuple[str, Path]]:
    """Resolve explicit ``--input`` paths (files or folders) into ``(group, path)`` pairs.

    * If *input* is a ``*.pdf`` file  → group is its parent folder name.
    * If *input* is a directory       → all ``*.pdf`` files in it (non-recursive),
                                        group is the directory name.

    Args:
        inputs: List of file or directory paths supplied by the user.

    Returns:
        Deduplicated, sorted list of ``(group_name, path)`` tuples.

    Raises:
        FileNotFoundError: If a supplied path does not exist.
        ValueError: If a supplied file exists but is not a PDF.
    """
    seen: set[Path] = set()
    results: list[tuple[str, Path]] = []

    for inp in inputs:
        if not inp.exists():
            raise FileNotFoundError(f"Input path does not exist: {inp}")

        if inp.is_file():
            if inp.suffix.lower() != ".pdf":
                raise ValueError(f"Input file is not a PDF: {inp}")
            if inp not in seen:
                seen.add(inp)
                results.append((inp.parent.name, inp))
        else:
            for pdf in sorted(inp.glob("*.pdf")):
                if pdf not in seen:
                    seen.add(pdf)
                    results.append((inp.name, pdf))

    return results
