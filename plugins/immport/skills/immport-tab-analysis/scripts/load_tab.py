#!/usr/bin/env python3
"""
Load ImmPort Tab.zip packages into one SQLite database.

Each Tab.zip (e.g. SDY180-DR58_Tab.zip) holds one tab-separated file per ImmPort table under
<SDY>-DR<n>_Tab/Tab/<table>.txt, with an uppercase header row. This loads every table into SQLite
with lowercase table and column names, matching the ImmPort data model (get_data_model), so the
data can be queried with SQL. Several Tab.zips can go into the same database for cross-study work:
rows are appended, and every research table carries study_accession or links to a table that does.

Values that look like integers or decimals are stored as numbers, empty values as NULL.
Standard library only.

Usage:
    python3 load_tab.py SDY180-DR58_Tab.zip                          # → immport.db
    python3 load_tab.py SDY180-DR58_Tab.zip SDY269-DR58_Tab.zip --db flu.db
    python3 load_tab.py path/to/extracted/Tab/ --db study.db         # an unzipped Tab folder works too
"""
from __future__ import annotations

import argparse
import csv
import io
import pathlib
import re
import sqlite3
import sys
import zipfile

csv.field_size_limit(sys.maxsize)
_INT = re.compile(r"-?\d+")
_FLOAT = re.compile(r"-?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?")
_BATCH = 5000


def convert(value: str):
    if value == "":
        return None
    if _INT.fullmatch(value) and len(value.lstrip("-")) < 19:
        return int(value)
    if _FLOAT.fullmatch(value):
        return float(value)
    return value


def tables_in(source: pathlib.Path):
    """(table name, text stream) for each table file in a Tab.zip or folder.

    Tables are the .txt files directly in the Tab folder; Tab/protocols/ holds the study's
    protocol documents, which are not tables.
    """
    if source.is_dir():
        tab = next((d for d in [source, *source.rglob("Tab")] if d.name == "Tab"), source)
        for f in sorted(tab.glob("*.txt")):
            yield f.stem.lower(), open(f, encoding="utf-8", errors="replace", newline="")
        return
    with zipfile.ZipFile(source) as z:
        for name in sorted(z.namelist()):
            parts = pathlib.PurePosixPath(name).parts
            if name.endswith(".txt") and len(parts) >= 2 and parts[-2] == "Tab":
                yield pathlib.PurePosixPath(name).stem.lower(), io.TextIOWrapper(
                    z.open(name), encoding="utf-8", errors="replace", newline="")


def load(db: sqlite3.Connection, source: pathlib.Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, stream in tables_in(source):
        with stream:
            reader = csv.reader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
            header = next(reader, None)
            if not header:
                continue
            columns = [c.strip().lower() for c in header]
            cols_sql = ", ".join(f'"{c}"' for c in columns)
            db.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_sql})')
            existing = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
            for c in columns:  # a newer release may add columns
                if c not in existing:
                    db.execute(f'ALTER TABLE "{table}" ADD COLUMN "{c}"')
            insert = f'INSERT INTO "{table}" ({cols_sql}) VALUES ({", ".join("?" * len(columns))})'
            batch, n = [], 0
            for row in reader:
                if not row:
                    continue
                row = (row + [""] * len(columns))[: len(columns)]
                batch.append([convert(v) for v in row])
                if len(batch) >= _BATCH:
                    db.executemany(insert, batch)
                    n += len(batch)
                    batch = []
            if batch:
                db.executemany(insert, batch)
                n += len(batch)
            counts[table] = counts.get(table, 0) + n
    db.commit()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="+", type=pathlib.Path, help="Tab.zip files or extracted Tab folders")
    parser.add_argument("--db", type=pathlib.Path, default=pathlib.Path("immport.db"), help="SQLite file (default immport.db)")
    args = parser.parse_args()

    db = sqlite3.connect(args.db)
    for source in args.sources:
        if not source.exists():
            print(f"Not found: {source}", file=sys.stderr)
            return 1
        counts = load(db, source)
        data = {t: n for t, n in counts.items() if not t.startswith("lk_")}
        print(f"{source.name}: {len(counts)} tables ({len(counts) - len(data)} lookup tables)")
        for table, n in sorted(data.items(), key=lambda kv: -kv[1]):
            if n:
                print(f"  {table:40s} {n:>10,}")
    print(f"Database: {args.db.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
