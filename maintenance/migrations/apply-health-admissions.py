"""Publish the guide's regular 2026 health sciences admissions requirements."""
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCIENCE = "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲကို STEAMS-1 (ဓာတုဗေဒ၊ ရူပဗေဒ၊ ဇီဝဗေဒ) ဘာသာတွဲဖြင့် အောင်မြင်ရမည်။"
IDENTITY = "သတ်မှတ်ထားသော နိုင်ငံသားစိစစ်ရေးကတ်ပြား ကိုင်ဆောင်ထားရမည်။ ကျန်းမာရေး ကောင်းမွန်ရမည်။"
APPLICATION = (
    "ဝင်ခွင့်လျှောက်လွှာစာအိတ်ပါ သတ်မှတ်ပုံစံဖြင့် လျှောက်ထားရမည်။ ပထမဦးစားပေး လျှောက်ထားသူများသည် "
    "သတ်မှတ်လက်ခံဌာနသို့ နောက်ဆုံးရက်မတိုင်မီ ပေးပို့ရမည်။"
)
PLACEMENT = "သတ်မှတ်ခွဲဝေပေးသည့် တက္ကသိုလ်တွင် သင်တန်းပြီးဆုံးသည်အထိ တက်ရောက်နိုင်ရမည်။"
SERVICE = (
    "သက်ဆိုင်ရာတာဝန်ထမ်းဆောင်မှုအစီအစဉ်အရ ဘွဲ့ရပြီးနောက် အနည်းဆုံး ၅ နှစ် တာဝန်ထမ်းဆောင်ရန် "
    "ကတိခံဝန်ချက်စာချုပ် ချုပ်ဆိုရမည်။ ဘွဲ့လွန်သင်တန်းပြီးပါကလည်း သတ်မှတ်ဝန်ထမ်းကာလ ၅ နှစ်ကို လိုက်နာရမည်။ "
    "စာချုပ်ပျက်ကွက်ပါက သတ်မှတ်လျော်ကြေးနှင့် စည်းမျဉ်းအရ အရေးယူမှုများ သက်ဆိုင်နိုင်သည်။"
)
NO_FIXED_TOTAL = "၂၀၂၆ လမ်းညွှန်၏ ဤကဏ္ဍတွင် သတ်မှတ်အနိမ့်ဆုံး စုစုပေါင်းရမှတ်ကို ဖော်ပြမထားပါ။"
NO_GENDER_SPLIT = "အမျိုးသားနှင့် အမျိုးသမီး ဝင်ခွင့်ရာခိုင်နှုန်း မခွဲခြားပါ။"
OFFICIAL = "https://www.um1ygn.edu.mm/post/article/2026-entrance"


def clinical(is_medicine):
    intake = "၁၄၀၀" if is_medicine else "၂၀၀"
    quota = ("အမျိုးသား ၅၀% နှင့် အမျိုးသမီး ၅၀% လက်ခံမည်။" if is_medicine
             else "အမျိုးသား ၆၀% နှင့် အမျိုးသမီး ၄၀% လက်ခံမည်။")
    return [
        quota, "အကျင့်စာရိတ္တ ကောင်းမွန်ရမည်။",
        "ခြောက်ဘာသာ စုစုပေါင်း အနည်းဆုံး ၄၅၀ မှတ် ရရှိရမည်။ အင်္ဂလိပ်စာ၊ ဓာတုဗေဒနှင့် ဇီဝဗေဒ "
        "သုံးဘာသာပေါင်းရမှတ်ဖြင့် ပဏာမရွေးချယ်မည်။",
        "ပဏာမရွေးချယ်ခံရသူများသည် ဝင်ခွင့် လူတွေ့နှုတ်မေးစာမေးပွဲ ဝင်ရောက်ဖြေဆိုရမည်။ "
        "သတ်မှတ်အချိန်တွင် မဖြေဆိုပါက ဝင်ခွင့်အတွက် စဉ်းစားမည်မဟုတ်ပါ။",
        f"နှုတ်မေးရမှတ်အလိုက် ဤတက္ကသိုလ်အုပ်စုအတွက် လမ်းညွှန်ပါ သတ်မှတ်ဦးရေ {intake} ဦးကို ရွေးချယ်မည်။ "
        "ဝင်ခွင့်ရသူများသည် သက်ဆိုင်ရာတက္ကသိုလ်တွင် စိတ်ပိုင်းဆိုင်ရာ ဆန်းစစ်မှု ခံယူရမည်။",
        PLACEMENT, SERVICE,
        "တာဝန်ထမ်းဆောင်မှုအစီအစဉ်အစား မိမိစရိတ်ဖြင့် တက်ရောက်နိုင်သူဦးရေသည် လမ်းညွှန်ပါ မူလလက်ခံဦးရေ၏ ၃၀% ထက် မပိုရပါ။",
        APPLICATION,
        "ပထမဦးစားပေး လျှောက်လွှာကို ကျန်းမာရေးလူ့စွမ်းအားအရင်းအမြစ်ဦးစီးဌာန (နေပြည်တော်) "
        "သို့မဟုတ် လမ်းညွှန်ပါ ဆေးနှင့် သွားဘက်ဆိုင်ရာဆေးတက္ကသိုလ် လက်ခံဌာနတစ်ခုသို့ တိုက်ရိုက်ပေးပို့ရမည်။ "
        "ရွေးချယ်မှုကတ်တွင် အခြားဦးစားပေးသင်တန်းများကိုလည်း အစီအစဉ်အတိုင်း ဖြည့်သွင်းရမည်။",
    ]


def allied(quota):
    return [quota, NO_FIXED_TOTAL, "အကျင့်စာရိတ္တ ကောင်းမွန်ရမည်။", PLACEMENT,
            SERVICE, APPLICATION,
            "မိမိစရိတ်ဖြင့် တက်ရောက်နိုင်သူဦးရေသည် လမ်းညွှန်ပါ မူလလက်ခံဦးရေ၏ ၂၀% ထက် မပိုရပါ။"]


def publish(db):
    reviewed = [
        (range(1, 6), "23–25", 450, clinical(True)),
        (range(6, 8), "25–27", 450, clinical(False)),
        (range(8, 10), "27–29", None, allied(NO_GENDER_SPLIT)),
        (range(10, 12), "29–30", None, allied(NO_GENDER_SPLIT) + [
            "လမ်းညွှန်တွင် Medical Laboratory Technology၊ Medical Imaging Technology၊ Physiotherapy၊ "
            "Health Information နှင့် Radiotherapy Technology တို့ကို ဖော်ပြထားသည်။"]),
        (range(12, 14), "30–32", None, allied("အမျိုးသား ၁၀% နှင့် အမျိုးသမီး ၉၀% လက်ခံမည်။")),
        (range(14, 15), "32–33", None, [
            "အမျိုးသား ၈၀% နှင့် အမျိုးသမီး ၂၀% လက်ခံမည်။", NO_FIXED_TOTAL, SERVICE, APPLICATION]),
        (range(15, 16), "33", None, [
            NO_GENDER_SPLIT, NO_FIXED_TOTAL, "သင်တန်းကို ပြီးဆုံးအောင် တက်ရောက်ရမည်။ "
            "ဘွဲ့ရပြီးနောက် နိုင်ငံ့ဝန်ထမ်းအဖြစ် ၃ နှစ် တာဝန်ထမ်းဆောင်ရန် ကတိခံဝန်ချက်စာချုပ် ချုပ်ဆိုရမည်။"]),
    ]
    for ids, pages, total, conditions in reviewed:
        for id_ in ids:
            name, old_total, subjects, description = db.execute("""
                SELECT name, required_total, required_subjects_json, description_html
                FROM legacy_admission WHERE id=?
            """, (id_,)).fetchone()
            if old_total != total or subjects != '["myan", "eng", "math", "phy", "chem", "bio"]':
                raise ValueError(f"Unexpected legacy rule for {name}")
            link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', description, re.I)
            if link is None or not (ROOT / unquote(link[1])).is_file():
                raise ValueError(f"Missing detail page for {name}")
            updated = "\n\n".join([SCIENCE, IDENTITY, *conditions])
            if id_ <= 14:
                updated += f'\n\n<a href="{OFFICIAL}" target="_blank" rel="noopener">၂၀၂၆ ဝင်ခွင့်ကြေညာချက်</a>'
            updated += "\n\n" + link[0]
            db.execute("""
                INSERT INTO admission_2026_review
                (review_key, legacy_id, university, program, printed_pages, minimum_total, stream_status,
                 region_rule, burmese_requirements_html, review_status)
                VALUES (?, ?, ?, ?, ?, ?, 'STEAMS-1', 'No exam-center filter', ?,
                        'published — score and wording only')
                ON CONFLICT(review_key) DO UPDATE SET burmese_requirements_html=excluded.burmese_requirements_html
            """, (f"legacy:{id_}", id_, name, name, pages, total, updated))


if __name__ == "__main__":
    database = ROOT / "maintenance" / "unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
