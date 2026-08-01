#!/usr/bin/env python3
"""Publish suburb posts from /tmp/suburb_posts_sync to the KB repo.

Reads:  /tmp/suburb_posts_sync/*.json (downloaded by sync_posts.py)
Writes: ~/suburb-insights-kb/markdown/suburbs/{state}/{slug}.md

Each post JSON has keys: suburb, slug, post, generated_at.
The slug encodes state: e.g. 'abbotsford-vic', 'toorak-vic'.

Output markdown format (matches existing KB files):
  # {Suburb} ({STATE})
  Slug: `{slug}`

  {post body}

Usage:
  python3 publish_posts_to_kb.py [--state vic]   # default: all states
"""
import json
import os
import re
import sys
from pathlib import Path

SRC_DIR = Path("/tmp/suburb_posts_sync")
KB_SUBURBS = Path("/home/tim/suburb-insights-kb/markdown/suburbs")
FILTER_STATE = None
for a in sys.argv[1:]:
    if a.startswith("--state="):
        FILTER_STATE = a.split("=", 1)[1].lower()
    elif a == "--state":
        pass
    elif not a.startswith("-"):
        FILTER_STATE = a.lower()


def slug_to_state(slug: str) -> str | None:
    """Extract state code from slug suffix. Returns 'vic'/'nsw'/'qld' or None."""
    for s in ("vic", "nsw", "qld", "sa", "wa", "act", "tas", "nt"):
        if slug.endswith("-" + s):
            return s
    return None


def slug_to_suburb_name(slug: str) -> str:
    """Convert 'abbotsford-vic' → 'Abbotsford'."""
    state = slug_to_state(slug)
    base = slug[: -(len(state) + 1)] if state else slug
    return " ".join(w.capitalize() for w in base.split("-"))


def main():
    if not SRC_DIR.exists():
        print(f"ERROR: {SRC_DIR} not found. Run sync_posts.py first.")
        sys.exit(1)

    files = sorted(SRC_DIR.glob("*.json"))
    print(f"Source posts: {len(files)}")

    written = 0
    skipped_exist = 0
    skipped_empty = 0
    skipped_state = 0
    by_state: dict[str, int] = {}

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR reading {f.name}: {e}")
            continue
        slug = data.get("slug") or f.stem
        post = data.get("post") or ""
        if not post or len(post) < 200:
            skipped_empty += 1
            continue
        state = slug_to_state(slug)
        if state is None:
            skipped_state += 1
            continue
        if FILTER_STATE and state != FILTER_STATE:
            continue
        # Write to KB
        state_dir = KB_SUBURBS / state
        state_dir.mkdir(parents=True, exist_ok=True)
        out = state_dir / f"{slug}.md"
        if out.exists():
            skipped_exist += 1
            continue
        name = slug_to_suburb_name(slug)
        state_up = state.upper()
        md = f"# {name} ({state_up})\n\nSlug: `{slug}`\n\n{post}\n"
        out.write_text(md, encoding="utf-8")
        written += 1
        by_state[state] = by_state.get(state, 0) + 1

    print(f"\nWritten: {written}")
    print(f"Skipped (already exist): {skipped_exist}")
    print(f"Skipped (empty/short post): {skipped_empty}")
    print(f"Skipped (no state / filtered): {skipped_state}")
    print("\nBy state:")
    for s, c in sorted(by_state.items()):
        print(f"  {s.upper()}: {c} new files")

    # Print totals per state dir
    print("\n=== Total KB suburb files by state ===")
    for sdir in sorted(KB_SUBURBS.iterdir()):
        if sdir.is_dir():
            total = len(list(sdir.glob("*.md")))
            print(f"  {sdir.name.upper()}: {total}")


if __name__ == "__main__":
    main()
