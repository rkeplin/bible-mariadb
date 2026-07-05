"""Validate data/nlt2015.json against the ground-truth structure extracted
from the existing NLT translation (data/nlt_structure.json): same books,
same chapter counts per book, same verse counts per chapter.

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
            exp_max_verse = exp_chapters[chapter_id]
            got_verses = got_chapters[chapter_id]
            got_verse_ids = sorted(int(v) for v in got_verses.keys())
            got_max_verse = got_verse_ids[-1] if got_verse_ids else 0

            if got_max_verse != exp_max_verse:
                problems.append(
                    f"{name} {chapter_id}: expected {exp_max_verse} verses, got {got_max_verse}"
                )
                continue

            expected_ids = set(range(1, exp_max_verse + 1))
            if set(got_verse_ids) != expected_ids:
                missing = sorted(expected_ids - set(got_verse_ids))
                problems.append(f"{name} {chapter_id}: non-contiguous verse ids, missing={missing}")

            for v in got_verse_ids:
                text = got_verses[str(v)]
                if not text.strip():
                    problems.append(f"{name} {chapter_id}:{v}: empty verse text")
                non_ascii = sorted({c for c in text if ord(c) > 127})
                if non_ascii:
                    problems.append(
                        f"{name} {chapter_id}:{v}: non-ASCII chars {[hex(ord(c)) for c in non_ascii]} (existing t_nlt table is pure ASCII/latin1)"
                    )

    if problems:
        print(f"{len(problems)} problem(s) found:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    total_verses = sum(len(v) for chs in data.values() for v in chs.values())
    print(f"OK: {len(data)} books, {sum(len(chs) for chs in data.values())} chapters, {total_verses} verses — matches existing NLT structure exactly.")


if __name__ == "__main__":
    main()
