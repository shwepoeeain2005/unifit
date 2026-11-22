"""Publish regular undergraduate education routes from the 2026 guide."""

import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PASSED = "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်ရမည်။"
NO_CUTOFF = "၂၀၂၆ လမ်းညွှန်တွင် သတ်မှတ်ထားသော အနည်းဆုံးဝင်ခွင့်ရမှတ်ကို ဖော်ပြမထားပါ။"
SERVICE = (
    "သင်တန်းကို ပြီးဆုံးအောင် တက်ရောက်ရပြီး ဘွဲ့ရပြီးနောက် နိုင်ငံ့ဝန်ထမ်းအဖြစ် "
    "အနည်းဆုံး ၅ နှစ် တာဝန်ထမ်းဆောင်ရန် ခံဝန်ကတိ လက်မှတ်ရေးထိုးရမည်။"
)
BOND = (
    "ခံဝန်ချက် ပျက်ကွက်ပါက ကျပ် ၂,၀၀၀,၀၀၀ နှင့် သင်တန်းကာလအတွင်း ရရှိခဲ့သည့် "
    "နိုင်ငံတော်ထောက်ပံ့ကြေးနှင့် စားသောက်စရိတ်များကို ပြန်လည်ပေးလျော်ရမည်။ "
    "ပေးလျော်ရန် ထပ်မံပျက်ကွက်ပါက သက်ဆိုင်ရာ စည်းမျဉ်းများအရ အရေးယူနိုင်သည်။"
)
UNIVERSITY_REGIONS = (
    "ရန်ကုန်ပညာရေးတက္ကသိုလ်အတွက် ကရင်၊ တနင်္သာရီ၊ ပဲခူး၊ မွန်၊ ရခိုင်၊ ရန်ကုန်နှင့် ဧရာဝတီဒေသများ သတ်မှတ်ထားသည်။",
    "စစ်ကိုင်းပညာရေးတက္ကသိုလ်အတွက် ကချင်၊ ကယား၊ ချင်း၊ စစ်ကိုင်း၊ မကွေး၊ နေပြည်တော်၊ မန္တလေးနှင့် ရှမ်းဒေသများ သတ်မှတ်ထားသည်။",
)
UNIVERSITY_STREAMS = (
    ("STEAMS-1", [["myan", "eng", "math", "chem", "phy", "bio"]],
     "သိပ္ပံဘာသာရပ်အတွက် STEAMS-1 (ဓာတုဗေဒ၊ ရူပဗေဒ၊ ဇီဝဗေဒ) ဖြင့် အောင်မြင်ရမည်။"),
    ("STEAMS-2", [["myan", "eng", "math", "chem", "phy", "eco"]],
     "ဝိပ္ပံဘာသာရပ်အတွက် STEAMS-2 (ဓာတုဗေဒ၊ ရူပဗေဒ၊ ဘောဂဗေဒ) ဖြင့် အောင်မြင်ရမည်။"),
    ("STAMS-1 or STAMS-2", [
        ["myan", "eng", "math", "geo", "hist", "eco"],
        ["myan", "eng", "math", "customMyan", "eco", "social"],
    ], "ဝိဇ္ဇာဘာသာရပ်အတွက် STAMS-1 သို့မဟုတ် STAMS-2 ဖြင့် အောင်မြင်ရမည်။"),
)
COLLEGE_RULES = [
    "ကောလိပ် ၂၅ ကျောင်းတွင် ကျောင်းအလိုက် ဝင်ဆံ့အင်အားအရ လက်ခံမည်။",
    "သင်တန်းကာလ ၄ နှစ်ဖြစ်ပြီး မူလတန်း သို့မဟုတ် အလယ်တန်းအထူးပြု ပညာရပ်များ သင်ယူ၍ B.A. (Education) သို့မဟုတ် B.Sc. (Education) ဘွဲ့ ရရှိနိုင်သည်။",
    "နိုင်ငံသားစိစစ်ရေးကတ်ပြား (နိုင်၊ ပြု၊ ဧည့်) ကိုင်ဆောင်ထားရမည်။",
    "သက်ဆိုင်ရာကောလိပ်တွင် လူတွေ့နှုတ်ဖြေ စစ်ဆေးမှုကို အောင်မြင်သူသာ တက်ရောက်ခွင့်ရမည်။ တက်ရောက်ခွင့်ရသူသည် အိမ်ထောင်မပြုဖူးသူ ဖြစ်ရမည်။",
    SERVICE,
    "ဆရာ၊ ဆရာမအဖြစ် ခန့်ထားပါက ဒေသမရွေး တာဝန်ထမ်းဆောင်နိုင်ရမည်။ ကောလိပ်စည်းကမ်းများကို လိုက်နာရမည်။",
    BOND,
    "ဝင်ခွင့်ရရှိသည့် ကောလိပ်တွင်သာ သင်တန်းပြီးဆုံးအောင် တက်ရောက်ရမည်။ အခြားပညာရေးဒီဂရီကောလိပ်သို့ ပြောင်းရွှေ့ခွင့်မရှိပါ။",
    "ကျောင်းအလိုက် လျှောက်ထားနိုင်သည့် ဒေသနှင့် အသေးစိတ်ရွေးချယ်မှု သတ်မှတ်ချက်များကို သက်ဆိုင်ရာကောလိပ်တွင် စစ်ဆေးပါ။",
]


def publish(db):
    rows = db.execute("""
        SELECT id, name, description_html
        FROM legacy_admission
        WHERE id BETWEEN 755 AND 760 OR id BETWEEN 763 AND 787
        ORDER BY id
    """).fetchall()
    if len(rows) != 31:
        raise ValueError("Expected six university streams and 25 college routes")
    for legacy_id, name, previous in rows:
        link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', previous, re.I)
        if link is None or not (ROOT / unquote(link[1])).is_file():
            raise ValueError(f"Missing detail link for {name}")
        if legacy_id <= 760:
            pages = "6, 68–70"
            stream, subjects, stream_rule = UNIVERSITY_STREAMS[(legacy_id - 755) % 3]
            region = "Designated areas; up to 10% outside designated areas"
            rules = [
                "ပညာရေးဘွဲ့ B.Ed. သင်တန်းကာလ ၅ နှစ် ဖြစ်သည်။ အမျိုးသား ၅၀ ရာခိုင်နှုန်းနှင့် အမျိုးသမီး ၅၀ ရာခိုင်နှုန်း လက်ခံမည်။",
                stream_rule, UNIVERSITY_REGIONS[int(legacy_id >= 758)],
                "သတ်မှတ်ဒေသပြင်ပမှ လျှောက်ထားသူများကို သတ်မှတ်လက်ခံဦးရေ၏ ၁၀ ရာခိုင်နှုန်းအထိ လက်ခံနိုင်သည်။ "
                "လျှောက်ထားမည့် တက္ကသိုလ်ကို ဦးစားပေးအစီအစဉ်အတိုင်း ဖော်ပြရမည်။",
                "နိုင်ငံသားစိစစ်ရေးကတ်ပြားအမှတ်ဖြည့်၍ မိတ္တူပူးတွဲပါ။ နိုင်ငံသားဖြစ်ရန် လျှောက်ထားဆဲဆိုပါက သက်ဆိုင်ရာ လူဝင်မှုကြီးကြပ်ရေးဌာန၏ ထောက်ခံစာ တင်ပြရမည်။",
                SERVICE + " ဒေသမရွေး တာဝန်ထမ်းဆောင်နိုင်ရမည်။", BOND,
            ]
        else:
            pages, stream = "6–7, 72–73", "No stream restriction specified in guide"
            region, subjects = "Campus catchments not specified in guide", None
            rules = COLLEGE_RULES
        description = "\n\n".join([PASSED, NO_CUTOFF, *rules, link[0]])
        db.execute("""
            INSERT INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, stream_examples_json,
             stream_status, region_rule, burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'published — education admissions')
            ON CONFLICT(review_key) DO UPDATE SET printed_pages=excluded.printed_pages,
                minimum_total=NULL, minimum_combined=NULL, combined_subjects=NULL,
                stream_examples_json=excluded.stream_examples_json, stream_status=excluded.stream_status,
                region_rule=excluded.region_rule, burmese_requirements_html=excluded.burmese_requirements_html,
                review_status=excluded.review_status
        """, (f"legacy:{legacy_id}", legacy_id, name.split(" (", 1)[0], name,
              pages, json.dumps(subjects) if subjects else None, stream, region, description))


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
