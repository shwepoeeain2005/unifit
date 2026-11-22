"""Publish the 2026 regular B.A. routes for YUFL and MUFL."""

import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SHARED_PROGRAMS = (
    ("Chinese", None), ("English", 60), ("French", None), ("German", None),
    ("Japanese", None), ("Korean", None), ("Russian", None), ("Thai", None),
)
CAMPUS_PROGRAMS = {
    761: ("English for Professional Communication", 65),
    762: ("English for Business Purposes", 60),
}
PASS = "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်ထားသူဖြစ်ရမည်။ မြန်မာနိုင်ငံတစ်ဝန်းရှိ စာစစ်ဌာနအားလုံးမှ လျှောက်ထားနိုင်သည်။"
IDENTITY = (
    "လျှောက်ထားသူသည် မြန်မာနိုင်ငံသား ဖြစ်ရမည်။ နိုင်ငံသားစိစစ်ရေးကတ်ပြားအမှတ်ကို ဖြည့်စွက်ပြီး မိတ္တူ ပူးတွဲတင်ပြရမည်။ "
    "ကတ်ပြားလျှောက်ထားဆဲ ဖြစ်ပါက သက်ဆိုင်ရာ လူဝင်မှုကြီးကြပ်ရေးဌာန၏ ထောက်ခံစာမူရင်းကို ပူးတွဲတင်ပြရမည်။"
)
DIGITS = str.maketrans("0123456789", "၀၁၂၃၄၅၆၇၈၉")
CHINESE_PROGRAM_SOURCES = {
    761: "https://www.yufl.edu.mm/wp-content/uploads/2016/11/PS-Chi-Dept-24-3-25.pdf",
    762: "https://www.mufl.edu.mm/academic/language/chinese-department.html",
}


def publish(db):
    db.execute("BEGIN IMMEDIATE")
    if "minimum_english" not in {row[1] for row in db.execute("PRAGMA table_info(admission_2026_review)")}:
        db.execute("ALTER TABLE admission_2026_review ADD COLUMN minimum_english INTEGER")
    for legacy_id, special_program in CAMPUS_PROGRAMS.items():
        university, previous = db.execute(
            "SELECT name, description_html FROM legacy_admission WHERE id = ?", (legacy_id,)
        ).fetchone()
        link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', previous, re.I)
        if link is None or not (ROOT / unquote(link[1])).is_file():
            raise ValueError(f"Missing detail link for {university}")
        detail_path = unquote(link[1])
        section_id, = db.execute(
            "SELECT id FROM detail_section WHERE page_path = ? AND position = 1 AND title IN ('Myanmar', 'Chinese')",
            (detail_path,),
        ).fetchone()
        source = CHINESE_PROGRAM_SOURCES[legacy_id]
        chinese_description = f"""<div class="accordion-content">
  <p>Chinese (တရုတ်ဘာသာ) သည် တရုတ်ဘာသာစကားနှင့် စာပေကို အထူးပြုလေ့လာသည့် B.A. ဘွဲ့သင်တန်း ဖြစ်ပါတယ်။
  တရုတ်ဘာသာဖြင့် နားထောင်ခြင်း၊ ပြောဆိုခြင်း၊ ဖတ်ရှုခြင်းနှင့် ရေးသားခြင်းတို့ကို လေ့ကျင့်ရပြီး
  တရုတ်စာပေနှင့် ယဉ်ကျေးမှုကိုပါ လေ့လာနိုင်ပါတယ်။</p>
  <div class="carpath">Career Path</div>
  <p>1. Translator / Interpreter <br>
     2. Language Teacher <br>
     3. Tourism and Hospitality <br>
     4. International Business and Communications</p>
  <p><a href="{source}" target="_blank" rel="noopener">University programme information</a></p>
</div>"""
        db.execute("UPDATE detail_section SET title = 'Chinese', content_html = ? WHERE id = ?",
                   (chinese_description, section_id))
        db.execute("DELETE FROM section_image WHERE section_id = ?", (section_id,))
        for position, (program, english) in enumerate((*SHARED_PROGRAMS, special_program), 1):
            score_rule = "ဤဘာသာရပ်အတွက် ၂၀၂၆ လမ်းညွှန်တွင် သီးခြားအနည်းဆုံးရမှတ် မဖော်ပြထားပါ။"
            if english is not None:
                marks = str(english).translate(DIGITS)
                score_rule = f"တက္ကသိုလ်ဝင်စာမေးပွဲ အင်္ဂလိပ်စာရမှတ် အနည်းဆုံး {marks} မှတ် ရရှိရမည်။"
            title = f"B.A. ({program})"
            description = "\n\n".join([f"{title} ဘွဲ့သင်တန်း။", PASS, score_rule, IDENTITY, link[0]])
            db.execute("""
                INSERT INTO admission_2026_review
                (review_key, legacy_id, university, program, printed_pages, minimum_english,
                 stream_status, region_rule, burmese_requirements_html, review_status)
                VALUES (?, ?, ?, ?, '70–72', ?, 'No stream restriction specified in guide',
                        'Nationwide', ?, 'published — foreign languages')
                ON CONFLICT(review_key) DO UPDATE SET program=excluded.program,
                    minimum_english=excluded.minimum_english, minimum_total=NULL,
                    burmese_requirements_html=excluded.burmese_requirements_html
            """, (f"foreign-languages:{legacy_id}:{position}", legacy_id, university, title, english, description))


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
