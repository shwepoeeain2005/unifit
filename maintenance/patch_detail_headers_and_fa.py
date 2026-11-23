"""Add data-unifit header hooks and real Font Awesome SRI on pages."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "universities"
FA = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" '
    'integrity="sha512-12fbfce0caf892a54644d4a02062ff17f6880ea41bef1436bdcadd230c5f8d38521fc09247b3c111a902af9d4293ec3efd4eacc14d889b5bd55f449593d00186" '
    'crossorigin="anonymous" referrerpolicy="no-referrer">'
)
FA_RE = re.compile(r'<link[^>]*font-awesome[^>]*>\s*', re.I)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
LOC_RE = re.compile(r'<p class="location"[^>]*>(.*?)</p>', re.I | re.S)


def ensure_fa(html: str) -> str:
    updated = FA_RE.sub("", html)
    return updated.replace("</head>", f"  {FA}\n</head>", 1)


def patch_university(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    if "this page moved" in original.lower():
        return False
    updated = ensure_fa(original)

    if "data-unifit-name" not in updated:
        h1 = H1_RE.search(updated)
        loc = LOC_RE.search(updated)
        if h1:
            name = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h1.group(1))).strip()
            address = ""
            if loc:
                address = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", loc.group(1))).strip()
            replacement = (
                '<div class="header">\n'
                f'    <h1 data-unifit-name>{name}</h1>\n'
                f'    <p class="location" data-unifit-address>{address}</p>\n'
                "  </div>"
            )
            updated = re.sub(
                r'<div class="header">[\s\S]*?</div>',
                replacement,
                updated,
                count=1,
                flags=re.I,
            )

    updated = updated.replace("?v=2026-admissions-3", "?v=2026-admissions-4")
    updated = re.sub(
        r'university-detail\.js(?:\?v=[^"\']*)?',
        "university-detail.js?v=2026-admissions-4",
        updated,
    )

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = sum(1 for path in sorted(UNI.glob("*.html")) if patch_university(path))
    print(f"university pages updated: {changed}")
    for name in [
        "index.html", "search.html", "unilists.html", "aboutus.html",
        "req1.html", "requirement.html", "formeq.html", "contact.html",
    ]:
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "font-awesome" not in text.lower():
            continue
        updated = ensure_fa(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            print("root", name)


if __name__ == "__main__":
    main()
