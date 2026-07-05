"""Extract the ground-truth book/chapter/verse structure from the existing
`t_nlt` table in initdb.d/seed.sql, so the new NLT-2015 scrape can be
validated to have the exact same shape (same books, same chapter counts,
same verse counts per chapter).

Usage: python3 extract_structure.py
Writes: data/nlt_structure.json  { "<bookId>": { "<chapterId>": maxVerseId, ... }, ... }
"""
import json
import re
from collections import defaultdict
from pathlib import Path

from sqltuple import split_tuples

ROOT = Path(__file__).resolve().parent.parent.parent
SEED_SQL = ROOT / "initdb.d" / "seed.sql"
OUT = Path(__file__).resolve().parent / "data" / "nlt_structure.json"


def main():
    text = SEED_SQL.read_text(encoding="latin1")

    start = text.index("LOCK TABLES `t_nlt` WRITE")
    end = text.index("UNLOCK TABLES", start)
    block = text[start:end]

    inserts = re.findall(r"INSERT INTO `t_nlt` VALUES (.*?);\n", block, re.S)
    if not inserts:
        raise SystemExit("No INSERT statements found for t_nlt")

    struct = defaultdict(dict)
    total_verses = 0
    for ins in inserts:
        for row in split_tuples(ins):
            rid, book_id, chapter_id, verse_id, _verse = row.split(",", 4)
            book_id, chapter_id, verse_id = int(book_id), int(chapter_id), int(verse_id)
            struct[book_id][chapter_id] = max(struct[book_id].get(chapter_id, 0), verse_id)
            total_verses += 1

    out = {str(b): {str(c): v for c, v in sorted(chs.items())} for b, chs in sorted(struct.items())}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))

    total_chapters = sum(len(v) for v in struct.values())
    print(f"books={len(struct)} chapters={total_chapters} verses={total_verses}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
