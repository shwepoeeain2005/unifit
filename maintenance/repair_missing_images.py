"""Repair DB image paths that point at missing files after WebP conversion."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "maintenance" / "unifit.sqlite"


def resolve(path: str) -> str | None:
    raw = path or ""
    candidates = [ROOT / raw]
    if raw.startswith("../"):
        candidates.append(ROOT / raw[3:])
    for candidate in candidates:
        if candidate.exists():
            return path
    # try alternate extensions
    stem_paths = []
    for candidate in candidates:
        stem_paths.extend([
            candidate.with_suffix(".webp"),
            candidate.with_suffix(".jpg"),
            candidate.with_suffix(".jpeg"),
            candidate.with_suffix(".png"),
        ])
    for alt in stem_paths:
        if alt.exists():
            rel = alt.relative_to(ROOT).as_posix()
            if path.startswith("../"):
                return f"../{rel}"
            return rel
    return None


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    fixed = 0
    missing = []

    for row in conn.execute("SELECT id, image_path FROM university_card"):
        path = row["image_path"] or ""
        if (ROOT / path).exists():
            continue
        repaired = resolve(path)
        if repaired and repaired != path:
            conn.execute("UPDATE university_card SET image_path = ? WHERE id = ?", (repaired, row["id"]))
            fixed += 1
            print("card", row["id"], path, "->", repaired)
        else:
            missing.append(("card", row["id"], path))

    for row in conn.execute("SELECT section_id, position, image_path FROM section_image"):
        path = row["image_path"] or ""
        disk = ROOT / (path[3:] if path.startswith("../") else path)
        if disk.exists():
            continue
        repaired = resolve(path)
        if repaired and repaired != path:
            conn.execute(
                "UPDATE section_image SET image_path = ? WHERE section_id = ? AND position = ?",
                (repaired, row["section_id"], row["position"]),
            )
            fixed += 1
        else:
            missing.append(("section", row["section_id"], path))

    conn.commit()
    print(f"fixed {fixed}; still missing {len(missing)}")
    for item in missing[:20]:
        print("MISSING", item)
    conn.close()


if __name__ == "__main__":
    main()
