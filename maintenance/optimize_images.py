"""Convert JPG/PNG assets to WebP, update DB/HTML refs, remove replaced originals."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "images"
DB = ROOT / "maintenance" / "unifit.sqlite"
MAX_EDGE = 1600
WEBP_QUALITY = 78
EXTS = {".jpg", ".jpeg", ".png"}


def convert_one(path: Path) -> Path | None:
    if path.suffix.lower() not in EXTS:
        return None
    target = path.with_suffix(".webp")
    # Never overwrite a pre-existing WebP that may already be the published asset.
    if target.exists():
        return None
    tmp = path.with_suffix(".tmp.webp")
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            if max(img.size) > MAX_EDGE:
                img.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
            save_kwargs = {"quality": WEBP_QUALITY, "method": 4}
            if path.suffix.lower() == ".png" and img.mode in {"RGBA", "LA", "P"}:
                img = img.convert("RGBA")
            elif img.mode not in {"RGB", "RGBA"}:
                img = img.convert("RGB")
            img.save(tmp, "WEBP", **save_kwargs)
    except Exception as exc:  # noqa: BLE001
        print(f"skip {path.name}: {exc}")
        if tmp.exists():
            tmp.unlink()
        return None

    if not tmp.exists() or tmp.stat().st_size >= path.stat().st_size:
        if tmp.exists():
            tmp.unlink()
        return None
    tmp.replace(target)
    return target


def rewrite_text(text: str, mapping: dict[str, str]) -> str:
    updated = text
    for old, new in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        updated = updated.replace(old, new)
        updated = updated.replace(old.replace("\\", "/"), new)
    return updated


def main() -> None:
    files = [p for p in IMAGES.rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    print(f"candidates: {len(files)}")
    mapping: dict[str, str] = {}
    saved = 0
    converted = 0
    for path in files:
        before = path.stat().st_size
        target = convert_one(path)
        if not target:
            continue
        after = target.stat().st_size
        old_rel = path.relative_to(ROOT).as_posix()
        new_rel = target.relative_to(ROOT).as_posix()
        mapping[old_rel] = new_rel
        # also map path relative to universities pages
        mapping[f"../{old_rel}"] = f"../{new_rel}"
        saved += before - after
        converted += 1
        path.unlink()
        print(f"ok {old_rel} -> {new_rel} ({before/1024:.0f}KB -> {after/1024:.0f}KB)")

    print(f"converted {converted}, saved {saved/1024/1024:.1f} MB")
    if not mapping:
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    updates = 0
    for row in conn.execute("SELECT id, image_path FROM university_card"):
        path = row["image_path"] or ""
        if path in mapping:
            conn.execute(
                "UPDATE university_card SET image_path = ? WHERE id = ?",
                (mapping[path], row["id"]),
            )
            updates += 1

    for row in conn.execute("SELECT section_id, position, image_path FROM section_image"):
        path = row["image_path"] or ""
        new_path = mapping.get(path)
        if not new_path:
            bare = path[3:] if path.startswith("../") else path
            if bare in mapping:
                new_path = f"../{mapping[bare]}" if path.startswith("../") else mapping[bare]
        if new_path and new_path != path:
            conn.execute(
                "UPDATE section_image SET image_path = ? WHERE section_id = ? AND position = ?",
                (new_path, row["section_id"], row["position"]),
            )
            updates += 1

    # HTML content fields may embed image paths
    for table, key, column in [
        ("detail_section", "id", "content_html"),
        ("legacy_admission", "id", "description_html"),
        ("admission_2026_review", "review_key", "burmese_requirements_html"),
    ]:
        for row in conn.execute(f"SELECT {key} AS k, {column} AS html FROM {table}"):
            html = row["html"] or ""
            updated = rewrite_text(html, mapping)
            if updated != html:
                conn.execute(f"UPDATE {table} SET {column} = ? WHERE {key} = ?", (updated, row["k"]))
                updates += 1
    conn.commit()
    conn.close()
    print(f"db fields updated: {updates}")

    # Root HTML/CSS/JS static references (homepage carousel etc.)
    text_files = list(ROOT.glob("*.html")) + list((ROOT / "assets").rglob("*.{css,js,html}"))
    # pathlib doesn't expand braces; do explicit
    text_files = (
        list(ROOT.glob("*.html"))
        + list((ROOT / "assets" / "css").glob("*.css"))
        + list((ROOT / "assets" / "js").glob("*.js"))
        + list((ROOT / "universities").glob("*.html"))
    )
    file_updates = 0
    for path in text_files:
        if "this page moved" in path.read_text(encoding="utf-8", errors="replace").lower():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        updated = rewrite_text(text, mapping)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            file_updates += 1
    print(f"text files updated: {file_updates}")


if __name__ == "__main__":
    main()
