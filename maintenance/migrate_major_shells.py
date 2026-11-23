"""Replace hand-maintained major accordions with SQLite-driven shells."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI_DIR = ROOT / "universities"

FIELDSET_RE = re.compile(r"<fieldset\b([^>]*)>(.*?)</fieldset>", re.I | re.S)
LEGEND_RE = re.compile(r"<legend\b[^>]*>.*?</legend>", re.I | re.S)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.I | re.S)
DETAIL_SCRIPT_RE = re.compile(
    r'<script\b[^>]*src=["\']\.\./(?:data/details/[^"\']+|assets/js/university-detail\.js[^"\']*)["\'][^>]*>\s*</script>',
    re.I,
)
ACCORDION_SCRIPT_RE = re.compile(
    r"<script>\s*//\s*Accordion toggle[\s\S]*?</script>\s*",
    re.I,
)


def migrate(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    if "this page moved" in original.lower() and 'http-equiv="refresh"' in original.lower():
        return False
    match = FIELDSET_RE.search(original)
    if not match:
        raise SystemExit(f"No fieldset in {path.name}")

    attrs = match.group(1)
    body = match.group(2)
    legend = LEGEND_RE.search(body)
    if not legend:
        raise SystemExit(f"No legend in {path.name}")

    scripts = DETAIL_SCRIPT_RE.findall(body)
    # Also catch detail scripts that appear after fieldset already
    existing_after = DETAIL_SCRIPT_RE.findall(original[match.end(): match.end() + 400])

    if 'data-unifit-majors' not in attrs:
        attrs = (attrs + ' data-unifit-majors').replace("  ", " ")

    replacement = f"<fieldset{attrs}>\n    {legend.group(0)}\n  </fieldset>"
    updated = original[: match.start()] + replacement + original[match.end():]

    # Ensure detail scripts sit right after the fieldset once
    updated = DETAIL_SCRIPT_RE.sub("", updated)
    script_block = "\n".join(
        s.replace("?v=2026-admissions-2", "?v=2026-admissions-3")
        if "university-detail.js" in s or "data/details/" in s
        else s
        for s in (scripts or existing_after)
    )
    # If scripts were only outside originally, keep those paths with bumped version
    if not script_block:
        loose = DETAIL_SCRIPT_RE.findall(original)
        script_block = "\n".join(
            s.replace("?v=2026-admissions-2", "?v=2026-admissions-3") for s in loose
        )
    if not script_block:
        raise SystemExit(f"Missing detail scripts in {path.name}")

    # Normalize versions
    script_block = script_block.replace("?v=2026-admissions-2", "?v=2026-admissions-3")
    if "?v=2026-admissions-3" not in script_block and "university-detail.js" in script_block:
        script_block = script_block.replace(
            "university-detail.js",
            "university-detail.js?v=2026-admissions-3",
        )

    fieldset_match = FIELDSET_RE.search(updated)
    insert_at = fieldset_match.end()
    updated = updated[:insert_at] + "\n" + script_block + "\n" + updated[insert_at:]
    updated = ACCORDION_SCRIPT_RE.sub("", updated)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    for path in sorted(UNI_DIR.glob("*.html")):
        if migrate(path):
            changed += 1
            print(f"updated: {path.name}")
    print(f"done: {changed} files updated")


if __name__ == "__main__":
    main()
