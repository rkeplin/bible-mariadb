"""Build the `t_nlt_2015` table block + `translations` row and splice them
into initdb.d/seed.sql, in the exact same style as the existing `t_nlt`
table (same columns/indexes/charset), placed right after the `t_nlt` block.

Usage: python3 build_seed.py [--dry-run]
"""
import argparse
import json
import re
from pathlib import Path

from books import BOOKS_BY_ID
from sqltuple import escape_sql_string

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SEED_SQL = ROOT / "initdb.d" / "seed.sql"
STRUCTURE = json.loads((HERE / "data" / "nlt_structure.json").read_text())
DATA_PATH = HERE / "data" / "nlt2015.json"
OUT_FRAGMENT = HERE / "output" / "t_nlt_2015.sql"

TABLE_NAME = "t_nlt_2015"
TRANSLATION_ID = "011"
ROWS_PER_INSERT = 2000


def validate_structure(data):
    expected_books = set(STRUCTURE.keys())
    got_books = set(data.keys())
    if expected_books != got_books:
        raise SystemExit(f"book set mismatch: missing={sorted(expected_books - got_books, key=int)}")
    for book_id, exp_chapters in STRUCTURE.items():
        got_chapters = data.get(book_id, {})
        if set(exp_chapters.keys()) != set(got_chapters.keys()):
            raise SystemExit(f"book {book_id}: chapter set mismatch")
        for chapter_id, exp_max in exp_chapters.items():
            verses = got_chapters[chapter_id]
            ids = sorted(int(v) for v in verses)
            if ids != list(range(1, exp_max + 1)):
                raise SystemExit(f"book {book_id} chapter {chapter_id}: verse ids {ids} != 1..{exp_max}")
            for v in ids:
                text = verses[str(v)]
                if not text.strip():
                    raise SystemExit(f"book {book_id} chapter {chapter_id}:{v}: empty text")
                non_ascii = [c for c in text if ord(c) > 127]
                if non_ascii:
                    raise SystemExit(f"book {book_id} chapter {chapter_id}:{v}: non-ASCII chars {non_ascii}")


def build_table_block(data):
    lines = []
    lines.append("--")
    lines.append(f"-- Table structure for table `{TABLE_NAME}`")
    lines.append("--")
    lines.append("")
    lines.append(f"DROP TABLE IF EXISTS `{TABLE_NAME}`;")
    lines.append("/*!40101 SET @saved_cs_client     = @@character_set_client */;")
    lines.append("/*!40101 SET character_set_client = utf8 */;")
    lines.append(f"CREATE TABLE `{TABLE_NAME}` (")
    lines.append("  `id` int(8) unsigned zerofill NOT NULL,")
    lines.append("  `bookId` int(11) NOT NULL,")
    lines.append("  `chapterId` int(11) NOT NULL,")
    lines.append("  `verseId` int(11) NOT NULL,")
    lines.append("  `verse` text NOT NULL,")
    lines.append("  PRIMARY KEY (`id`),")
    lines.append("  UNIQUE KEY `id_2` (`id`),")
    lines.append("  KEY `id` (`id`)")
    lines.append(") ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    lines.append("/*!40101 SET character_set_client = @saved_cs_client */;")
    lines.append("")
    lines.append("--")
    lines.append(f"-- Dumping data for table `{TABLE_NAME}`")
    lines.append("--")
    lines.append("")
    lines.append(f"LOCK TABLES `{TABLE_NAME}` WRITE;")
    lines.append(f"/*!40000 ALTER TABLE `{TABLE_NAME}` DISABLE KEYS */;")

    rows = []
    for book_id in sorted(data.keys(), key=int):
        chapters = data[book_id]
        for chapter_id in sorted(chapters.keys(), key=int):
            verses = chapters[chapter_id]
            for verse_id in sorted(verses.keys(), key=int):
                text = verses[verse_id]
                b, c, v = int(book_id), int(chapter_id), int(verse_id)
                row_id = f"{b:02d}{c:03d}{v:03d}"
                escaped = escape_sql_string(text)
                rows.append(f"({row_id},{b},{c},{v},'{escaped}')")

    for i in range(0, len(rows), ROWS_PER_INSERT):
        chunk = rows[i : i + ROWS_PER_INSERT]
        lines.append(f"INSERT INTO `{TABLE_NAME}` VALUES {','.join(chunk)};")

    lines.append(f"/*!40000 ALTER TABLE `{TABLE_NAME}` ENABLE KEYS */;")
    lines.append("UNLOCK TABLES;")
    lines.append("")
    return "\n".join(lines), len(rows)


TRANSLATIONS_ROW = (
    "(" + TRANSLATION_ID + ",'" + TABLE_NAME + "','NLT2015','english',"
    "'New Living Translation (2015)','',"
    "'https://en.wikipedia.org/wiki/New_Living_Translation',"
    "'Tyndale House Publishers','Copyrighted',"
    "'Scripture quoted by permission. Quotations designated (NLT) are from the Holy Bible, "
    "New Living Translation, copyright (c) 1996, 2004, 2015 by Tyndale House Foundation. "
    "Used by permission of Tyndale House Publishers, Inc., Carol Stream, Illinois 60188. "
    "All rights reserved.')"
)


def splice_into_seed(table_block):
    text = SEED_SQL.read_text(encoding="latin1")

    start = text.index("LOCK TABLES `t_nlt` WRITE")
    end = text.index("UNLOCK TABLES;", start) + len("UNLOCK TABLES;\n")
    if f"`{TABLE_NAME}`" in text:
        raise SystemExit(f"{TABLE_NAME} already present in seed.sql - refusing to double-insert")

    new_text = text[:end] + "\n" + table_block + "\n" + text[end:]

    trans_match = re.search(r"INSERT INTO `translations` VALUES (.*?);\n", new_text, re.S)
    if not trans_match:
        raise SystemExit("could not find translations INSERT to extend")
    if TRANSLATION_ID in trans_match.group(0):
        raise SystemExit("translations row already present - refusing to double-insert")
    replacement = trans_match.group(0).rstrip("\n").rstrip(";") + "," + TRANSLATIONS_ROW + ";\n"
    new_text = new_text[: trans_match.start()] + replacement + new_text[trans_match.end() :]

    return new_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="write fragment to output/ but do not modify seed.sql")
    args = ap.parse_args()

    data = json.loads(DATA_PATH.read_text())
    validate_structure(data)
    print("structure validated OK against existing NLT shape")

    table_block, row_count = build_table_block(data)
    OUT_FRAGMENT.parent.mkdir(parents=True, exist_ok=True)
    OUT_FRAGMENT.write_text(table_block, encoding="latin1")
    print(f"wrote {OUT_FRAGMENT} ({row_count} verse rows)")

    if args.dry_run:
        print("dry run, not touching seed.sql")
        return

    new_seed = splice_into_seed(table_block)
    SEED_SQL.write_text(new_seed, encoding="latin1")
    print(f"updated {SEED_SQL}")


if __name__ == "__main__":
    main()
