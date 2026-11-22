"""Publish the verified 2026 wording for the seven existing regional polytechnics."""

from html import escape
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CAMPUSES = {"Bhamo": "Banmaw", "Lashio": "Lashio", "Kengtung": "Kyaing Tong",
            "Panglong": "Panglong", "Maubin": "Maubin", "Dawei": "Dawei", "Myeik": "Myeik"}
ADDITIONAL_CAMPUSES = {
    "Myitkyina": ("Myitkyina, Kachin State", 27, 47, None, 724),
    "Taunggyi": ("Taunggyi, Shan State", 33, 53, 710, 728),
    "Mawlamyine": ("Mawlamyine, Mon State", 41, None, 706, None),
    "Loikaw": ("Loikaw, Kayah State", 34, 54, 707, 722),
}


def publish(db):
    for campus, legacy_campus in CAMPUSES.items():
        for route, legacy_route, degree, ranking in (
            ("Engineering", "Engineering", "၅ နှစ် (B.E.)",
             "အင်္ဂလိပ်စာ၊ သင်္ချာ၊ ဓာတုဗေဒနှင့် ရူပဗေဒ လေးဘာသာပေါင်းရမှတ်"),
            ("Computer Science and Technology", "Computer Science & Computer Technology",
             "၄ နှစ် (B.C.Sc. / B.C.Tech.)", "တက္ကသိုလ်ဝင်စာမေးပွဲ စုစုပေါင်းရမှတ်"),
        ):
            legacy_id, description = db.execute(
                "SELECT id, description_html FROM legacy_admission WHERE university_group=? AND name=?",
                (f"Polytechnic University ({legacy_campus})", legacy_route),
            ).fetchone()
            link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', description, re.I)
            if link is None or not (ROOT / unquote(link[1])).is_file():
                raise ValueError(f"Missing detail page for {campus}")
            key = f"polytechnic:{campus}:{route}"
            existing, status = db.execute(
                "SELECT burmese_requirements_html, review_status FROM admission_2026_review WHERE review_key=?", (key,)
            ).fetchone()
            if status == "published — regional wording only":
                continue
            updated = (
                existing + "\nသတ်မှတ်ထားသော ဝင်ခွင့်လျှောက်လွှာစာအိတ်ပါ ပုံစံများဖြင့် လျှောက်ထားရမည်။ "
                "ဦးစားပေးအစီအစဉ်တွင် သက်ဆိုင်ရာ Polytechnic University နှင့် လျှောက်ထားမည့် သင်တန်းအမျိုးအစားကို ဖော်ပြရမည်။\n"
                "နိုင်ငံသားစိစစ်ရေးကတ်ပြား (နိုင်)/(ပြု)/(ဧည့်) ကိုင်ဆောင်ထားရမည်။ "
                "လက်တွေ့လုပ်ငန်းနှင့် ကွင်းဆင်းလေ့လာမှုများတွင် ပါဝင်ဆောင်ရွက်နိုင်ရမည်။\n"
                f"သင်တန်းကာလမှာ {degree} ဖြစ်သည်။ သတ်မှတ်လက်ခံဦးရေအတွင်း {ranking} အလိုက် စိစစ်ရွေးချယ်မည်။\n\n"
                + link[0]
            )
            db.execute("""
                UPDATE admission_2026_review
                SET legacy_id=?, burmese_requirements_html=?, review_status='published — regional wording only'
                WHERE review_key=?
            """, (legacy_id, updated, key))


def publish_additional_campuses(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS regional_polytechnic_campus (
            technology_card_id INTEGER PRIMARY KEY REFERENCES university_card(id),
            computing_card_id INTEGER UNIQUE REFERENCES university_card(id),
            university TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL,
            detail_url TEXT NOT NULL UNIQUE
        )
    """)
    for campus, (location, technology_card, computing_card, engineering_id, computing_id) in ADDITIONAL_CAMPUSES.items():
        university = f"Polytechnic University ({campus})"
        url = f"polytechnic-{campus.lower()}.html"
        db.execute("INSERT OR IGNORE INTO regional_polytechnic_campus VALUES (?, ?, ?, ?, ?)",
                   (technology_card, computing_card, university, location, url))
        references = []
        for card, label in ((technology_card, "Engineering information from the former UniFit listing"),
                            (computing_card, "Computing information from the former UniFit listing")):
            if card is not None:
                target, = db.execute("SELECT detail_url FROM university_card WHERE id=?", (card,)).fetchone()
                if not (ROOT / target).is_file():
                    raise ValueError(f"Missing legacy page for {campus}")
                references.append(f'<li><a href="{escape(target)}">{label}</a></li>')
        descriptions = []
        for route, old_id in (("Engineering", engineering_id),
                              ("Computer Science and Technology", computing_id)):
            original, = db.execute("SELECT burmese_requirements_html FROM admission_2026_review WHERE review_key=?",
                                   (f"polytechnic:Bhamo:{route}",)).fetchone()
            wording = original.split("\n\n<a", 1)[0]
            descriptions.append(f"<h2>{route}</h2><p>{escape(wording).replace(chr(10), '<br>')}</p>")
            cursor = db.execute("""
                UPDATE admission_2026_review
                SET legacy_id=?, burmese_requirements_html=?, review_status='published — regional polytechnic'
                WHERE review_key=?
            """, (old_id, wording + f'\n\n<a href="{url}" target="_blank" style="font-weight: bold; font-size: 15px;">more details</a>',
                  f"polytechnic:{campus}:{route}"))
            if cursor.rowcount != 1:
                raise ValueError(f"Missing 2026 draft for {university}, {route}")
        if (ROOT / url).exists():
            continue
        (ROOT / url).write_text(f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{university}</title>
  <link rel="stylesheet" href="nav.css">
</head>
<body>
  <div id="navbar"></div>
  <main style="max-width: 850px; margin: 2rem auto; padding: 0 1rem;">
    <p><a href="unilists.html">Back to University List</a></p>
    <h1>{university}</h1>
    <p>{location}</p>
    <h2>2026 admissions</h2>
    <p>University Admissions Guide, printed pages 56–59.</p>
    {''.join(descriptions)}
    <h2>Previous UniFit listings</h2>
    <ul>{''.join(references)}</ul>
    <p><a href="search.html">Search Your Uni</a></p>
  </main>
  <div id="footer"></div>
  <script src="include.js"></script>
</body>
</html>
""", encoding="utf-8")


if __name__ == "__main__":
    database = ROOT / "maintenance/unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        publish_additional_campuses(db)
        count = db.execute("""
            SELECT COUNT(*) FROM admission_2026_review WHERE review_status='published — regional wording only'
        """).fetchone()[0]
        if count != 14 or db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Unexpected result while publishing regional polytechnics")
        print(f"Published {count} wording updates.")
