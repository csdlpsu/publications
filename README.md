# CSDL Publications — Google Scholar sync

Tracks recent CSDL publications from Google Scholar and serves them as JSON +
an embeddable widget. A scheduled GitHub Action does the syncing, so no live
scraping happens in the browser (Scholar has no API and blocks cross-origin/bot
requests).

## How it works
1. `.github/workflows/sync.yml` runs weekly (and on-demand), executes
   `sync_scholar.py`, and commits `publications.json` if it changed.
2. `publications.json` is the **source of truth** — the 10 most recent works.
3. `index.html` is a self-contained widget that renders `publications.json`;
   served via GitHub Pages it can be embedded anywhere (incl. Google Sites).

## Consuming the data
- **Raw JSON (CORS-enabled, no Pages needed):**
  `https://raw.githubusercontent.com/csdlpsu/publications/main/publications.json`
- **GitHub Pages (after enabling Pages on `main`):**
  - Data: `https://csdlpsu.github.io/publications/publications.json`
  - Widget: `https://csdlpsu.github.io/publications/`

The personal website's Publications page fetches the JSON above and falls back to
its bundled copy if the network call fails.

## Configure
Edit the constants at the top of `sync_scholar.py`:
- `SCHOLAR_ID` — the Scholar user id (currently `bRzhctsAAAAJ`)
- `AUTHOR_TAG` — name to bold in author lists
- `N_RECENT` — how many to publish (currently 10)

Change the cron in `.github/workflows/sync.yml` to adjust frequency.

## Run locally
```bash
pip install scholarly
python sync_scholar.py
```

## Enabling GitHub Pages (optional, for the embeddable widget)
Settings → Pages → Build from branch → `main` / root. Then embed in Google Sites
via Insert → Embed → By URL using `https://csdlpsu.github.io/publications/`.

## Notes
- `scholarly` can hit a CAPTCHA on Scholar. The Action just reports no change and
  retries next run; the script never overwrites `publications.json` with empty data.
- The workflow needs no secrets — it uses the built-in `GITHUB_TOKEN` (the
  `contents: write` permission is declared in the workflow).
