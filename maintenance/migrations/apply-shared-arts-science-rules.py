"""Apply the verified common arts and sciences conditions from guide pages 73–75."""
from pathlib import Path
import re
import sqlite3

DATABASE = Path(__file__).resolve().with_name("unifit.sqlite")
INTERVIEW = "လူတွေ့စစ်ဆေးမှု ခံယူရမည်။"
GEOLOGY = (
    "ဘူမိဗေဒအတွက် တက္ကသိုလ်အလိုက် ဝင်ခွင့်ပြုဦးရေ၏ ၁၀ ရာခိုင်နှုန်းအထိ အမျိုးသမီးများကို လက်ခံမည်။ "
    "သတ်မှတ်စည်းမျဉ်းအရ မိုင် ၂၀ လမ်းလျှောက်နိုင်ရမည်။ "
    "ကျန်းမာရေး (က) အဆင့် ရရှိရမည်ဖြစ်ပြီး အမြင်နှင့် အရောင်ခွဲခြားနိုင်စွမ်း စစ်ဆေးမှု ခံယူရမည်။"
)
MARINE = (
    "၂၀၂၆ တက္ကသိုလ်ဝင်စာမေးပွဲကို STEAMS-1 သို့မဟုတ် STEAMS-2 ဘာသာတွဲဖြင့် အောင်မြင်ရမည်။\n"
    "လူတွေ့စစ်ဆေးမှု ခံယူရမည်။ လျှောက်ထားလိုသော တက္ကသိုလ်များကို ဦးစားပေးအစီအစဉ်အလိုက် ဖော်ပြရမည်။\n"
    "နိုင်ငံသားစိစစ်ရေးကတ်ပြား သို့မဟုတ် လမ်းညွှန်တွင် သတ်မှတ်ထားသော အထောက်အထားကို ပူးတွဲတင်ပြရမည်။"
)


def apply(db):
    additions = {25: INTERVIEW, 33: INTERVIEW, 39: GEOLOGY,
                 57: INTERVIEW, 64: INTERVIEW, 70: GEOLOGY}
    for admission_id, condition in additions.items():
        text, pages = db.execute("""
            SELECT burmese_requirements_html, printed_pages FROM admission_2026_review WHERE legacy_id=?
        """, (admission_id,)).fetchone()
        if condition not in text:
            body, link = text.split("\n\n<a", 1)
            db.execute("""
                UPDATE admission_2026_review SET burmese_requirements_html=?, printed_pages=? WHERE legacy_id=?
            """, (body + "\n" + condition + "\n\n<a" + link, pages + ", 73–75", admission_id))

    for admission_id in (86, 105, 125, 141):
        name, university, previous, total, minimums = db.execute("""
            SELECT name, university_group, description_html, required_total, subject_minimums_json
            FROM legacy_admission WHERE id=?
        """, (admission_id,)).fetchone()
        assert name == "အဏ္ဏဝါသိပ္ပံ" and total is None and minimums == "{}"
        link = re.search(r"<a\b[^>]*>.*?</a>", previous, re.I | re.S).group()
        db.execute("""
            INSERT OR IGNORE INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, stream_status, region_rule,
             burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, '8, 73–74', 'STEAMS-1 or STEAMS-2', 'Nationwide', ?,
                    'published — score and wording only')
        """, (f"legacy:{admission_id}", admission_id, university, name, MARINE + "\n\n" + link))


if __name__ == "__main__":
    with sqlite3.connect(DATABASE.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        apply(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
