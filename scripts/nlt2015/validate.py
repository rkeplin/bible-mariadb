"""Validate data/nlt2015.json against the ground-truth structure extracted
from the existing NLT translation (data/nlt_structure.json): same books,
same chapters, same exact set of verse ids per chapter (some chapters have
gaps in the old translation - this checks against the exact set, not a
contiguous range).

A handful of chapters (2 Corinthians 13, 3 John 1, Revelation 12) have one
more verse in the 2015 edition than the older edition in this database, due
to a genuine versification difference between editions - those extra ids
are pre-approved in data/nlt_structure.json (see comment there).

Verses that exist as an id on the page but render with no text (a small
number of textually-disputed verses that translations footnote rather than
print, e.g. Mark 9:44) are left as empty string here; build_seed.py fills
those with the same 'See Footnote' placeholder the existing t_nlt table
uses for the same verses.

Usage: python3 validate.py
Exit code is non-zero if any mismatch is found.
"""
import json
import sys
from pathlib import Path

from books import BOOKS_BY_ID

HERE = Path(__file__).resolve().parent
STRUCTURE = json.loads((HERE / "data" / "nlt_structure.json").read_text())
DATA_PATH = HERE / "data" / "nlt2015.json"

LATIN1_MAX = 255  # t_nlt (and this new table) use CHARSET=latin1 / ISO-8859-1


def main():
    data = json.loads(DATA_PATH.read_text())

    problems = []

    expected_books = set(STRUCTURE.keys())
    got_books = set(data.keys())
    if expected_books != got_books:
        problems.append(f"book set mismatch: missing={sorted(expected_books - got_books, key=int)} extra={sorted(got_books - expected_books, key=int)}")

    for book_id in sorted(expected_books, key=int):
        name = BOOKS_BY_ID[int(book_id)]["name"]
        exp_chapters = STRUCTURE[book_id]
        got_chapters = data.get(book_id, {})

        exp_chapter_set = set(exp_chapters.keys())
        got_chapter_set = set(got_chapters.keys())
        if exp_chapter_set != got_chapter_set:
            problems.append(
                f"{name} (book {book_id}): chapter mismatch missing={sorted(exp_chapter_set - got_chapter_set, key=int)} extra={sorted(got_chapter_set - exp_chapter_set, key=int)}"
            )

        for chapter_id in sorted(exp_chapter_set & got_chapter_set, key=int):
            expected_ids = set(exp_chapters[chapter_id])
            got_verses = got_chapters[chapter_id]
            got_ids = {int(v) for v in got_verses.keys()}

            missing_ids = sorted(expected_ids - got_ids)
            if missing_ids:
                problems.append(f"{name} {chapter_id}: verse id(s) {missing_ids} expected but not present on scraped page at all")

            for v in sorted(expected_ids & got_ids):
                text = got_verses[str(v)]
                non_latin1 = sorted({c for c in text if ord(c) > LATIN1_MAX})
                if non_latin1:
                    problems.append(
                        f"{name} {chapter_id}:{v}: char(s) outside latin1 {[hex(ord(c)) for c in non_latin1]}"
                    )

    if problems:
        print(f"{len(problems)} problem(s) found:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    total_verses = sum(
        len(set(exp_chapters[c]) & {int(v) for v in data[b][c].keys()})
        for b, exp_chapters in STRUCTURE.items()
        for c in exp_chapters
    )
    print(f"OK: {len(data)} books match existing NLT structure exactly (by verse id set). {total_verses} verses will be emitted.")


if __name__ == "__main__":
    main()
