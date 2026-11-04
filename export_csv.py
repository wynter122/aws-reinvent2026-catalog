#!/usr/bin/env python3
"""Convert data/sessions_raw.json into a CSV file.

Uses the same field selection as build_viewer.py (slim_session), so the CSV matches
what the viewer shows. Korean translations from translations/ko.json are included
when available. Standard library only: `python3 export_csv.py`.

Options:
  --raw PATH   input JSON (default: data/sessions_raw.json)
  --out PATH   output CSV (default: data/sessions.csv)
  --no-ko      leave out the Korean title/abstract columns
"""
import argparse
import csv
import json
from pathlib import Path

from build_viewer import BASE_DIR, RAW_PATH, load_translations, slim_session, text_key

OUT_PATH = BASE_DIR / "data" / "sessions.csv"
LIST_SEP = "; "
# Cells starting with these are treated as formulas by Excel/Sheets
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def joined(values):
    return LIST_SEP.join(values or [])


def speakers(row):
    out = []
    for p in row.get("sp") or []:
        extra = ", ".join(v for v in (p.get("j"), p.get("o")) if v)
        out.append(p.get("n", "") + (f" ({extra})" if extra else ""))
    return LIST_SEP.join(out)


def flag(value):
    return "Y" if value else ""


# (header, value getter)
COLUMNS = [
    ("code", lambda r: r.get("c")),
    ("group", lambda r: r.get("g")),
    ("title", lambda r: r.get("t")),
    ("title_ko", lambda r: r.get("tk")),
    ("type", lambda r: r.get("y")),
    ("level", lambda r: r.get("l")),
    ("track", lambda r: r.get("tr")),
    ("date", lambda r: r.get("d")),
    ("start", lambda r: r.get("s")),
    ("end", lambda r: r.get("e")),
    ("minutes", lambda r: r.get("len")),
    ("venue", lambda r: r.get("v")),
    ("room", lambda r: r.get("r")),
    ("capacity", lambda r: "" if r.get("cap") == "0" else r.get("cap")),
    ("speakers", speakers),
    ("topics", lambda r: joined(r.get("tp"))),
    ("areas_of_interest", lambda r: joined(r.get("ai"))),
    ("services", lambda r: joined(r.get("sv"))),
    ("roles", lambda r: joined(r.get("ro"))),
    ("industries", lambda r: joined(r.get("in"))),
    ("features", lambda r: joined(r.get("ft"))),
    ("laptop_required", lambda r: flag(r.get("lap"))),
    ("sponsored", lambda r: flag(r.get("spon"))),
    ("abstract", lambda r: r.get("a")),
    ("abstract_ko", lambda r: r.get("ak")),
    ("url", lambda r: r.get("u")),
]
KO_COLUMNS = {"title_ko", "abstract_ko"}


def safe_cell(value):
    """Prefix formula-like text with ' so spreadsheet apps show it as text."""
    if value is None:
        return ""
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def load_rows(raw_path, with_ko):
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    rows = sorted((slim_session(s) for s in raw), key=lambda r: r["c"])
    if with_ko:
        ko = load_translations()
        for row in rows:
            for src, dst in (("t", "tk"), ("a", "ak")):
                if row.get(src) and ko.get(text_key(row[src])):
                    row[dst] = ko[text_key(row[src])]
    return rows


def write_csv(rows, out_path, with_ko):
    columns = [c for c in COLUMNS if with_ko or c[0] not in KO_COLUMNS]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig adds a BOM so Excel reads non-ASCII text (Korean, accents) correctly
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(name for name, _ in columns)
        for row in rows:
            writer.writerow(safe_cell(get(row)) for _, get in columns)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW_PATH, help="input JSON path")
    parser.add_argument("--out", type=Path, default=OUT_PATH, help="output CSV path")
    parser.add_argument("--no-ko", action="store_true", help="omit Korean translation columns")
    args = parser.parse_args()

    if not args.raw.exists():
        parser.error(f"{args.raw} not found. Run fetch_catalog.py first.")
    rows = load_rows(args.raw, not args.no_ko)
    write_csv(rows, args.out, not args.no_ko)
    print(f"Done: {len(rows)} sessions -> {args.out}")


if __name__ == "__main__":
    main()
