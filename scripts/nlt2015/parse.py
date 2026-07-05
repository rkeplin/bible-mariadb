"""Parse cached chapter HTML into data/nlt2015.json.

Each chapter page has one <div data-verse-id="N" class="bible-verse-row ...">
per verse, containing a <span class="bible-text">...</span> with the verse
text (possibly with an inline <sup>...footnote...</sup> marker).

Usage: python3 parse.py
Writes: data/nlt2015.json  { "<bookId>": { "<chapterId>": { "<verseId>": "text", ... } } }
"""
import html
import json
import re
from pathlib import Path

from books import BOOKS_BY_ID

HERE = Path(__file__).resolve().parent
CACHE_DIR = HERE / "cache"
OUT = HERE / "data" / "nlt2015.json"

VERSE_ROW_RE = re.compile(
    r'data-verse-id="(\d+)"[\s\S]*?class="bible-text">([\s\S]*?)</span>',
)
SUP_RE = re.compile(r"<sup\b[\s\S]*?</sup>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# Typographic punctuation -> ASCII, to match the plain-ASCII style already
# used by every other translation table in this database (which are all
# latin1-charset). Keeps t_nlt_2015 consistent and avoids any lossy charset
# conversion when the dump is loaded.
NORMALIZE = {
    "‘": "'", "’": "'",   # single quotes
    "“": '"', "”": '"',   # double quotes
    "–": "-", "—": "--",  # en dash, em dash
    "…": "...",                # ellipsis
    " ": " ",                   # nbsp
}


def clean_verse_html(raw):
    text = SUP_RE.sub("", raw)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    for src, dst in NORMALIZE.items():
        text = text.replace(src, dst)
    text = " ".join(text.split()).strip()
    # the source site occasionally renders a stray space before sentence
    # punctuation (e.g. after the small-caps "LORD" divine name) - collapse it
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def parse_chapter_html(html_text):
    verses = {}
    for m in VERSE_ROW_RE.finditer(html_text):
        verse_id = int(m.group(1))
        text = clean_verse_html(m.group(2))
        if text:
            verses[verse_id] = text
    return verses


def main():
    result = {}
    total_verses = 0
    empty = []
    for book_id in sorted(BOOKS_BY_ID):
        book = BOOKS_BY_ID[book_id]
        book_dir = CACHE_DIR / f"{book_id:02d}-{book['slug']}"
        if not book_dir.exists():
            continue
        chapters = {}
        for f in sorted(book_dir.glob("*.html"), key=lambda p: int(p.stem)):
            chapter_id = int(f.stem)
            verses = parse_chapter_html(f.read_text(encoding="utf-8"))
            if not verses:
                empty.append((book_id, chapter_id))
            chapters[chapter_id] = verses
            total_verses += len(verses)
        if chapters:
            result[book_id] = chapters

    out = {
        str(b): {str(c): {str(v): t for v, t in sorted(verses.items())} for c, verses in sorted(chs.items())}
        for b, chs in sorted(result.items())
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    print(f"parsed books={len(result)} verses={total_verses}")
    if empty:
        print(f"WARNING: {len(empty)} chapters parsed with zero verses:")
        for b, c in empty[:20]:
            print(f"  book {b} ({BOOKS_BY_ID[b]['name']}) chapter {c}")


if __name__ == "__main__":
    main()
