"""Data cleanup + canonical university slugs + redirect stubs."""
from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "maintenance" / "unifit.sqlite"
UNI = ROOT / "universities"

NAME_FIXES = {
    70: "Government Technological College(South Dagon)",
    71: "Government Technological College(Mandalay)",
    72: "Government Technological College(Shwebo)",
    73: "Government Technological College(Kyauk Phyu)",
    123: "Co-operative College(Phaunggyi)",
    124: "Co-operative College(Mandalay)",
}

ADDRESS_FIXES = {
    3: "📍 30th Street, Between 73rd & 74th Streets, Mandalay, Mandalay Region, Myanmar",
    107: "📍 Ann Road, Kai Shay Quarter, Taunggoke, Rakhine State, Myanmar",
}

IMAGE_RENAMES = {
    "assets/images/monywa Univerrsity.jpg": "assets/images/monywa-university.jpg",
    "assets/images/Co-operativve College(Mandalay).jpg": "assets/images/Co-operative College(Mandalay).jpg",
}


def slugify(stem: str) -> str:
    text = stem.strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "campus"


def unique_slug(stem: str, used: set[str]) -> str:
    base = slugify(stem)
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}-{n}"
        n += 1
    used.add(candidate)
    return candidate


def redirect_html(target_rel: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url={target_rel}">
  <link rel="canonical" href="{target_rel}">
  <title>Moved</title>
  <script>location.replace({target_rel!r});</script>
</head>
<body>
  <p>This page moved to <a href="{target_rel}">{target_rel}</a>.</p>
</body>
</html>
"""


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")

    # --- typo / address / image cleanup ---
    for card_id, name in NAME_FIXES.items():
        conn.execute("UPDATE university_card SET name = ? WHERE id = ?", (name, card_id))
        print(f"renamed card {card_id} -> {name}")
    for card_id, address in ADDRESS_FIXES.items():
        conn.execute("UPDATE university_card SET address = ? WHERE id = ?", (address, card_id))
        print(f"fixed address {card_id}")

    for old, new in IMAGE_RENAMES.items():
        old_path = ROOT / old
        new_path = ROOT / new
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            print(f"renamed image {old} -> {new}")
        elif not old_path.exists() and new_path.exists():
            print(f"image already renamed: {new}")
        conn.execute(
            "UPDATE university_card SET image_path = ? WHERE image_path = ?",
            (new, old),
        )

    # --- slug migration ---
    html_files = sorted(UNI.glob("*.html"))
    mapping: dict[str, str] = {}
    used_slugs: set[str] = set()
    stem_fixes = {
        "Dawei Education Degree Collage": "Dawei Education Degree College",
        "Hakha Education Degree Collage": "Hakha Education Degree College",
        "Loikaw Education Degree Collage": "Loikaw Education Degree College",
        "Monywa Education degree Collage": "Monywa Education Degree College",
    }

    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'http-equiv="refresh"' in text.lower() and "this page moved" in text.lower():
            continue
        old_rel = f"universities/{path.name}"
        stem = stem_fixes.get(path.stem, path.stem)
        new_name = f"{unique_slug(stem, used_slugs)}.html"
        new_rel = f"universities/{new_name}"
        mapping[old_rel] = new_rel

    changed = {old: new for old, new in mapping.items() if old != new}
    print(f"slug renames: {len(changed)}")

    for old, new in sorted(changed.items()):
        exists = conn.execute("SELECT 1 FROM source_page WHERE path = ?", (old,)).fetchone()
        if exists:
            target_exists = conn.execute("SELECT 1 FROM source_page WHERE path = ?", (new,)).fetchone()
            if target_exists:
                raise SystemExit(f"source_page already has {new}")
            conn.execute("UPDATE source_page SET path = ? WHERE path = ?", (new, old))
        conn.execute("UPDATE detail_page SET page_path = ? WHERE page_path = ?", (new, old))
        conn.execute("UPDATE detail_section SET page_path = ? WHERE page_path = ?", (new, old))
        conn.execute("UPDATE university_card SET detail_url = ? WHERE detail_url = ?", (new, old))
        conn.execute(
            "UPDATE regional_polytechnic_campus SET detail_url = ? WHERE detail_url = ?",
            (new, old),
        )
        # admission HTML may still mention old paths; export regenerates search links

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        raise SystemExit(f"foreign key problems: {fk[:5]}")

    # Rename files and write redirect stubs
    for old, new in sorted(changed.items()):
        old_path = ROOT / old
        new_path = ROOT / new
        if not old_path.exists():
            print("missing file", old)
            continue
        if new_path.exists() and old_path.resolve() != new_path.resolve():
            raise SystemExit(f"target exists: {new}")
        shutil.move(str(old_path), str(new_path))
        # old_path is now gone; write redirect at old location
        old_path.write_text(redirect_html(Path(new).name), encoding="utf-8")
        print(f"slug {old} -> {new}")

    # Update campusAliases will be handled in JS via export; also patch any hardcoded HTML links? none expected.
    conn.close()
    print("done")


if __name__ == "__main__":
    main()
