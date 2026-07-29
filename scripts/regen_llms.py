#!/usr/bin/env python3
"""Regenerate llms.txt with accurate, current file counts + samples."""
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/tim/suburb-insights-kb")
MD = REPO / "markdown"

def section_rows(kind):
    rows = []
    for state_dir in sorted((MD / kind).iterdir()):
        if not state_dir.is_dir():
            continue
        files = sorted(p.name for p in state_dir.glob("*.md"))
        rows.append((state_dir.name, files))
    return rows

lines = [
    "# Suburb Insights Knowledge Base",
    "",
    "Markdown profiles for Australian suburbs and schools, optimized for LLM / agent consumption.",
    "Source: suburb-insights.com.au  |  Refresh: as new suburb/school profiles are generated.",
    "",
    "## How to use this index",
    "",
    "1. Each section below groups files by `category/state`.",
    "2. To fetch a file, prefix its path with:",
    "   https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/",
    "3. Sample URL: markdown/suburbs/nsw/truganina-nsw.md",
    "",
    "---",
    "",
]

totals = {"schools": 0, "suburbs": 0}
counts = {}
for kind in ("schools", "suburbs"):
    for state, files in section_rows(kind):
        counts[(kind, state)] = len(files)
        totals[kind] += len(files)
        lines.append(f"### {kind.capitalize()} / {state.upper()} ({len(files)} files)")
        lines.append("")
        lines.append("Samples (fetch full folder via GitHub API if more are needed):")
        for name in files[:5]:
            lines.append(f"- markdown/{kind}/{state}/{name}")
        lines.append("")

lines.append("---")
lines.append("Last regenerated: " + datetime.now(timezone.utc).isoformat())
lines.append("")

(REPO / "llms.txt").write_text("\n".join(lines))
print("llms.txt regenerated:", totals)

# Update README Stats section
readme = (REPO / "README.md").read_text()
import re
sch = {s: c for (k, s), c in counts.items() if k == "schools"}
sub = {s: c for (k, s), c in counts.items() if k == "suburbs"}
stats_lines = (
    f"- Suburbs: {totals[suburbs]} ("
    + ", ".join(f"{s}: {sub[s]}" for s in sorted(sub))
    + ")\n- Schools: " + str(totals["schools"]) + " ("
    + ", ".join(f"{s}: {sch[s]}" for s in sorted(sch)) + ")"
)
new_readme, n = re.subn(
    r"## Stats\n\n- Suburbs:.*\n- Schools:.*",
    f"## Stats\n\n{stats_lines}",
    readme,
    flags=re.S,
)
if n:
    (REPO / "README.md").write_text(new_readme)
    print("README Stats updated")
else:
    print("README Stats pattern not found — llms.txt still updated")
