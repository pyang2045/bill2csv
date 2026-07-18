#!/usr/bin/env python3
"""Validate and normalize extracted bill transactions.

Stdlib only. Reads a raw CSV (header: Date,Description,Payee,Amount,Category),
normalizes each row, and writes:
  - OUT_CSV           valid, normalized rows (UTF-8)
  - OUT_CSV stem + .errors.csv   rejected rows (row,reason,raw) — only if any

Usage: validate.py RAW_CSV OUT_CSV

Prints a summary (row counts, charge/credit totals, category breakdown,
remapped categories) to stdout for the caller to relay.
"""
import csv
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

DATE_FORMATS = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%y", "%d/%m/%y"]
SYMBOL_TABLE = str.maketrans({c: " " for c in "*#@&/\\|<>~`^+=[]{}"})
DASH_RUN = re.compile(r"[-–—_]+")
AMOUNT_RE = re.compile(r"^-?\d+(\.\d+)?$")
CURRENCY = "$£€¥₹¢"
FIELDS = ["Date", "Description", "Payee", "Amount", "Category"]


class RowError(Exception):
    pass


def _parse_categories_file(path, lookup):
    """Parse one categories markdown file (2-space indent tree) into lookup."""
    stack = []  # canonical names by indent level
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\s*)-\s+(.*\S)\s*$", line)
        if not m:
            continue  # skip headers and prose
        level = len(m.group(1)) // 2
        name = m.group(2).strip()
        stack = stack[:level]
        stack.append(name)
        full = " > ".join(stack)
        lookup[full.lower()] = full
        if level == 0:
            lookup[name.lower()] = full
        else:
            lookup.setdefault(name.lower(), full)


def load_categories():
    """Parse categories.md, then optional categories.local.md, into one lookup.

    {lowercase name/path -> canonical 'A > B > C'}. Arbitrary nesting via 2-space
    indentation; a bare leaf maps to its first-seen path, a top-level name to
    itself. categories.local.md (gitignored, personal) extends the public tree.
    """
    base = Path(__file__).resolve().parent.parent
    lookup = {}
    for fname in ("categories.md", "categories.local.md"):
        path = base / fname
        if path.exists():
            _parse_categories_file(path, lookup)
    return lookup


def norm_date(value):
    value = value.strip()
    if not value:
        raise RowError("empty date")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    raise RowError(f"unparseable date: {value!r}")


def norm_amount(value):
    value = value.strip()
    if not value:
        raise RowError("empty amount")
    value = value.replace("−", "-").replace("–", "-")
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    value = value.translate(str.maketrans("", "", CURRENCY + ", "))
    if not AMOUNT_RE.match(value):
        raise RowError(f"invalid amount: {value!r}")
    return f"{float(value):.2f}"


def norm_description(value):
    value = DASH_RUN.sub(" ", value.translate(SYMBOL_TABLE))
    value = " ".join(value.split())
    if not value:
        raise RowError("empty description")
    return value


def norm_payee(value):
    return " ".join(value.split())


def norm_category(value, lookup, remapped):
    value = " ".join(value.split())
    if not value:
        return "Other > Uncategorized"
    key = value.lower()
    for candidate in (key, key.replace("/", " > "), key.replace(" - ", " > "),
                      re.sub(r"\s*>\s*", " > ", key)):
        if candidate in lookup:
            return lookup[candidate]
    remapped.append(value)
    return "Other > Uncategorized"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raw_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    lookup = load_categories()

    with open(raw_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        missing = [c for c in FIELDS if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"error: raw CSV missing columns: {', '.join(missing)}")
        raw_rows = list(reader)

    valid, errors, remapped = [], [], []
    for i, row in enumerate(raw_rows, start=2):  # header is line 1
        try:
            valid.append({
                "Date": norm_date(row.get("Date") or ""),
                "Description": norm_description(row.get("Description") or ""),
                "Payee": norm_payee(row.get("Payee") or ""),
                "Amount": norm_amount(row.get("Amount") or ""),
                "Category": norm_category(row.get("Category") or "", lookup, remapped),
            })
        except RowError as e:
            raw = ",".join((row.get(c) or "") for c in FIELDS)
            errors.append({"row": i, "reason": str(e), "raw": raw})

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(valid)

    errors_path = out_path.with_suffix(".errors.csv")
    if errors:
        with open(errors_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["row", "reason", "raw"])
            writer.writeheader()
            writer.writerows(errors)

    charges = sum(a for a in (float(r["Amount"]) for r in valid) if a < 0)
    credits = sum(a for a in (float(r["Amount"]) for r in valid) if a > 0)
    by_main = Counter(r["Category"].split(" > ")[0] for r in valid)

    print(f"rows_written: {len(valid)} -> {out_path}")
    print(f"rows_rejected: {len(errors)}" + (f" -> {errors_path}" if errors else ""))
    print(f"total_charges: {charges:.2f}")
    print(f"total_credits: {credits:.2f}")
    print("category_breakdown:")
    for name, count in by_main.most_common():
        print(f"  {name}: {count}")
    if remapped:
        print("remapped_to_uncategorized: " + "; ".join(sorted(set(remapped))))


if __name__ == "__main__":
    main()
