#!/usr/bin/env python3
"""
Sync publications from a Google Scholar profile into publications.json.

Google Scholar has no official API and blocks datacenter IPs (so the `scholarly`
scraper fails from GitHub Actions runners). This script therefore supports two
backends:

  1. SerpAPI (recommended, reliable in CI) -- used when SERPAPI_API_KEY is set.
     Free tier covers ~100 searches/month; a weekly sync needs ~4.
  2. scholarly (no key, best-effort) -- used as a fallback, mainly for local runs
     from a residential/university IP that Scholar does not block.

The committed publications.json is the source of truth that the website and the
embeddable widget (index.html) read from. The script never overwrites it with an
empty result.

Usage:
    # Reliable (CI or local):
    pip install requests
    SERPAPI_API_KEY=xxxx python sync_scholar.py

    # Best-effort, no key:
    pip install scholarly
    python sync_scholar.py
"""

import datetime
import json
import os
import re
import sys
from pathlib import Path

SCHOLAR_ID = "bRzhctsAAAAJ"
AUTHOR_TAG = "A Renganathan"   # name highlighted in author lists on the page
N_RECENT = 10
OUT_FILE = Path(__file__).with_name("publications.json")

PROFILE_URL = f"https://scholar.google.com/citations?hl=en&user={SCHOLAR_ID}"


def _year_key(p):
    try:
        return int(p.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def _arxiv_url(venue):
    m = re.search(r"arXiv:(\d{4}\.\d{4,5})", venue or "")
    return f"https://arxiv.org/abs/{m.group(1)}" if m else ""


def fetch_serpapi(api_key):
    import requests

    params = {
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "api_key": api_key,
        "sort": "pubdate",   # newest first
        "num": 100,
        "hl": "en",
    }
    r = requests.get("https://serpapi.com/search", params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    out = []
    for a in data.get("articles", [])[:N_RECENT]:
        venue = (a.get("publication") or "").strip()
        out.append({
            "title": (a.get("title") or "").strip(),
            "authors": (a.get("authors") or "").strip(),
            "venue": venue,
            "year": str(a.get("year") or "").strip(),
            "url": _arxiv_url(venue),
        })
    return out


def fetch_scholarly():
    from scholarly import scholarly

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])
    pubs = sorted(author["publications"], key=lambda p: _year_key(p["bib"]), reverse=True)

    out = []
    for p in pubs[:N_RECENT]:
        bib = p["bib"]
        venue = (bib.get("citation") or bib.get("journal") or "").strip()
        out.append({
            "title": bib.get("title", "").strip(),
            "authors": bib.get("author", "").replace(" and ", ", ").strip(),
            "venue": venue,
            "year": str(bib.get("pub_year", "")).strip(),
            "url": _arxiv_url(venue),
        })
    return out


def fetch_recent():
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if key:
        print("Fetching via SerpAPI...")
        return fetch_serpapi(key)
    print("No SERPAPI_API_KEY set; falling back to scholarly (may be blocked in CI)...")
    try:
        return fetch_scholarly()
    except ImportError:
        sys.exit("Install a backend: `pip install requests` (+ SERPAPI_API_KEY) or `pip install scholarly`.")


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
