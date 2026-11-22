"""Apply 2026 guide and official MIIT requirements to the computing records."""
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCIENCE = "၂၀၂၆ တက္ကသိုလ်ဝင်စာမေးပွဲကို STEAMS-1 သို့မဟုတ် STEAMS-2 ဘာသာတွဲဖြင့် အောင်မြင်ရမည်။"
IDENTITY = "သတ်မှတ်ထားသော နိုင်ငံသားစိစစ်ရေးကတ်ပြား ကိုင်ဆောင်ရမည်။"
PRIORITY = (
    "သက်ဆိုင်ရာ တိုင်းဒေသကြီး သို့မဟုတ် ပြည်နယ်မှ လျှောက်ထားသူများကို ဦးစားပေးမည်။ "
    "သတ်မှတ်ဦးရေ မပြည့်ပါက အခြားဒေသမှ သတ်မှတ်ချက်ပြည့်မီသူများကို စဉ်းစားနိုင်သည်။"
)
PROGRAMS = "သင်တန်းကာလ ၄ နှစ်ဖြစ်ပြီး B.C.Sc. သို့မဟုတ် B.C.Tech. ဘွဲ့ ရရှိနိုင်သည်။"
REGIONAL = {723, 725, 727, *range(729, 738)}
MIIT_URL = "https://www.miit.edu.mm/en/bachelors-admission-process/"
SPECIAL = {
    719: ("53–54", 450, None, [
        "စုစုပေါင်း အနည်းဆုံး ၄၅၀ မှတ် ရရှိရမည်။ လမ်းညွှန်အရ ၂၀၀ ဦး လက်ခံမည်။",
        "Software Engineering၊ Knowledge Engineering၊ Business Information Systems၊ High Performance Computing၊ "
        "Embedded Systems၊ Computer Communication and Networks နှင့် Cyber Security တို့ကို ဖော်ပြထားသည်။",
    ]),
    720: ("51–53", 450, 140, [
        "စုစုပေါင်း အနည်းဆုံး ၄၅၀ မှတ် သို့မဟုတ် အင်္ဂလိပ်စာနှင့် သင်္ချာ နှစ်ဘာသာပေါင်း အနည်းဆုံး ၁၄၀ မှတ် ရရှိရမည်။",
        "စုစုပေါင်းရမှတ် အစဉ်အတိုင်း ဦးစားပေးရွေးချယ်မည်။ လမ်းညွှန်အရ အများဆုံး ၅၀၀ ဦး လက်ခံမည်။",
        "Software Engineering၊ Knowledge Engineering၊ Business Information Systems၊ Computer Security and Forensics၊ "
        "High Performance Computing၊ Embedded Systems နှင့် Computer Communication and Networks တို့ကို ဖော်ပြထားသည်။",
    ]),
    721: ("54–55", 430, 140, [
        "ပုသိမ်ကြီးမြို့နယ်ရှိ မန္တလေးကွန်ပျူတာတက္ကသိုလ်အတွက် စုစုပေါင်း အနည်းဆုံး ၄၃၀ မှတ် "
        "သို့မဟုတ် အင်္ဂလိပ်စာနှင့် သင်္ချာ နှစ်ဘာသာပေါင်း အနည်းဆုံး ၁၄၀ မှတ် ရရှိရမည်။",
        "လမ်းညွှန်အရ ၂၀၀ ဦး လက်ခံမည်။ Software Engineering၊ Knowledge Engineering၊ Business Information Systems၊ "
        "High Performance Computing၊ Computer Communication and Networks နှင့် Embedded Systems တို့ကို ဖော်ပြထားသည်။",
    ]),
}
CAMPUS_NAMES = {
    721: "University of Computer Studies, Mandalay (Patheingyi)",
    729: "University of Computer Studies (Mandalay, Sintkaing)",
}


def publish(db):
    db.execute("INSERT OR REPLACE INTO admission_total_or_math_english VALUES (?, ?, ?)", (720, "51", None))
    for id_ in sorted(REGIONAL | SPECIAL.keys() | {793}):
        name, previous = db.execute("SELECT name, description_html FROM legacy_admission WHERE id=?", (id_,)).fetchone()
        link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', previous, re.I)
        if link is None or not (ROOT / unquote(link[1])).is_file():
            raise ValueError(f"Missing detail link for {name}")
        region = "Nationwide"
        if id_ in REGIONAL:
            pages, total, combo = "55–56", 320, None
            region = "Local priority; outside region if places remain"
            rules = [SCIENCE, IDENTITY, "စုစုပေါင်း အနည်းဆုံး ၃၂၀ မှတ် ရရှိရမည်။", PRIORITY, PROGRAMS]
            if id_ == 729:
                rules.insert(0, "ဤသတ်မှတ်ချက်မှာ ကျောက်ဆည်ခရိုင်၊ စဉ့်ကိုင်မြို့နယ်ရှိ ကွန်ပျူတာတက္ကသိုလ် (မန္တလေး) အတွက် ဖြစ်သည်။")
        elif id_ == 793:
            pages, total, combo = "77; official MIIT admissions process", None, None
            rules = [
                SCIENCE,
                "သင်္ချာ၊ ရူပဗေဒ၊ ဓာတုဗေဒနှင့် အင်္ဂလိပ်စာ ပါဝင်ရမည်။ "
                "MIIT ၏ ၂၀၂၆ ဝင်ခွင့်အရည်အချင်းတွင် သတ်မှတ်အနိမ့်ဆုံး စုစုပေါင်းရမှတ်ကို ဖော်ပြမထားပါ။",
                "B.E. (Hons.) Computer Science & Engineering သို့မဟုတ် Electronics & Communications Engineering ကို လျှောက်ထားနိုင်သည်။ "
                "ဝင်ခွင့်စာမေးပွဲ ဖြေဆိုရမည်။ တက္ကသိုလ်ဝင်ရမှတ်နှင့် MIIT ဝင်ခွင့်စာမေးပွဲရမှတ်ကို အသုံးပြု၍ ရွေးချယ်မည်။",
                f'<a href="{MIIT_URL}" target="_blank" rel="noopener">MIIT ဝင်ခွင့်အချက်အလက်</a>',
            ]
        else:
            pages, total, combo, conditions = SPECIAL[id_]
            rules = [SCIENCE, IDENTITY, *conditions, PROGRAMS]
        db.execute("""
            INSERT INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, minimum_total, minimum_combined,
             combined_subjects, stream_status, region_rule, burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'STEAMS-1 or STEAMS-2', ?, ?, 'published — computing admissions')
            ON CONFLICT(review_key) DO UPDATE SET program=excluded.program,
                burmese_requirements_html=excluded.burmese_requirements_html
        """, (f"legacy:{id_}", id_, name, CAMPUS_NAMES.get(id_, name), pages, total, combo, "math_eng_combo" if combo else None,
              region, "\n\n".join([*rules, link[0]])))


if __name__ == "__main__":
    database = ROOT / "maintenance" / "unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
