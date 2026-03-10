"""pdf-markdown CLI — convert PDFs to Markdown using Marker with image fallback."""

import tempfile
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from pdf_markdown import __version__
from pdf_markdown.config import Settings
from pdf_markdown.discovery import (
    collect_pdfs_from_folder,
    collect_pdfs_from_groups,
    collect_pdfs_from_inputs,
)
from pdf_markdown.fallback_images import extract_images, generate_placeholder_markdown
from pdf_markdown.markdown_metadata import embed_metadata
from pdf_markdown.marker_runner import find_marker_output, run_marker
from pdf_markdown.models import ConversionResult, RunSummary
from pdf_markdown.output import assets_dir, copy_marker_output, destination_md, write_markdown
from pdf_markdown.pdf_metadata import get_pdf_metadata
from pdf_markdown.report import generate_report
from pdf_markdown.run_logger import make_run_name, read_run_log, write_run_log
from pdf_markdown.validation import validate_output_tree

_SECS_PER_MINUTE = 60

app = typer.Typer(
    name="pdf-markdown",
    help=(
        "Convert PDFs to Markdown using Marker, with automatic image-extraction fallback.\n\n"
        "PDFs can be supplied via a [bold]--source[/bold] folder tree "
        "(organised as <source>/<group>/*.pdf) or as explicit [bold]--input[/bold] "
        "paths to files or directories."
    ),
    rich_markup_mode="rich",
    add_completion=True,
)

# stderr for progress / status messages; stdout for structured output (dry-run tables).
console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pdf-markdown {__version__}")
        raise typer.Exit


@app.callback()
def _global(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            is_eager=True,
            callback=_version_callback,
            help="Print version and exit.",
        ),
    ] = None,
) -> None:
    """Entry point for app-level flags (e.g. --version)."""


# ── convert ───────────────────────────────────────────────────────────────────


@app.command()
def convert(
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            "-s",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help=(
                "Root directory whose sub-folders are treated as named groups. "
                "Each group may hold any number of PDFs. "
                "Example: --source ./archive  (containing 1880/, 1890/, …)"
            ),
        ),
    ] = None,
    groups: Annotated[
        str | None,
        typer.Option(
            "--groups",
            "-g",
            help=(
                "Comma-separated list of group names to process when using --source. "
                "If omitted, all sub-folders in --source are processed. "
                "Example: --groups 1880,1890,1900"
            ),
        ),
    ] = None,
    inputs: Annotated[
        list[Path] | None,
        typer.Option(
            "--input",
            "-i",
            resolve_path=True,
            help=(
                "Explicit path to a PDF file or a folder of PDFs. "
                "Can be repeated. Example: --input ./1880/foo.pdf --input ./docs/"
            ),
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            resolve_path=True,
            help="Root directory where converted Markdown is written.",
        ),
    ] = Path("transformed"),
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            "-w",
            min=1,
            help="Number of parallel workers. Default from PDF_MARKDOWN_WORKERS (1).",
        ),
    ] = None,
    batch_multiplier: Annotated[
        int,
        typer.Option(
            "--batch-multiplier",
            help="Marker batch multiplier. Higher values use more RAM/VRAM.",
            min=1,
            max=16,
            hidden=True,
        ),
    ] = 2,
    langs: Annotated[
        str | None,
        typer.Option(
            "--langs",
            help="Comma-separated language hints for Marker (e.g. English,German).",
            hidden=True,
        ),
    ] = None,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            help="Per-file Marker timeout in seconds.",
            min=10,
        ),
    ] = 600,
    model_path: Annotated[
        Path | None,
        typer.Option(
            "--model-path",
            help="Path to HuggingFace model cache. Overrides PDF_MARKDOWN_MODEL_PATH.",
            resolve_path=True,
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Discover files and print what would be processed; do not convert.",
        ),
    ] = False,
    run_name: Annotated[
        str | None,
        typer.Option(
            "--run-name",
            help="Custom name for this run (used in log/report paths). Auto-generated if omitted.",
        ),
    ] = None,
    html_report: Annotated[
        bool,
        typer.Option(
            "--html-report/--no-html-report",
            help="Generate an HTML report after conversion.",
        ),
    ] = True,
) -> None:
    """Convert one or more PDFs to Markdown.

    [bold]Modes:[/bold]

    [green]1.[/green] Process a folder tree by group:
       [dim]pdf-markdown convert --source ./archive --groups 1880,1890[/dim]

    [green]2.[/green] Process all groups in a folder:
       [dim]pdf-markdown convert --source ./archive[/dim]

    [green]3.[/green] Process explicit files or folders:
       [dim]pdf-markdown convert --input ./1880/report.pdf --input ./1890/[/dim]

    Output is written to [bold]<output>/<group>/<filename>.md[/bold].
    If Marker fails, images are extracted and a placeholder Markdown is created.
    A run log is saved to [bold]data/runs/<run-name>/output.log[/bold].
    """
    if source is None and not inputs:
        console.print(
            "[bold red]Error:[/bold red] Provide --source and/or --input.",
            highlight=False,
        )
        raise typer.Exit(code=1)

    pdf_pairs = _collect_pdfs(source, groups, inputs)

    if not pdf_pairs:
        console.print("[yellow]No PDFs found to process.[/yellow]")
        raise typer.Exit

    if dry_run:
        _print_discovery_table(pdf_pairs, output)
        raise typer.Exit

    cfg = Settings()
    name = run_name or make_run_name("convert")
    num_workers = workers if workers is not None else cfg.workers
    mp = model_path or cfg.model_path

    model_line = f"  Model: [bold]{mp!s}[/bold]" if mp else ""
    run_info = (
        f"[dim]Run name: [bold]{name}[/bold]  Workers: [bold]{num_workers}[/bold]{model_line}[/dim]"
    )
    console.print(
        Panel(
            f"[bold]pdf-markdown[/bold]  v{__version__}\n"
            f"[dim]Found [bold]{len(pdf_pairs)}[/bold] PDF(s) → [bold]{output!s}[/bold][/dim]\n"
            f"{run_info}",
            border_style="cyan",
        ),
    )

    started = datetime.now(tz=UTC)
    results = _run_conversions(
        pdf_pairs,
        output,
        batch_multiplier=batch_multiplier,
        langs=langs,
        timeout=timeout,
        workers=num_workers,
        model_path=mp,
    )
    finished = datetime.now(tz=UTC)

    summary = RunSummary(
        run_name=name,
        started_at=started,
        finished_at=finished,
        results=results,
        log_path=cfg.log_path(name),
    )

    write_run_log(summary, summary.log_path)
    console.print(f"[dim]Run log saved → {summary.log_path!s}[/dim]")

    if html_report:
        rpt_path = cfg.report_path(name)
        html_str = generate_report(summary, title=cfg.report_title)
        rpt_path.parent.mkdir(parents=True, exist_ok=True)
        rpt_path.write_text(html_str, encoding="utf-8")
        summary.report_path = rpt_path
        console.print(f"[dim]HTML report → {rpt_path!s}[/dim]")
        if cfg.open_report:
            webbrowser.open(rpt_path.as_uri())

    _print_summary(results)

    if any(not r.success for r in results):
        raise typer.Exit(code=1)


# ── validate ──────────────────────────────────────────────────────────────────


@app.command()
def validate(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Root output directory to validate (e.g. ./transformed).",
        ),
    ],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Fail if any referenced image in a placeholder .md is missing.",
        ),
    ] = False,
) -> None:
    """Validate converted Markdown output under the output directory.

    Checks each ``.md`` file for:

    * Non-empty content.
    * Correct UTF-8 encoding.
    * (Strict mode) All image references resolve to existing files.

    Exits with code 1 if any errors are found.
    """
    issues = validate_output_tree(output, strict=strict)

    if not issues:
        console.print(f"[green]✓ All files valid in {output!s}[/green]")
        return

    table = Table(title=f"Validation Issues in {output}", show_lines=True)
    table.add_column("Severity", no_wrap=True)
    table.add_column("File", style="dim")
    table.add_column("Issue")

    for issue in issues:
        colour = "red" if issue["severity"] == "error" else "yellow"
        table.add_row(
            f"[{colour}]{issue['severity']}[/{colour}]",
            issue["file"],
            issue["message"],
        )

    console.print(table)

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    if errors:
        console.print(f"\n[red]Found {len(errors)} error(s), {len(warnings)} warning(s).[/red]")
        raise typer.Exit(code=1)
    console.print(f"\n[yellow]Found {len(warnings)} warning(s) (no errors).[/yellow]")


# ── report ────────────────────────────────────────────────────────────────────


@app.command()
def report(
    log: Annotated[
        Path | None,
        typer.Option(
            "--log",
            "-l",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help="Path to a specific output.log file to render.",
        ),
    ] = None,
    run_name: Annotated[
        str | None,
        typer.Option(
            "--run-name",
            help="Run name whose log to render (looked up in the data directory).",
        ),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(
            "--out",
            resolve_path=True,
            help="Destination for the report HTML. Defaults to <run_dir>/report.html.",
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            help="Override the report title (falls back to PDF_MARKDOWN_REPORT_TITLE or default).",
        ),
    ] = None,
    open_browser: Annotated[
        bool,
        typer.Option(
            "--open/--no-open",
            help="Open the report in the browser after generation.",
        ),
    ] = False,
    list_runs: Annotated[
        bool,
        typer.Option(
            "--list",
            help="List all available runs in the data directory and exit.",
        ),
    ] = False,
) -> None:
    """Generate (or re-generate) an HTML report from a past conversion run.

    [bold]Usage:[/bold]

    [green]From a run name:[/green]
      [dim]pdf-markdown report --run-name convert-2026-03-09T14-05-32[/dim]

    [green]From an explicit log file:[/green]
      [dim]pdf-markdown report --log ./data/runs/my-run/output.log[/dim]

    [green]List all recorded runs:[/green]
      [dim]pdf-markdown report --list[/dim]
    """
    cfg = Settings()

    if list_runs:
        _print_run_list(cfg)
        raise typer.Exit

    log_path: Path | None = log
    if log_path is None and run_name:
        log_path = cfg.log_path(run_name)
    elif log_path is None:
        log_path = _latest_log(cfg)
        if log_path is None:
            console.print(
                "[yellow]No runs found in data directory. Run a conversion first.[/yellow]",
            )
            raise typer.Exit
        console.print(f"[dim]No run specified — using most recent: {log_path!s}[/dim]")

    try:
        summary = read_run_log(log_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    report_title = title or cfg.report_title
    html_content = generate_report(summary, title=report_title)

    dest = out or cfg.report_path(summary.run_name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_content, encoding="utf-8")

    console.print(f"[green]✓ Report written → {dest!s}[/green]")

    if open_browser or cfg.open_report:
        webbrowser.open(dest.as_uri())


# ── Internal helpers ──────────────────────────────────────────────────────────


def _collect_pdfs(
    source: Path | None,
    groups: str | None,
    inputs: list[Path] | None,
) -> list[tuple[str, Path]]:
    """Resolve all PDF inputs into ``(group, path)`` pairs."""
    pdf_pairs: list[tuple[str, Path]] = []

    if source:
        try:
            if groups:
                group_list = [g.strip() for g in groups.split(",") if g.strip()]
                pdf_pairs += collect_pdfs_from_groups(source, group_list)
            else:
                pdf_pairs += collect_pdfs_from_folder(source)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

    if inputs:
        try:
            pdf_pairs += collect_pdfs_from_inputs(inputs)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

    return pdf_pairs


def _run_conversions(
    pdf_pairs: list[tuple[str, Path]],
    output: Path,
    *,
    batch_multiplier: int,
    langs: str | None,
    timeout: int,
    workers: int = 1,
    model_path: Path | None = None,
) -> list[ConversionResult]:
    """Convert all PDFs, optionally in parallel, with a Rich progress bar."""
    results: list[ConversionResult] = []

    def _convert_with_worker(
        item: tuple[int, tuple[str, Path]],
    ) -> ConversionResult:
        worker_id, (group, pdf) = item
        return _convert_one(
            group=group,
            pdf=pdf,
            output=output,
            batch_multiplier=batch_multiplier,
            langs=langs,
            timeout=timeout,
            model_path=model_path,
            worker_id=worker_id if workers > 1 else None,
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Converting…", total=len(pdf_pairs))

        if workers <= 1:
            for group, pdf in pdf_pairs:
                progress.update(task, description=f"[cyan]{group}/{pdf.name}")
                result = _convert_with_worker((1, (group, pdf)))
                results.append(result)
                progress.advance(task)
        else:
            indexed = [(i % workers + 1, pair) for i, pair in enumerate(pdf_pairs)]
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_convert_with_worker, item): item for item in indexed}
                for future in as_completed(futures):
                    worker_id, (group, pdf) = futures[future]
                    results.append(future.result())
                    progress.update(
                        task,
                        description=f"[cyan]worker {worker_id}: {group}/{pdf.name}",
                        advance=1,
                    )

    # Preserve input order for summary table and logs
    order_map = {(g, str(p)): i for i, (g, p) in enumerate(pdf_pairs)}
    results.sort(key=lambda r: order_map.get((r.group, str(r.pdf)), 0))
    return results


def _convert_one(
    *,
    group: str,
    pdf: Path,
    output: Path,
    batch_multiplier: int,
    langs: str | None,
    timeout: int,
    model_path: Path | None = None,
    worker_id: int | None = None,
) -> ConversionResult:
    """Run Marker for one PDF; fall back to image extraction on failure."""
    dest = destination_md(output, group, pdf)
    a_dir = assets_dir(output, group, pdf)
    stdout = ""
    stderr = ""
    error = ""

    t0 = time.monotonic()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        success, stdout, stderr = run_marker(
            pdf,
            tmp_path,
            batch_multiplier=batch_multiplier,
            langs=langs,
            timeout=timeout,
            model_path=model_path,
        )

        if success:
            marker_md = find_marker_output(tmp_path, pdf.stem)
            if marker_md:
                copy_marker_output(marker_md, dest, pdf)
                return ConversionResult(
                    pdf=pdf,
                    group=group,
                    success=True,
                    output_md=dest,
                    stdout=stdout,
                    stderr=stderr,
                    duration_s=time.monotonic() - t0,
                    worker_id=worker_id,
                )
            success = False
            error = "Marker exited 0 but produced no .md output."
        else:
            error = stderr or "Marker returned a non-zero exit code."

    try:
        images = extract_images(pdf, a_dir)
    except Exception as exc:  # noqa: BLE001
        images = []
        error = f"{error} | Image extraction also failed: {exc}"

    md_content = generate_placeholder_markdown(
        pdf=pdf,
        assets_dir=a_dir,
        images=images,
        error_msg=error,
    )
    metadata = get_pdf_metadata(pdf)
    full_content = embed_metadata(metadata) + md_content
    write_markdown(dest, full_content)

    return ConversionResult(
        pdf=pdf,
        group=group,
        success=False,
        is_fallback=True,
        output_md=dest,
        stdout=stdout,
        stderr=stderr,
        error=error,
        extracted_images=images,
        duration_s=time.monotonic() - t0,
        worker_id=worker_id,
    )


def _print_discovery_table(pdf_pairs: list[tuple[str, Path]], output: Path) -> None:
    typer.echo(f"{'Group':<12}  {'Source PDF':<60}  Output")
    typer.echo("-" * 120)
    for group, pdf in pdf_pairs:
        dest = destination_md(output, group, pdf)
        typer.echo(f"{group:<12}  {pdf!s:<60}  {dest!s}")
    typer.echo(f"\nTotal: {len(pdf_pairs)} PDF(s) would be processed.")


def _print_summary(results: list[ConversionResult]) -> None:
    ok = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    show_worker = any(r.worker_id is not None for r in results)

    table = Table(title="Conversion Summary", show_lines=True)
    table.add_column("Status", style="bold", no_wrap=True)
    if show_worker:
        table.add_column("Worker", style="dim", no_wrap=True)
    table.add_column("Group", style="cyan", no_wrap=True)
    table.add_column("File", style="white")
    table.add_column("Output", style="dim")
    table.add_column("Duration", style="dim", no_wrap=True)

    def _row(r: ConversionResult, status: str) -> list[str]:
        base = [status, r.group, r.pdf.name, str(r.output_md or ""), _fmt_dur(r.duration_s)]
        if show_worker:
            wid = str(r.worker_id or "—")
            return [
                status,
                wid,
                r.group,
                r.pdf.name,
                str(r.output_md or ""),
                _fmt_dur(r.duration_s),
            ]
        return base

    for r in ok:
        row = _row(r, "[green]✓ OK[/green]")
        table.add_row(*row)
    for r in failed:
        label = "[yellow]⚠ fallback[/yellow]" if r.is_fallback else "[red]✗ failed[/red]"
        row = _row(r, label)
        table.add_row(*row)
        if r.error:
            pad = ["", ""] if show_worker else [""]
            table.add_row("", *pad, f"[dim]{r.error}[/dim]", "", "")

    console.print(table)
    console.print(
        f"\n[bold]Total:[/bold] {len(results)}  "
        f"[green]OK: {len(ok)}[/green]  "
        f"[yellow]Fallback/Failed: {len(failed)}[/yellow]\n",
    )


def _fmt_dur(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < _SECS_PER_MINUTE:
        return f"{seconds:.1f}s"
    return f"{int(seconds // _SECS_PER_MINUTE)}m {int(seconds % _SECS_PER_MINUTE)}s"


def _print_run_list(cfg: Settings) -> None:
    runs_dir = cfg.data_dir / cfg.log_subdir
    if not runs_dir.is_dir():
        console.print(f"[yellow]No data directory found at {runs_dir!s}[/yellow]")
        return

    logs = sorted(runs_dir.rglob("output.log"), reverse=True)
    if not logs:
        console.print("[yellow]No run logs found.[/yellow]")
        return

    table = Table(title="Available Runs", show_lines=True)
    table.add_column("Run Name", style="cyan")
    table.add_column("Log Path", style="dim")
    table.add_column("Report")

    for log_file in logs:
        name = log_file.parent.name
        report_file = log_file.parent / "report.html"
        rpt = "[green]✓[/green]" if report_file.exists() else "[dim]—[/dim]"
        table.add_row(name, str(log_file), rpt)

    console.print(table)


def _latest_log(cfg: Settings) -> Path | None:
    runs_dir = cfg.data_dir / cfg.log_subdir
    if not runs_dir.is_dir():
        return None
    logs = sorted(runs_dir.rglob("output.log"), reverse=True)
    return logs[0] if logs else None


if __name__ == "__main__":
    app()
