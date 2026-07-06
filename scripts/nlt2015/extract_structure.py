"""Extract the ground-truth book/chapter/verse structure from the existing
`t_nlt` table in initdb.d/seed.sql, so the new NLT-2015 scrape can be
validated to have the exact same shape (same books, same chapters, and the
exact same set of verse ids per chapter - note some chapters have gaps,
e.g. Numbers 1 skips verse ids 21/23/25/.../43 entirely).

Usage: python3 extract_structure.py
Writes: data/nlt_structure.json  { "<bookId>": { "<chapterId>": [verseId, ...], ... }, ... }
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

    struct = defaultdict(lambda: defaultdict(list))
    total_verses = 0
    for ins in inserts:
        for row in split_tuples(ins):
            rid, book_id, chapter_id, verse_id, _verse = row.split(",", 4)
            book_id, chapter_id, verse_id = int(book_id), int(chapter_id), int(verse_id)
            struct[book_id][chapter_id].append(verse_id)
            total_verses += 1

    out = {
        str(b): {str(c): sorted(verse_ids) for c, verse_ids in sorted(chs.items())}
        for b, chs in sorted(struct.items())
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))

    total_chapters = sum(len(v) for v in struct.values())
    print(f"books={len(struct)} chapters={total_chapters} verses={total_verses}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
