"""Build the six reviewed detail pages using existing UniFit layouts and content."""

from hashlib import sha256
from html import escape
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
POLYTECHNIC_TEMPLATE = "PU(Bamaw).html"
EDUCATION_TEMPLATE = "Katha Education College.html"
ENGINEERING = [
    "Civil Engineering", "Mechanical Engineering", "Electrical Power Engineering",
    "Electronic Engineering",
]
COMPUTING = ["Computer Science", "Computer Technology"]
CEIT = ("tumawlamyine.html", "Computer Engineering & Information Technology")
EXTRA_MAJORS = {"Taunggyi": [CEIT, ("taunggyi(tu).html", "Mining Engineering")],
                "Mawlamyine": [CEIT]}
REFERENCES = {
    "Myitkyina": ("https://www.moi.gov.mm/moi%3Aeng/news/19980", "Ministry of Information opening notice"),
    "Taunggyi": ("https://www.myanmaritv.com/news/visiting-taunggyi-tu-union-minister-inspects-taunggyi-technological-university",
                 "State broadcaster report on the polytechnic site"),
    "Mawlamyine": ("https://gad.gov.mm/public/index.php/news/1110", "Government polytechnic project notice"),
    "Taungoo Education Degree College": ("https://moe.gov.mm/en/node/5540", "Ministry of Education college notice"),
}


def original_section(db, page, title):
    row = db.execute(
        "SELECT id, content_html FROM detail_section WHERE page_path=? AND title=?", (page, title)
    ).fetchone()
    images = db.execute(
        "SELECT image_path, alt_text FROM section_image WHERE section_id=? ORDER BY position", (row[0],)
    ).fetchall()
    return title, row[1], images


def section(title, content, images=()):
    return title, f'<div class="accordion-content">{content}</div>', images


def references(name):
    if name in REFERENCES:
        url, label = REFERENCES[name]
        link = f'<p><a href="{escape(url)}">{escape(label)}</a></p>'
    else:
        link = ""
    return section("Website links", link + "<p>Campus website pending verification.</p>")


def render(db, url, name, location, template, sections):
    db.execute("INSERT OR IGNORE INTO source_page VALUES (?, ?)",
               (url, sha256((ROOT / url).read_bytes()).hexdigest()))
    db.execute("""
        INSERT OR IGNORE INTO detail_page (page_path, export_key)
        SELECT ?, COALESCE(MAX(export_key), 0) + 1 FROM detail_page
    """, (url,))
    export_key, = db.execute("SELECT export_key FROM detail_page WHERE page_path=?", (url,)).fetchone()
    for position, (title, content, images) in enumerate(sections, 1):
        for image, _ in images:
            if not (ROOT / image).is_file():
                raise ValueError(f"Missing image for {url}: {image}")
        db.execute("""
            INSERT INTO detail_section (page_path, position, title, content_html) VALUES (?, ?, ?, ?)
            ON CONFLICT(page_path, position) DO UPDATE SET title=excluded.title, content_html=excluded.content_html
        """, (url, position, title, content))
        section_id, = db.execute("SELECT id FROM detail_section WHERE page_path=? AND position=?",
                                 (url, position)).fetchone()
        db.execute("DELETE FROM section_image WHERE section_id=?", (section_id,))
        db.executemany("INSERT INTO section_image VALUES (?, ?, ?, ?)",
                       [(section_id, n, image, alt) for n, (image, alt) in enumerate(images, 1)])
    db.execute("""
        DELETE FROM section_image WHERE section_id IN (
            SELECT id FROM detail_section WHERE page_path=? AND position>?
        )
    """, (url, len(sections)))
    db.execute("DELETE FROM detail_section WHERE page_path=? AND position>?", (url, len(sections)))

    markup = "\n".join(
        f'    <div class="accordion"><div class="accordion-header">{escape(title)} '
        '<span class="arrow">▶️</span></div><template data-unifit-section></template></div>'
        for title, _, _ in sections
    )
    original = (ROOT / template).read_text(encoding="utf-8")
    original = re.sub(r"<title>.*?</title>", f"<title>{escape(name)}</title>", original, count=1)
    original = re.sub(r"<h1>.*?</h[13]>", f"<h1>{escape(name)}</h1>", original, count=1)
    original = re.sub(r'<p class="location">.*?</p>',
                      f'<p class="location">{escape(location)}</p>', original, count=1)
    content = (
        '<fieldset>\n    <legend>Available ' + ("Subjects" if template == EDUCATION_TEMPLATE else "Majors")
        + '</legend>\n' + markup + '\n  </fieldset>\n'
        + f'<script src="data/details/{export_key}.js"></script>\n'
        + '<script src="assets/js/university-detail.js"></script>'
    )
    updated, count = re.subn(r"<fieldset>.*?</fieldset>", lambda _: content, original, count=1, flags=re.S)
    if count != 1 or updated.count("data-unifit-section") != len(sections):
        raise ValueError(f"Invalid detail page template: {template}")
    (ROOT / url).write_text(updated, encoding="utf-8")


def build(db):
    for url, name, location in db.execute("""
        SELECT detail_url, university, location
        FROM regional_polytechnic_campus ORDER BY technology_card_id
    """).fetchall():
        campus = name.removeprefix("Polytechnic University (").removesuffix(")")
        majors = [(POLYTECHNIC_TEMPLATE, major) for major in ENGINEERING]
        majors += EXTRA_MAJORS.get(campus, [])
        majors += [(POLYTECHNIC_TEMPLATE, major) for major in COMPUTING]
        sections = [original_section(db, source, title) for source, title in majors]
        sections.append(references(campus))
        render(db, url, name, location, POLYTECHNIC_TEMPLATE, sections)

    for college in ("Sagaing Education Degree College", "Taungoo Education Degree College"):
        location, image, url = db.execute(
            "SELECT address, image_path, detail_url FROM university_card WHERE name=?", (college,)
        ).fetchone()
        overview = (
            "<p>The 2026 guide lists four-year B.A. (Education) and B.Sc. (Education) programs "
            "for Education Degree Colleges, with primary and middle-school teaching specializations.</p>"
            f'<div class="images"><img src="{escape(image)}" alt="{escape(college)}"></div>'
        )
        sections = [section("Education Programs", overview, [(image, college)])]
        for title in ("First and Second Year", "Third and Fourth Year"):
            _, content, images = original_section(db, EDUCATION_TEMPLATE, title)
            content = content.replace('<div class="accordion-content">',
                                      '<div class="accordion-content"><p>Sample teacher-training subjects from the existing UniFit education-college profile. Confirm the exact subject list with the college.</p>', 1)
            sections.append((title, content, images))
        sections.append(references(college))
        render(db, url, college, location, EDUCATION_TEMPLATE, sections)


if __name__ == "__main__":
    database = ROOT / "maintenance/unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        build(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
