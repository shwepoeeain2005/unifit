"""Audit local links in UniFit's HTML and published database exports."""
from collections import Counter, defaultdict
from html.parser import HTMLParser
import json
import posixpath
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.paths = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.paths.extend(value for key, value in attrs if key in {"href", "src", "poster"} and value)

    handle_startendtag = handle_starttag


def load_export(path):
    first_line = path.read_text(encoding="utf-8").partition("\n")[0]
    return json.loads(first_line.split(" = ", 1)[1].removesuffix(";"))


def main():
    files = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
    lower = {path.casefold(): path for path in files}
    counts = Counter()
    problems = defaultdict(set)

    def check(page, references, layer):
        for reference in references:
            url = urlsplit(reference)
            if url.scheme or url.netloc or not url.path:
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(page), unquote(url.path)))
            counts[layer] += 1
            if path not in files:
                candidate = lower.get(path.casefold())
                reason = f"case mismatch, use {candidate}" if candidate else "missing"
                problems[(layer, reference, reason)].add(page)
            elif path.lower().endswith(".html") and (ROOT / path).stat().st_size == 0:
                problems[(layer, reference, "empty detail page")].add(page)

    for path in sorted(ROOT.rglob("*.html")):
        page = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8-sig")
        check(page, References(source).paths, "HTML")

    for path in sorted(ROOT.rglob("*.css")):
        page = path.relative_to(ROOT).as_posix()
        check(page, re.findall(r"""url\(\s*['"]?([^'"()]+?)['"]?\s*\)""",
                              path.read_text(encoding="utf-8-sig")), "CSS")

    routes = load_export(ROOT / "data/admissions.js")
    for row in routes:
        check("search.html", [row["detailUrl"]], "search results")

    for row in load_export(ROOT / "data/universities.js"):
        check("unilists.html", filter(None, (row["detail_url"], row["image_path"])), "list cards")

    database = ROOT / "maintenance/unifit.sqlite"
    detail_anchors = {}
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        for page, key in db.execute("SELECT page_path, export_key FROM detail_page"):
            detail = load_export(ROOT / "data/details" / f"{key}.js")
            sections = detail["sections"]
            expected = db.execute("SELECT COUNT(*) FROM detail_section WHERE page_path = ?", (page,)).fetchone()[0]
            assert len(sections) == expected, f"Stale detail export: {page}"
            for section in sections:
                check(page, [image["image_path"] for image in section["images"]], "detail images")
            if detail["admissions"] is not None:
                admissions = detail["admissions"]
                detail_anchors[page] = {"admission-requirements", *(item["id"] for item in admissions["programmes"])}
                rules = [*admissions["shared"], *(rule for item in admissions["programmes"] for rule in item["rules"])]
                check(page, References("\n".join(rules)).paths, "admission requirements")
    for row in routes:
        url = urlsplit(row["detailUrl"])
        if url.fragment not in detail_anchors.get(unquote(url.path), ()):
            problems[("search results", row["detailUrl"], "missing admission target")].add("search.html")

    for layer, count in sorted(counts.items()):
        print(f"{layer}: {count} local references")
    for (layer, path, reason), pages in sorted(problems.items()):
        print(f"{layer}: {path} [{reason}] -- {len(pages)} page(s), e.g. {min(pages)}")


if __name__ == "__main__":
    main()
