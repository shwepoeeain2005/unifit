"""Publish verified 2026 economics and management admissions."""

from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PASS = "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲကို မည်သည့်ဘာသာတွဲဖြင့်မဆို အောင်မြင်သူ လျှောက်ထားနိုင်သည်။"
NO_FIXED = "၂၀၂၆ ဝင်ခွင့်အတွက် သတ်မှတ်ထားသော အနည်းဆုံးရမှတ်ကို ဖော်ပြမထားပါ။"
RANK = "လက်ခံနိုင်သည့် ဦးရေအတွင်း တက္ကသိုလ်ဝင်စာမေးပွဲရမှတ် အစဉ်အတိုင်း ရွေးချယ်မည်။"
EXCEPTION = (
    "သတ်မှတ်ဒေသပြင်ပမှ လျှောက်ထားသူများကိုလည်း တက္ကသိုလ်က သတ်မှတ်သည့် "
    "အနည်းဆုံးရမှတ် ပြည့်မီပါက လက်ခံဦးရေ၏ ၁၀ ရာခိုင်နှုန်းအထိ လက်ခံနိုင်သည်။"
)
TOWNS = "ရေစကြို၊ မြိုင်၊ ပေါက်၊ ထီးလင်း၊ ဂန့်ဂေါ၊ ပခုက္ကူနှင့် ဆောမြို့နယ်များ"
REGIONAL = "Designated areas; up to 10% outside designated areas"
ECON_COMMON = "B.Econ (Economics)၊ B.Econ (Statistics)၊ B.Com၊ B.Act နှင့် BBA"
YANGON_DEGREES = ECON_COMMON + " အပြင် BPA၊ B.DevS၊ BPS နှင့် BAS ဘွဲ့များ သင်ကြားပေးသည်။"
IDENTITY = "နိုင်ငံသားစိစစ်ရေးကတ်ပြားအမှတ်ကို ဖြည့်စွက်ပြီး ကတ်ပြားမိတ္တူကို ပူးတွဲတင်ပြရမည်။"
YANGON_NOTICE = "https://yueco.edu.mm/?page_id=602"
COOP_COLLEGE_NOTICE = "https://mcrd.gov.mm/index.php?page=YW5ub19kZXRhaWwmMTc4"
COOP_DEGREES = (
    "လေးနှစ်သင် B.BSc ဘွဲ့များမှာ Regional Development၊ Accounting and Finance၊ "
    "Applied Statistics၊ Marketing Management နှင့် Social Enterprise Management တို့ဖြစ်သည်။"
)
COOP_DIPLOMAS = (
    "နှစ်နှစ်သင် ဒီပလိုမာများမှာ Social Enterprise Management၊ Regional Development၊ "
    "Business Accounting၊ Marketing Management နှင့် Applied Statistics တို့ဖြစ်သည်။ "
    "ဒီပလိုမာအောင်မြင်လျှင် သန်လျင် သို့မဟုတ် စစ်ကိုင်းရှိ သမဝါယမနှင့် စီမံခန့်ခွဲမှုပညာတက္ကသိုလ်တွင် "
    "သက်ဆိုင်ရာ အထူးပြုဘာသာရပ်၏ တတိယနှစ်သို့ ဆက်တက်နိုင်သည်။"
)
COOP_COLLEGE_APPLY = (
    "၂၀၂၆ လျှောက်လွှာကာလမှာ စက်တင်ဘာ ၁ ရက်မှ အောက်တိုဘာ ၃၀ ရက်အထိ ဖြစ်သည်။ "
    "အောင်လက်မှတ်မိတ္တူ သို့မဟုတ် အောင်ကြောင်းထောက်ခံစာမူရင်း၊ အမှတ်စာရင်းမူရင်းနှင့် "
    "နိုင်ငံသားစိစစ်ရေးကတ်ပြားမိတ္တူတို့ဖြင့် သက်ဆိုင်ရာကောလိပ်သို့ လျှောက်ထားရသည်။"
)

ROUTES = {
    686: ("65–66", "Nationwide", YANGON_NOTICE, [
        "စာစစ်ဌာနအားလုံးမှ အောင်မြင်သူများ လျှောက်ထားနိုင်သည်။",
        YANGON_DEGREES, IDENTITY,
    ]),
    687: ("66–67", "Kayin, Tanintharyi, Bago, Mon, Rakhine, Yangon, Ayeyarwady", YANGON_NOTICE, [
        "ရွာသာကြီးနယ်မြေအတွက် ကရင်၊ တနင်္သာရီ၊ ပဲခူး၊ မွန်၊ ရခိုင်၊ ရန်ကုန်နှင့် ဧရာဝတီဒေသများမှ လျှောက်ထားနိုင်သည်။",
        YANGON_DEGREES, IDENTITY,
    ]),
    688: ("67–68", REGIONAL, None, [
        f"သတ်မှတ်ဒေသများမှာ ကချင်၊ ချင်း၊ စစ်ကိုင်း၊ ရှမ်းပြည်နယ်မြောက်ပိုင်းနှင့် မကွေးတိုင်းရှိ {TOWNS} ဖြစ်သည်။",
        EXCEPTION, ECON_COMMON + " အပြင် B.Econ (Trade and Logistics) ဘွဲ့ကို မုံရွာတွင် သင်ကြားပေးသည်။",
    ]),
    689: ("67–68", REGIONAL, None, [
        f"သတ်မှတ်ဒေသများမှာ ကယား၊ မန္တလေး၊ ရှမ်းပြည်နယ်တောင်ပိုင်းနှင့် အရှေ့ပိုင်း၊ မကွေးတိုင်းရှိ {TOWNS}မှအပ ကျန်မြို့နယ်များ ဖြစ်သည်။",
        EXCEPTION, ECON_COMMON + " အပြင် BPA နှင့် BEM ဘွဲ့များကို မိတ္ထီလာတွင် သင်ကြားပေးသည်။",
    ]),
    788: ("78–79", "Direct application", None, [
        "ကောလိပ်၏ သီးခြားဝင်ခွင့်ကြေညာချက်အတိုင်း သတ်မှတ်လျှောက်လွှာဖြင့် ဗိုလ်တထောင်မြို့နယ်ရှိ ကောလိပ်သို့ တိုက်ရိုက်လျှောက်ထားရသည်။",
        "လေးနှစ်သင် BBM၊ BTHM၊ B.A. (English for Professional Purposes)၊ B.A. (Journalism) နှင့် BEF ဘွဲ့များကို လမ်းညွှန်တွင် ဖော်ပြထားသည်။",
        "ဘာသာရပ်အလိုက် ဝင်ခွင့်သတ်မှတ်ချက်များကို ကောလိပ်၏ သီးခြားကြေညာချက်တွင် စစ်ဆေးပါ။",
    ]),
    794: ("77–78", "Direct application", "https://mcrd.gov.mm/index.php?page=YW5ub19kZXRhaWwmMTc3", [
        RANK, COOP_DEGREES,
        "၂၀၂၆ လျှောက်လွှာကာလမှာ ဩဂုတ် ၂၈ ရက်မှ အောက်တိုဘာ ၂၃ ရက်အထိ ဖြစ်သည်။ "
        "အောင်လက်မှတ်မိတ္တူ၊ အမှတ်စာရင်းမူရင်း၊ ဓာတ်ပုံ လေးပုံနှင့် လျှောက်ထားသူနှင့် မိဘနှစ်ဦး၏ "
        "နိုင်ငံသားစိစစ်ရေးကတ်ပြားမိတ္တူတို့ကို ပူးတွဲတင်ပြရသည်။",
    ]),
    795: ("77–78", "Direct application", "https://ucms.edu.mm/News.aspx?NewsID=530", [
        RANK, COOP_DEGREES,
        "စစ်ကိုင်းတက္ကသိုလ်၏ ကြေညာချက်ပါ လျှောက်လွှာနှင့် စာရွက်စာတမ်းများကို တက္ကသိုလ်သို့ တင်ပြရသည်။",
    ]),
    796: ("77–78", "Direct application", COOP_COLLEGE_NOTICE, [RANK, COOP_DIPLOMAS, COOP_COLLEGE_APPLY]),
    797: ("77–78", "Direct application", COOP_COLLEGE_NOTICE, [RANK, COOP_DIPLOMAS, COOP_COLLEGE_APPLY]),
}


def publish(db):
    for legacy_id, (pages, region, source, requirements) in ROUTES.items():
        name, previous = db.execute(
            "SELECT name, description_html FROM legacy_admission WHERE id=?", (legacy_id,)
        ).fetchone()
        link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', previous, re.I)
        if link is None or not (ROOT / unquote(link[1])).is_file():
            raise ValueError(f"Missing detail link for {name}")
        introductory_rules = [PASS, NO_FIXED]
        stream_status = "Any 2026 matriculation stream"
        if legacy_id == 788:
            introductory_rules = ["၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်သူ လျှောက်ထားနိုင်သည်။"]
            stream_status = "See separate college notice for programme criteria"
        description = [*introductory_rules, *requirements]
        if source:
            description.append(f'<a href="{source}" target="_blank" rel="noopener">ဝင်ခွင့်ကြေညာချက်</a>')
        description.append(link[0])
        db.execute("""
            INSERT INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, stream_status,
             region_rule, burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published — economics and management')
            ON CONFLICT(review_key) DO UPDATE SET printed_pages=excluded.printed_pages,
                minimum_total=NULL, minimum_combined=NULL, combined_subjects=NULL, stream_examples_json=NULL,
                stream_status=excluded.stream_status, region_rule=excluded.region_rule,
                burmese_requirements_html=excluded.burmese_requirements_html, review_status=excluded.review_status
        """, (f"legacy:{legacy_id}", legacy_id, name, name, pages, stream_status, region, "\n\n".join(description)))


if __name__ == "__main__":
    database = ROOT / "maintenance" / "unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
