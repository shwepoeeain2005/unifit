"""Sync confirmed arts and science major differences into campus detail pages."""

import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
ADD = {
    "Hpa-An University.html": ("Biochemistry", "Creative Writing", "Environmental Studies"),
    "Magway University.html": ("Creative Writing",),
    "Mandalar university.html": ("Environmental Science",),
    "Maubin University.html": ("Environmental Science",),
    "Mawlamyine.html": ("Economics", "Marine Science", "Oriental Studies", "Philosophy"),
    "Meiktila University.html": ("Law",),
    "Monywa University.html": ("International Relations",),
    "Myeik University.html": ("Marine Science",),
    "Myitkyina University.html": ("Creative Writing",),
    "Sagaing University.html": ("Creative Writing",),
    "Shwebo University.html": ("Creative Writing",),
    "Yadanarbon University.html": ("Environmental Studies",),
    "Yenanchaung University.html": ("Petroleum Geology",),
    "Naypitaw State Academy.html": ("Library and Information Studies", "Diplomacy", "Industrial Chemistry", "Nuclear Physics"),
    "Mandalar university.html": ("Tourism and Hospitality Management",),
    "University of Veterinary Science.html": ("Bachelor of Animal Science (BASc)",),
    "Government Technological College(Mandalay).html": ("Electronics", "Information Technology"),
    "Government Technological College(South Dagon).html": ("Electronics", "Information Technology"),
}
REMOVE = {
    "Bago University.html": "Economics",
    "Yadanarbon University.html": "Biotechnology",
    "Naypitaw State Academy.html": "Psychology",
}
ACADEMY_TITLES = {
    (9, "Law"): "Law (LL.B. and B.A. (Law))",
    (10, "Economics"): "Economics (B.A.)",
    (13, "Economics"): "Economics (B.Econ.)",
    (14, "Statistics"): "Statistics (B.Econ.)",
    (17, "Economics"): "Banking and Finance (BBF)",
}
SPECIAL_CONTENT = {
    "Bachelor of Animal Science (BASc)": (
        "မွေးမြူရေးပညာဘွဲ့ (BASc) သည် လေးနှစ်သင်တန်းဖြစ်ပြီး တိရစ္ဆာန်မျိုးပွားခြင်း၊ အာဟာရနှင့် မွေးမြူရေးစီမံခန့်ခွဲမှုတို့ကို လေ့လာရပါတယ်။",
        "Animal Production Officer <br> Farm Manager <br> Animal Nutrition Assistant",
    ),
    "Diplomacy": (
        "သံတမန်ရေးရာပညာမှာ နိုင်ငံများအကြား ဆက်သွယ်ညှိနှိုင်းမှု၊ နိုင်ငံခြားရေးမူဝါဒနှင့် သံတမန်လုပ်ငန်းတို့ကို လေ့လာပါတယ်။",
        "International Relations Researcher <br> Programme Officer",
    ),
    "Banking and Finance (BBF)": (
        "ဘဏ်လုပ်ငန်းနှင့် ဘဏ္ဍာရေးပညာမှာ ငွေကြေးစီမံခန့်ခွဲမှု၊ ချေးငွေ၊ ရင်းနှီးမြှုပ်နှံမှုနှင့် ဘဏ္ဍာရေးအန္တရာယ်တို့ကို လေ့လာပါတယ်။",
        "Bank Officer <br> Financial Analyst",
    ),
    "Electronics": (
        "အီလက်ထရွန်နစ်ပညာမှာ လျှပ်စစ်ပတ်လမ်းများ၊ အချက်ပြစနစ်များနှင့် အီလက်ထရွန်နစ်ပစ္စည်းများကို တိုင်းတာစမ်းသပ်ပုံတို့ကို လေ့လာပါတယ်။",
        "Electronics Technician <br> Technical Support Specialist",
    ),
    "Information Technology": (
        "သတင်းအချက်အလက်နည်းပညာမှာ ကွန်ပျူတာစနစ်များ၊ ကွန်ရက်များ၊ ပရိုဂရမ်ရေးသားခြင်းနှင့် ဒေတာကို စနစ်တကျ ကိုင်တွယ်ပုံတို့ကို လေ့လာပါတယ်။",
        "IT Support Specialist <br> Network Technician <br> Software Developer",
    ),
}
PETROLEUM = """<div class="accordion-content">
  <p>ရေနံဘူမိဗေဒ (Petroleum Geology) မှာ ရေနံနှင့် သဘာဝဓာတ်ငွေ့ ဖြစ်ပေါ်ပုံ၊
  ကျောက်လွှာများအတွင်း စုဝေးနေထိုင်ပုံနဲ့ သိုက်တည်နေရာ ရှာဖွေဖော်ထုတ်ပုံတို့ကို လေ့လာပါတယ်။
  ကျောက်လွှာအစီအစဉ်၊ အနည်ကျကျောက်များနှင့် မြေအောက်ဘူမိဗေဒ အချက်အလက်များကို ဆန်းစစ်ရပါတယ်။</p>
  <div class="carpath">Career Path</div>
  <p>1. Petroleum Geologist <br>2. Exploration Geologist <br>3. Geological Data Analyst</p>
</div>"""
ACCORDION = (
    '<div class="accordion">\n'
    '  <div class="accordion-header">{title}<span class="arrow">▶️</span></div>\n'
    '  <template data-unifit-section></template>\n'
    '</div>\n'
)


def major_content(db, title):
    if title == "Petroleum Geology":
        return PETROLEUM, []
    if title in SPECIAL_CONTENT:
        description, careers = SPECIAL_CONTENT[title]
        return f'<div class="accordion-content"><p>{description}</p><div class="carpath">Career Path</div><p>{careers}</p></div>', []
    for section_id, content in db.execute(
        "SELECT id, content_html FROM detail_section WHERE title = ? ORDER BY id", (title,)
    ):
        images = db.execute(
            "SELECT image_path, alt_text FROM section_image WHERE section_id = ? ORDER BY position", (section_id,)
        ).fetchall()
        valid = [image for image in images if (ROOT / unquote(image[0])).is_file()]
        if images and not valid:
            continue
        return remove_missing_images(content), valid
    # Reuse the description even when all of its original photos are missing.
    content, = db.execute(
        "SELECT content_html FROM detail_section WHERE title = ? ORDER BY id LIMIT 1", (title,)
    ).fetchone()
    return remove_missing_images(content), []


def remove_missing_images(content):
    return re.sub(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>',
                  lambda match: match[0] if (ROOT / unquote(match[1])).is_file() else "", content)


def update_academy_labels(db, html):
    for (position, old), new in ACADEMY_TITLES.items():
        section_id, title = db.execute(
            "SELECT id, title FROM detail_section WHERE page_path = 'Naypitaw State Academy.html' AND position = ?",
            (position,),
        ).fetchone()
        if title == new:
            continue
        if title != old:
            raise ValueError(f"Unexpected academy major at position {position}: {title}")
        headers = list(re.finditer(r'(<div class="accordion-header"[^>]*>)([^<]+)(<span class="arrow">)', html))
        header = headers[position - 1]
        if header[2].strip() != old:
            raise ValueError(f"Academy label does not match at position {position}")
        html = html[:header.start(2)] + new + html[header.end(2):]
        db.execute("UPDATE detail_section SET title = ? WHERE id = ?", (new, section_id))
        if new in SPECIAL_CONTENT:
            content, _ = major_content(db, new)
            db.execute("UPDATE detail_section SET content_html = ? WHERE id = ?", (content, section_id))
            db.execute("DELETE FROM section_image WHERE section_id = ?", (section_id,))
    return html


def sync(db):
    changes = {}
    for file in sorted(ADD.keys() | REMOVE.keys()):
        path = ROOT / file
        html = path.read_bytes().decode("utf-8")
        if file == "Naypitaw State Academy.html":
            html = update_academy_labels(db, html)
        sections = {title: (id_, position) for id_, position, title in db.execute(
            "SELECT id, position, title FROM detail_section WHERE page_path = ?", (file,)
        )}
        remove = REMOVE.get(file)
        if remove in sections:
            block = re.compile(
                r'<div class="accordion">\s*<div class="accordion-header">\s*' + re.escape(remove)
                + r'\s*<span class="arrow">[^<]*</span></div>\s*<template data-unifit-section></template>\s*</div>'
            )
            html, removed = block.subn("", html, count=1)
            if removed != 1:
                raise ValueError(f"Missing {remove} accordion in {file}")
            section_id, _ = sections.pop(remove)
            db.execute("DELETE FROM section_image WHERE section_id = ?", (section_id,))
            db.execute("DELETE FROM detail_section WHERE id = ?", (section_id,))
        additions = [title for title in ADD.get(file, ()) if title not in sections]
        if additions:
            website = sections.get("Website link") or sections.get("Website Link")
            if website:
                website_id, position = website
                marker = re.search(r'<div class="accordion">\s*<div class="accordion-header"[^>]*>\s*Website link', html, re.I)
                if marker is None:
                    raise ValueError(f"Missing website accordion in {file}")
                index = marker.start()
                db.execute("UPDATE detail_section SET position = ? WHERE id = ?",
                           (position + len(additions), website_id))
            else:
                index = html.index("</fieldset>")
                position = max(value[1] for value in sections.values()) + 1
            html = html[:index] + "".join(ACCORDION.format(title=title) for title in additions) + html[index:]
            for offset, title in enumerate(additions):
                content, images = major_content(db, title)
                cursor = db.execute(
                    "INSERT INTO detail_section (page_path, position, title, content_html) VALUES (?, ?, ?, ?)",
                    (file, position + offset, title, content),
                )
                db.executemany("INSERT INTO section_image VALUES (?, ?, ?, ?)", (
                    (cursor.lastrowid, number, *image) for number, image in enumerate(images, 1)
                ))
        expected, = db.execute("SELECT COUNT(*) FROM detail_section WHERE page_path = ?", (file,)).fetchone()
        if html.count("template data-unifit-section") != expected:
            raise ValueError(f"Detail placeholders and SQLite records disagree for {file}")
        if html.rfind("template data-unifit-section") > html.index('src="assets/js/university-detail.js'):
            scripts = re.compile(
                r'<script src="data/details/[^"]+"></script>\s*'
                r'<script src="assets/js/university-detail\.js(?:\?[^"]*)?"></script>'
            )
            block = scripts.search(html)
            if block is None:
                raise ValueError(f"Missing detail scripts in {file}")
            html = scripts.sub("", html, count=1)
            html = html.replace("</fieldset>", "</fieldset>\n" + block[0], 1)
        changes[path] = html
    return changes


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        changes = sync(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
    for path, html in changes.items():
        path.write_bytes(html.encode("utf-8"))
