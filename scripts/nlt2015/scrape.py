"""Scrape NLT (2015) chapter pages from biblestudytools.com.

Resumable: already-cached chapter files are skipped on re-run. Uses a
person-like User-Agent and a randomized delay between requests to be a
good citizen and avoid rate limiting.

Usage:
  python3 scrape.py                # scrape everything
  python3 scrape.py --book 19      # scrape a single book (by id)
  python3 scrape.py --book 19 --chapter 3   # scrape a single chapter
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from books import BOOKS_BY_ID

HERE = Path(__file__).resolve().parent
STRUCTURE = json.loads((HERE / "data" / "nlt_structure.json").read_text())
CACHE_DIR = HERE / "cache"

BASE_URL = "https://www.biblestudytools.com/nlt"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

MIN_DELAY = 2.0
MAX_DELAY = 4.5
MAX_RETRIES = 4


def cache_path(book_id, chapter):
    book_dir = CACHE_DIR / f"{book_id:02d}-{BOOKS_BY_ID[book_id]['slug']}"
    book_dir.mkdir(parents=True, exist_ok=True)
    return book_dir / f"{chapter}.html"


def fetch(url):
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            last_err = e
            if e.code == 429:
                backoff = 20 * attempt
                print(f"    429 rate limited, backing off {backoff}s (attempt {attempt})")
                time.sleep(backoff)
            elif 500 <= e.code < 600:
                backoff = 10 * attempt
                print(f"    HTTP {e.code}, retrying in {backoff}s (attempt {attempt})")
                time.sleep(backoff)
            else:
                raise
        except URLError as e:
            last_err = e
            backoff = 10 * attempt
            print(f"    URLError {e}, retrying in {backoff}s (attempt {attempt})")
            time.sleep(backoff)
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {last_err}")


def scrape_chapter(book_id, chapter):
    dest = cache_path(book_id, chapter)
    if dest.exists() and dest.stat().st_size > 0:
        return False  # already cached, no request made

    slug = BOOKS_BY_ID[book_id]["slug"]
    url = f"{BASE_URL}/{slug}/{chapter}.html"
    html = fetch(url)
    dest.write_text(html, encoding="utf-8")
    return True


def iter_targets(only_book=None, only_chapter=None):
    for book_id_str, chapters in STRUCTURE.items():
        book_id = int(book_id_str)
        if only_book is not None and book_id != only_book:
            continue
        for chapter_str in chapters:
            chapter = int(chapter_str)
            if only_chapter is not None and chapter != only_chapter:
                continue
            yield book_id, chapter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", type=int, default=None, help="only scrape this book id")
    ap.add_argument("--chapter", type=int, default=None, help="only scrape this chapter (requires --book)")
    args = ap.parse_args()

    targets = list(iter_targets(args.book, args.chapter))
    print(f"{len(targets)} chapters targeted")

    fetched = 0
    skipped = 0
    for idx, (book_id, chapter) in enumerate(targets, 1):
        name = BOOKS_BY_ID[book_id]["name"]
        try:
            did_fetch = scrape_chapter(book_id, chapter)
        except Exception as e:
            print(f"[{idx}/{len(targets)}] FAILED {name} {chapter}: {e}", file=sys.stderr)
            raise
        if did_fetch:
            fetched += 1
            print(f"[{idx}/{len(targets)}] fetched {name} {chapter}")
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        else:
            skipped += 1
            if idx % 50 == 0:
                print(f"[{idx}/{len(targets)}] (cached) {name} {chapter}")

    print(f"done. fetched={fetched} skipped(cached)={skipped}")


if __name__ == "__main__":
    main()
