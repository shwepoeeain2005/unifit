"""Rewrite old university paths inside SQLite HTML fields using redirect stubs."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "maintenance" / "unifit.sqlite"
UNI = ROOT / "universities"

TARGET_RE = re.compile(
    r'url=(?P<target>[^">\s]+)|location\.replace\([\'"](?P<js>[^\'"]+)[\'"]\)',
    re.I,
)


def load_redirect_map() -> dict[str, str]:
    mapping = {}
    for path in UNI.glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "this page moved" not in text.lower():
            continue
        match = TARGET_RE.search(text)
        if not match:
            continue
        target = match.group("target") or match.group("js")
        old_rel = f"universities/{path.name}"
        new_rel = f"universities/{Path(target).name}"
        variants = {
            old_rel: new_rel,
            path.name: Path(target).name,
            quote(old_rel): quote(new_rel),
            quote(path.name): quote(Path(target).name),
            old_rel.replace(" ", "%20"): new_rel,
            path.name.replace(" ", "%20"): Path(target).name,
        }
        mapping.update(variants)
    return mapping


def rewrite(text: str, mapping: dict[str, str]) -> str:
    if not text:
        return text
    updated = text
    for old, new in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        if old in updated:
            updated = updated.replace(old, new)
    return updated


def main() -> None:
    mapping = load_redirect_map()
    print("redirect map size", len(mapping))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    updates = [
        ("legacy_admission", "id", "description_html"),
        ("admission_2026_review", "review_key", "burmese_requirements_html"),
        ("detail_section", "id", "content_html"),
    ]
    total = 0
    for table, key, column in updates:
        rows = conn.execute(f"SELECT {key} AS k, {column} AS html FROM {table}").fetchall()
        for row in rows:
            new_html = rewrite(row["html"], mapping)
            if new_html != row["html"]:
                conn.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {key} = ?",
                    (new_html, row["k"]),
                )
                total += 1
    conn.commit()
    print(f"updated {total} html fields")
    conn.close()


if __name__ == "__main__":
    main()
