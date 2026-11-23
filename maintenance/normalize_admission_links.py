"""Point local university hrefs at canonical detail_url values from university_card."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "maintenance" / "unifit.sqlite"
LINK = re.compile(r'(href=")([^"]+)(")', re.I)


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    canonical = {
        row["detail_url"].casefold(): row["detail_url"]
        for row in conn.execute("SELECT detail_url FROM university_card")
    }
    # also accept bare filenames
    canonical.update({
        Path(path).name.casefold(): Path(path).name
        for path in canonical.values()
    })

    def fix_html(html: str) -> str:
        def sub(match: re.Match[str]) -> str:
            raw = match.group(2)
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                return match.group(0)
            path = unquote(parts.path)
            canon = canonical.get(path.casefold())
            if not canon:
                return match.group(0)
            if not path.startswith("universities/") and canon.startswith("universities/"):
                # href was bare filename
                pass
            elif path.startswith("universities/") and not canon.startswith("universities/"):
                canon = f"universities/{canon}"
            out = canon
            if parts.query:
                out += f"?{parts.query}"
            if parts.fragment:
                out += f"#{parts.fragment}"
            return f"{match.group(1)}{out}{match.group(3)}"

        return LINK.sub(sub, html)

    # redirect stub map for space renames still referenced oddly
    redirects = {}
    for path in (ROOT / "universities").glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "this page moved" not in text.lower():
            continue
        m = re.search(r"url=([^\"\s>]+)", text)
        if m:
            redirects[f"universities/{path.name}"] = f"universities/{Path(m.group(1)).name}"
            redirects[f"universities/{path.name}".replace(" ", "%20")] = (
                f"universities/{Path(m.group(1)).name}"
            )

    total = 0
    for table, key, column in [
        ("legacy_admission", "id", "description_html"),
        ("admission_2026_review", "review_key", "burmese_requirements_html"),
        ("detail_section", "id", "content_html"),
    ]:
        for row in conn.execute(f"SELECT {key} AS k, {column} AS html FROM {table}"):
            html = row["html"] or ""
            updated = fix_html(html)
            for old, new in sorted(redirects.items(), key=lambda item: len(item[0]), reverse=True):
                updated = updated.replace(old, new)
            updated = fix_html(updated)
            if updated != html:
                conn.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {key} = ?",
                    (updated, row["k"]),
                )
                total += 1
    conn.commit()
    print(f"updated {total} rows")
    conn.close()


if __name__ == "__main__":
    main()
