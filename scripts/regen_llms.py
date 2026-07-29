#!/usr/bin/env python3
"""
Regenerate llms.txt index and update README.md Stats for suburb-insights-kb.

Scans the markdown/ directory tree, counts files per category/state,
writes an accurate llms.txt with up to 5 alphabetical samples per section,
and patches the Stats section in README.md.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

KB_DIR = Path.home() / "suburb-insights-kb"
MARKDOWN_DIR = KB_DIR / "markdown"
LLMS_FILE = KB_DIR / "llms.txt"
README_FILE = KB_DIR / "README.md"

# Ordered categories and their display names
CATEGORIES = [
    ("suburbs", "Suburbs"),
    ("schools", "Schools"),
]

# State ordering for display
STATE_ORDER = ["nsw", "qld", "vic", "sa", "wa"]

def collect_files() -> dict:
    """Scan markdown/ and return {(category, state): [sorted filenames]}."""
    files: dict = defaultdict(list)

    if not MARKDOWN_DIR.exists():
        print(f"ERROR: {MARKDOWN_DIR} not found", file=sys.stderr)
        sys.exit(1)

    for cat_dir_name, cat_display in CATEGORIES:
        cat_path = MARKDOWN_DIR / cat_dir_name
        if not cat_path.is_dir():
            continue
        for state_dir in sorted(cat_path.iterdir()):
            if not state_dir.is_dir():
                continue
            state = state_dir.name
            md_files = sorted(
                f.name for f in state_dir.iterdir()
                if f.is_file() and f.suffix == ".md"
            )
            if md_files:
                files[(cat_dir_name, state)] = md_files

    return files

def generate_llms(files: dict) -> str:
    """Generate the full llms.txt content."""
    lines = []
    lines.append("# Suburb Insights Knowledge Base")
    lines.append("")
    lines.append("Markdown profiles for Australian suburbs and schools, optimized for LLM / agent consumption.")
    lines.append("Source: suburb-insights.com.au  |  Refresh: as new suburb/school profiles are generated.")
    lines.append("")
    lines.append("## How to use this index")
    lines.append("")
    lines.append("1. Each section below groups files by `category/state`.")
    lines.append("2. To fetch a file, prefix its path with:")
    lines.append("   https://raw.githubusercontent.com/timmyphang/suburb-insights-kb/main/")
    lines.append("3. Sample URL: markdown/suburbs/nsw/truganina-nsw.md")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat_dir_name, cat_display in CATEGORIES:
        for state in STATE_ORDER:
            key = (cat_dir_name, state)
            if key not in files:
                continue
            md_list = files[key]
            count = len(md_list)
            state_upper = state.upper()
            lines.append(f"### {cat_display} / {state_upper} ({count} files)")
            lines.append("")
            lines.append("Samples (fetch full folder via GitHub API if more are needed):")
            for fname in md_list[:5]:
                lines.append(f"- markdown/{cat_dir_name}/{state}/{fname}")
            lines.append("")

    # Footer
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"Last regenerated: {now_utc}")

    return "\n".join(lines) + "\n"

def update_readme_stats(files: dict):
    """Patch the Stats section in README.md with accurate counts."""
    if not README_FILE.exists():
        print(f"WARNING: {README_FILE} not found, skipping README update")
        return

    content = README_FILE.read_text()

    # Aggregate counts
    suburb_counts = {}
    school_counts = {}
    for (cat, state), md_list in files.items():
        if cat == "suburbs":
            suburb_counts[state] = len(md_list)
        elif cat == "schools":
            school_counts[state] = len(md_list)

    total_suburbs = sum(suburb_counts.values())
    total_schools = sum(school_counts.values())

    # Build the new Stats lines (preserving the existing format)
    suburb_parts = ", ".join(
        f"{st}: {suburb_counts.get(st, 0)}"
        for st in ["nsw", "qld", "sa", "vic", "wa"]
        if st in suburb_counts
    )
    school_parts = ", ".join(
        f"{st}: {school_counts.get(st, 0)}"
        for st in ["nsw", "qld", "vic"]
        if st in school_counts
    )

    new_stats_lines = (
        f"## Stats\n\n"
        f"- Suburbs: {total_suburbs} ({suburb_parts})\n"
        f"- Schools: {total_schools} ({school_parts})\n"
    )

    # Find and replace the Stats section
    import re
    pattern = r"## Stats\n\n- Suburbs:.*\n- Schools:.*\n"
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_stats_lines, content)
    else:
        # Stats section not found — append
        new_content = content.rstrip() + "\n\n" + new_stats_lines

    if new_content != content:
        README_FILE.write_text(new_content)
        print(f"  Updated README.md Stats section")
    else:
        print(f"  README.md Stats already up to date")

def commit_and_push():
    """Stage, commit, and push changes. Non-fatal on push failure."""
    import subprocess

    cmds = [
        (["git", "-C", str(KB_DIR), "add", "-A"], "git add"),
        (
            ["git", "-C", str(KB_DIR), "commit", "-m",
             "Regenerate llms.txt + README stats with accurate counts"],
            "git commit",
        ),
        (["git", "-C", str(KB_DIR), "push"], "git push"),
    ]

    for cmd, label in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Check if it's "nothing to commit" which is fine
            if "nothing to commit" in result.stdout + result.stderr:
                print(f"  {label}: nothing to commit (already up to date)")
                continue
            # Check if push fails with auth — don't crash
            if label == "git push":
                print(f"  WARNING: git push failed (auth or network)")
                print(f"    {result.stderr.strip()}")
                continue
            print(f"  ERROR: {label} failed: {result.stderr.strip()}")
            sys.exit(1)
        else:
            output = result.stdout.strip() or result.stderr.strip()
            if label == "git push":
                print(f"  {label}: OK")
            else:
                print(f"  {label}: {output if output else 'OK'}")

def main():
    print("Scanning markdown directories...")
    files = collect_files()

    # Print what we found
    for (cat, state), md_list in sorted(files.items()):
        print(f"  {cat}/{state}: {len(md_list)} files")

    print(f"\nWriting {LLMS_FILE}...")
    llms_content = generate_llms(files)
    LLMS_FILE.write_text(llms_content)
    print(f"  Wrote {len(llms_content)} bytes")

    print("\nUpdating README.md...")
    update_readme_stats(files)

    print("\nCommitting and pushing...")
    commit_and_push()

    print("\nDone. llms.txt regenerated successfully.")

if __name__ == "__main__":
    main()
