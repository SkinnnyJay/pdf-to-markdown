"""HTML report generator — produces a rich, self-contained report from a RunSummary."""

from __future__ import annotations

import html
from pathlib import Path

from pdf_markdown.models import ConversionResult, RunSummary

__all__ = ["generate_report"]

# Status badge colours (Tailwind classes)
_BADGE: dict[str, str] = {
    "ok": "bg-green-100 text-green-800 border border-green-300",
    "fallback": "bg-yellow-100 text-yellow-800 border border-yellow-300",
    "failed": "bg-red-100 text-red-800 border border-red-300",
}

_STATUS_ICON: dict[str, str] = {
    "ok": "✓",
    "fallback": "⚠",
    "failed": "✗",
}


def _h(value: object) -> str:
    """HTML-escape a value."""
    return html.escape(str(value))


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def _fmt_ts(dt: object) -> str:
    if dt is None:
        return "—"
    try:
        local = dt.astimezone()  # convert UTC → local for display
        return local.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return str(dt)


def _summary_widgets(summary: RunSummary) -> str:
    """Render the four KPI cards at the top of the report."""
    rate_colour = (
        "text-green-600"
        if summary.success_rate >= 90
        else "text-yellow-600"
        if summary.success_rate >= 60
        else "text-red-600"
    )

    def card(label: str, value: str, sub: str = "", colour: str = "text-gray-800") -> str:
        return f"""
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 flex flex-col gap-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</p>
          <p class="text-3xl font-bold {colour}">{value}</p>
          {f'<p class="text-xs text-gray-500">{sub}</p>' if sub else ""}
        </div>"""

    dur = _fmt_duration(summary.duration_s)
    return f"""
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {card("Total PDFs", str(summary.total))}
      {card("Converted OK", str(summary.ok_count), "full Marker output", "text-green-600")}
      {card("Fallback", str(summary.fallback_count), "image extraction used", "text-yellow-600")}
      {card("Failed", str(summary.failed_count), "no output produced", "text-red-600")}
    </div>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
      {card("Success Rate", f"{summary.success_rate:.1f}%", "", rate_colour)}
      {card("Groups", str(len(summary.groups)), ", ".join(summary.groups[:6]))}
      {card("Run Duration", dur)}
    </div>"""


def _result_rows(results: list[ConversionResult], log_path: Path | None) -> str:
    """Render one ``<tr>`` per result, with an expandable error log panel."""
    rows: list[str] = []

    for i, r in enumerate(results):
        status = r.status_label
        badge_cls = _BADGE.get(status, "bg-gray-100 text-gray-800")
        icon = _STATUS_ICON.get(status, "?")
        row_id = f"row-{i}"
        log_id = f"log-{i}"

        md_link = ""
        if r.output_md:
            md_link = (
                f'<a href="{_h(r.output_md)}" class="text-blue-600 hover:underline text-xs">'
                f"{_h(r.output_md.name)}</a>"
            )

        has_log = bool(r.log_text and r.log_text != "(no output captured)")
        expand_btn = ""
        if has_log or r.error:
            expand_btn = (
                f"<button onclick=\"toggleLog('{log_id}')\" "
                f'class="ml-2 text-xs text-gray-400 hover:text-gray-700 underline">logs</button>'
            )

        log_panel = ""
        if has_log or r.error:
            log_content = _h(r.log_text)
            log_panel = f"""
        <tr id="{log_id}" class="hidden bg-gray-50">
          <td colspan="6" class="px-4 py-3">
            <div class="text-xs font-mono text-gray-700 bg-gray-100 rounded-lg p-4
                        overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto
                        border border-gray-200">{log_content}</div>
          </td>
        </tr>"""

        dur_cell = _fmt_duration(r.duration_s)
        imgs_cell = str(len(r.extracted_images)) if r.extracted_images else "—"

        rows.append(f"""
        <tr id="{row_id}" class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
          <td class="px-4 py-3">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs
                         font-semibold {badge_cls}">{icon} {status}</span>
          </td>
          <td class="px-4 py-3 text-sm font-medium text-gray-700">{_h(r.group)}</td>
          <td class="px-4 py-3 text-sm text-gray-600 break-all">
            {_h(r.pdf.name)}{expand_btn}
          </td>
          <td class="px-4 py-3 text-sm">{md_link}</td>
          <td class="px-4 py-3 text-sm text-gray-500 tabular-nums">{dur_cell}</td>
          <td class="px-4 py-3 text-sm text-gray-500 tabular-nums">{imgs_cell}</td>
        </tr>{log_panel}""")

    return "\n".join(rows)


def generate_report(summary: RunSummary, *, title: str = "PDF Conversion Report") -> str:
    """Render a complete, self-contained HTML report for *summary*.

    The returned string is a full ``<!DOCTYPE html>`` document that embeds
    Tailwind CSS and Alpine.js via CDN — no local assets required.

    Args:
        summary: Populated :class:`~pdf_markdown.models.RunSummary`.
        title: Browser title and ``<h1>`` heading for the report.

    Returns:
        HTML string ready to write to a ``.html`` file.
    """
    widgets = _summary_widgets(summary)
    rows = _result_rows(summary.results, summary.log_path)

    log_path_link = (
        f'<a href="{_h(summary.log_path)}" class="underline text-blue-400">'
        f"{_h(summary.log_path)}</a>"
        if summary.log_path
        else "—"
    )

    started = _fmt_ts(summary.started_at)
    finished = _fmt_ts(summary.finished_at)

    groups_str = ", ".join(_h(g) for g in summary.groups) or "—"

    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_h(title)} — {_h(summary.run_name)}</title>

  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Alpine.js for lightweight interactivity -->
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

  <style>
    [x-cloak] {{ display: none !important; }}
    .sort-icon::after {{ content: ' ↕'; opacity: 0.4; }}
    .sort-asc::after  {{ content: ' ↑'; opacity: 1; }}
    .sort-desc::after {{ content: ' ↓'; opacity: 1; }}
  </style>
</head>

<body class="bg-gray-50 text-gray-900 min-h-screen font-sans antialiased">

  <!-- ── Header ─────────────────────────────────────────────────────────── -->
  <header class="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{_h(title)}</h1>
        <p class="text-xs text-gray-500 mt-0.5">
          Run: <code class="font-mono">{_h(summary.run_name)}</code>
        </p>
      </div>
      <div class="text-right text-xs text-gray-400 space-y-0.5">
        <p>Started: {started}</p>
        <p>Finished: {finished}</p>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-6 py-8">

    <!-- ── Summary widgets ──────────────────────────────────────────────── -->
    {widgets}

    <!-- ── Run metadata strip ───────────────────────────────────────────── -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-8
                flex flex-wrap gap-x-8 gap-y-2 text-sm text-gray-600">
      <span><strong class="text-gray-800">Groups:</strong> {groups_str}</span>
      <span><strong class="text-gray-800">Log:</strong> {log_path_link}</span>
    </div>

    <!-- ── Results table ────────────────────────────────────────────────── -->
    <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
         x-data="sortableTable()">

      <!-- Toolbar -->
      <div class="flex flex-wrap items-center justify-between gap-4 px-5 py-4
                  border-b border-gray-100">
        <h2 class="text-base font-semibold text-gray-800">Conversion Results</h2>
        <div class="flex items-center gap-3">
          <!-- Filter by status -->
          <select id="statusFilter"
                  class="text-sm border border-gray-200 rounded-lg px-3 py-1.5
                         bg-gray-50 text-gray-700 focus:outline-none focus:ring-2
                         focus:ring-blue-300"
                  onchange="filterTable()">
            <option value="">All statuses</option>
            <option value="ok">✓ OK</option>
            <option value="fallback">⚠ Fallback</option>
            <option value="failed">✗ Failed</option>
          </select>
          <!-- Search -->
          <input id="searchBox" type="text" placeholder="Search…"
                 class="text-sm border border-gray-200 rounded-lg px-3 py-1.5 w-48
                        bg-gray-50 text-gray-700 focus:outline-none focus:ring-2
                        focus:ring-blue-300"
                 oninput="filterTable()" />
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table id="resultsTable" class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer
                         select-none sort-icon" onclick="sortTable(0)">Status</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer
                         select-none sort-icon" onclick="sortTable(1)">Group</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer
                         select-none sort-icon" onclick="sortTable(2)">PDF File</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600">Output</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer
                         select-none sort-icon" onclick="sortTable(4)">Duration</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600 cursor-pointer
                         select-none sort-icon" onclick="sortTable(5)">Images</th>
            </tr>
          </thead>
          <tbody id="tableBody">
{rows}
          </tbody>
        </table>
      </div>

      <!-- Footer count -->
      <div class="px-5 py-3 border-t border-gray-100 text-xs text-gray-400 text-right">
        <span id="visibleCount"></span>
      </div>
    </div>

  </main>

  <!-- ── Footer ─────────────────────────────────────────────────────────── -->
  <footer class="max-w-7xl mx-auto px-6 py-6 text-xs text-gray-400 text-center">
    Generated by <strong>pdf-markdown</strong> &mdash; run <code>{_h(summary.run_name)}</code>
  </footer>

  <!-- ── JavaScript ─────────────────────────────────────────────────────── -->
  <script>
    // ── Log panel toggle ────────────────────────────────────────────────────
    function toggleLog(id) {{
      const el = document.getElementById(id);
      el.classList.toggle('hidden');
    }}

    // ── Search + filter ─────────────────────────────────────────────────────
    function filterTable() {{
      const query  = document.getElementById('searchBox').value.toLowerCase();
      const status = document.getElementById('statusFilter').value.toLowerCase();
      const tbody  = document.getElementById('tableBody');
      let visible  = 0;

      // Iterate only primary rows (skip log-panel rows which follow each primary row)
      const rows = Array.from(tbody.querySelectorAll('tr[id^="row-"]'));
      rows.forEach(row => {{
        const text      = row.textContent.toLowerCase();
        const statusTd  = row.querySelector('td:first-child span');
        const rowStatus = statusTd ? statusTd.textContent.trim().toLowerCase() : '';

        const matchText   = !query  || text.includes(query);
        const matchStatus = !status || rowStatus.includes(status);

        const show = matchText && matchStatus;
        row.style.display = show ? '' : 'none';

        // Always hide the associated log row when the primary row is hidden
        const logId  = row.id.replace('row-', 'log-');
        const logRow = document.getElementById(logId);
        if (logRow && !show) logRow.classList.add('hidden');

        if (show) visible++;
      }});

      const total = rows.length;
      document.getElementById('visibleCount').textContent =
        visible === total ? `${{total}} rows` : `${{visible}} of ${{total}} rows`;
    }}

    // ── Column sorting ──────────────────────────────────────────────────────
    let _sortCol = -1;
    let _sortAsc = true;

    function sortTable(colIdx) {{
      const tbody = document.getElementById('tableBody');
      // Collect only primary rows (not log-panel rows)
      const primaryRows = Array.from(tbody.querySelectorAll('tr[id^="row-"]'));

      _sortAsc = (_sortCol === colIdx) ? !_sortAsc : true;
      _sortCol = colIdx;

      primaryRows.sort((a, b) => {{
        const aVal = (a.querySelectorAll('td')[colIdx]?.textContent || '').trim();
        const bVal = (b.querySelectorAll('td')[colIdx]?.textContent || '').trim();
        const cmp  = aVal.localeCompare(bVal, undefined, {{ numeric: true, sensitivity: 'base' }});
        return _sortAsc ? cmp : -cmp;
      }});

      // Re-append each primary row immediately followed by its log panel
      primaryRows.forEach(row => {{
        const logId  = row.id.replace('row-', 'log-');
        const logRow = document.getElementById(logId);
        tbody.appendChild(row);
        if (logRow) tbody.appendChild(logRow);
      }});

      // Update sort icons in headers
      document.querySelectorAll('thead th').forEach((th, i) => {{
        th.classList.remove('sort-asc', 'sort-desc', 'sort-icon');
        if (i === colIdx) {{
          th.classList.add(_sortAsc ? 'sort-asc' : 'sort-desc');
        }} else if (th.onclick) {{
          th.classList.add('sort-icon');
        }}
      }});
    }}

    // ── Init ────────────────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => filterTable());
  </script>
</body>
</html>"""
