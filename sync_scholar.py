#!/usr/bin/env python3
"""
Sync publications from a Google Scholar profile into publications.json.

Google Scholar has no official API and rate-limits/bot-blocks scrapers, so this
runs as a scheduled job (see .github/workflows/sync.yml) rather than live in the
browser. The committed publications.json is the source of truth that the website
and the embeddable widget (index.html) read from.

Usage:
    pip install scholarly
    python sync_scholar.py
"""

import datetime
import json
import re
import sys
from pathlib import Path

SCHOLAR_ID = "bRzhctsAAAAJ"
AUTHOR_TAG = "A Renganathan"   # name highlighted in author lists on the page
N_RECENT = 10
OUT_FILE = Path(__file__).with_name("publications.json")

PROFILE_URL = f"https://scholar.google.com/citations?hl=en&user={SCHOLAR_ID}"


def fetch_recent():
    try:
        from scholarly import scholarly
    except ImportError:
        sys.exit("Missing dependency. Run: pip install scholarly")

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    pubs = author["publications"]
    pubs.sort(key=lambda p: int(p["bib"].get("pub_year", 0) or 0), reverse=True)

    out = []
    for p in pubs[:N_RECENT]:
        bib = p["bib"]
        venue = (bib.get("citation") or bib.get("journal") or "").strip()
        url = ""
        m = re.search(r"arXiv:(\d{4}\.\d{4,5})", venue)
        if m:
            url = f"https://arxiv.org/abs/{m.group(1)}"
        out.append({
            "title": bib.get("title", "").strip(),
            "authors": bib.get("author", "").replace(" and ", ", ").strip(),
            "venue": venue,
            "year": str(bib.get("pub_year", "")).strip(),
            "url": url,
        })
    return out


def main():
    pubs = fetch_recent()
    if not pubs:
        sys.exit("No publications fetched; aborting (leaving publications.json untouched).")

    payload = {
        "profileUrl": PROFILE_URL,
        "lastSynced": datetime.date.today().isoformat(),
        "author": AUTHOR_TAG,
        "publications": pubs,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUT_FILE.name} with {len(pubs)} publications.")


if __name__ == "__main__":
    main()
