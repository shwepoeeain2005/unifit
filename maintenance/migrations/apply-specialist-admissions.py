"""Publish regular 2026 specialist admissions and direct-application information."""

import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parents[1]
PASS = "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်သူဖြစ်ရမည်။"
SCIENCE = [
    ["myan", "eng", "math", "phy", "chem", "bio"],
    ["myan", "eng", "math", "phy", "chem", "eco"],
]
SPORT = [*SCIENCE, ["myan", "eng", "math", "hist", "geo", "eco"]]
YAU = "https://www.edge.com.mm/article/6a8bf9aa514e2.html"
UVS = "https://uvs.edu.mm/2026/08/"
UFES = "https://ufes.edu.mm/၂၀၂၆-၂၀၂၇-ပညာသင်နှစ်အတွက်/"
LACQUER = "https://mcrd.gov.mm/index.php?page=YW5ub19kZXRhaWwmMTc4"
MMU = "https://www.mmu.edu.mm/News.aspx?NewsID=347"
ARTS = ("ဂီတ၊ သဘင်၊ ပန်းချီ၊ ပန်းပု၊ ရုပ်ရှင်နှင့် ပြဇာတ် ပညာရပ်များကို လျှောက်ထားနိုင်သည်။ "
        "လျှောက်လွှာပုံစံနှင့် ရွေးချယ်မှုအသေးစိတ်ကို သက်ဆိုင်ရာတက္ကသိုလ်၏ ၂၀၂၆ ကြေညာချက်တွင် စစ်ဆေးပါ။")
DIRECT = "သက်ဆိုင်ရာ တက္ကသိုလ် သို့မဟုတ် ကောလိပ်သို့ တိုက်ရိုက်လျှောက်ထားရသည်။"
UVS_FORMS = "၂၀၂၆ အောက်တိုဘာ ၁၅ ရက် နောက်ဆုံးထား၍ ရေဆင်းရှိ တက္ကသိုလ်သို့ လျှောက်ထားရသည်။ သီးခြား မွေးမြူရေးအတတ်ပညာ Grade A၊ GCE A Level နှင့် IB လမ်းကြောင်းများကို ကြေညာချက်တွင် စစ်ဆေးပါ။"
ROUTES = {
    789: ("77", 350, SCIENCE[:1], YAU, [
        "စိုက်ပျိုးရေးသိပ္ပံဘွဲ့ B.Agr.Sc. သင်တန်းကာလ ၄ နှစ် ဖြစ်သည်။ ပုံမှန်တက္ကသိုလ်ဝင်လမ်းကြောင်းအတွက် STEAMS-1 ဖြင့် အနည်းဆုံး ၃၅၀ မှတ် ရရှိရမည်။",
        "အမျိုးသား ၅၀% နှင့် အမျိုးသမီး ၅၀% အချိုးဖြင့် လက်ခံမည်။ အောက်တိုဘာ ၁၅ ရက် နောက်ဆုံးထား၍ ရေဆင်းသို့ လျှောက်ထားရသည်။",
        "စိုက်ပျိုးရေးအတတ်ပညာ Grade A၊ GCE A Level နှင့် IB အတွက် သီးခြားသတ်မှတ်ချက်များ ရှိသည်။",
    ]),
    790: ("77", 410, SCIENCE[:1], UVS, [
        "တိရစ္ဆာန်ဆေးပညာဘွဲ့ DVM သင်တန်းကာလ ၅ နှစ် ဖြစ်သည်။ STEAMS-1 ဖြင့် အနည်းဆုံး ၄၁၀ မှတ် ရရှိရမည်။", UVS_FORMS,
    ]),
    791: ("77", 350, SCIENCE[:1], UVS, [
        "မွေးမြူရေးပညာဘွဲ့ BASc သင်တန်းကာလ ၄ နှစ် ဖြစ်သည်။ STEAMS-1 ဖြင့် အနည်းဆုံး ၃၅၀ မှတ် ရရှိရမည်။", UVS_FORMS,
    ]),
    792: ("77", 350, SCIENCE[:1], UFES, [
        "သစ်တောပညာဘွဲ့ B.Sc. (Forestry) အတွက် STEAMS-1 ဖြင့် အနည်းဆုံး ၃၅၀ မှတ် ရရှိရမည်။",
        "သတ်မှတ်လျှောက်လွှာ၊ အမှတ်စာရင်းနှင့် လိုအပ်သော အထောက်အထားများကို ရေဆင်းရှိ တက္ကသိုလ်သို့ ပေးပို့ရမည်။ အသေးစိတ်ကို တက္ကသိုလ်ကြေညာချက်တွင် စစ်ဆေးပါ။",
    ]),
    798: ("78", None, [], LACQUER, [
        "မည်သည့်ဘာသာတွဲဖြင့်မဆို အောင်မြင်ထားသူသည် ယွန်းပညာနည်းပညာ ဒီပလိုမာ (Dip. L.T.) သင်တန်းကို လျှောက်ထားနိုင်သည်။ သင်တန်းကာလ ၂ နှစ် ဖြစ်သည်။",
        "၂၀၂၆ စက်တင်ဘာ ၁ ရက်မှ အောက်တိုဘာ ၃၀ ရက်အထိ ယွန်းပညာကောလိပ် (ပုဂံ) သို့ လျှောက်ထားရသည်။",
        "အောင်လက်မှတ်မိတ္တူ သို့မဟုတ် အောင်ကြောင်းထောက်ခံစာမူရင်း၊ အမှတ်စာရင်းမူရင်းနှင့် နိုင်ငံသားစိစစ်ရေးကတ်ပြားမိတ္တူ ပူးတွဲပါ။",
    ]),
    799: ("78, 95", None, [], "https://www.edge.com.mm/article/university-of-arts-and-culture.html", [
        DIRECT, ARTS, "ရန်ကုန်တွင် ယဉ်ကျေးမှုအမွေအနှစ် စီမံခန့်ခွဲမှုပညာ B.A. ကိုလည်း လျှောက်ထားနိုင်သည်။",
        "၂၀၂၆ နိုဝင်ဘာ ၁၁ ရက်အထိ လျှောက်လွှာလက်ခံခဲ့ပြီး နိုဝင်ဘာ ၁၃ ရက်တွင် လူတွေ့စစ်ဆေးခဲ့သည်။",
    ]),
    800: ("78, 95", None, [], None, [DIRECT, ARTS]),
    802: ("95–97", 450, SCIENCE, MMU, [
        "STEAMS-1 သို့မဟုတ် STEAMS-2 ဖြင့် အောင်မြင်ပြီး စုစုပေါင်း အနည်းဆုံး ၄၅၀ မှတ် ရရှိရမည်။",
        "Naval Architecture၊ Marine Engineering၊ Port and Harbour Engineering၊ River and Coastal Engineering၊ Marine Electrical Systems & Electronics Engineering၊ Marine Mechanical Engineering နှင့် Nautical Science တို့မှာ ၅ နှစ်သင်တန်းများ ဖြစ်သည်။",
        "စုစုပေါင်း ၃၆၀ ဦးအထိ လက်ခံပြီး အမျိုးသမီး ၂၀% အထိ လက်ခံမည်။ Marine Engineering၊ Marine Electrical Systems & Electronics Engineering နှင့် Nautical Science ကို အမျိုးသမီးများ လျှောက်ထားခွင့်မရှိပါ။",
        "လူတွေ့နှင့် ကျန်းမာရေး (က) အဆင့် စစ်ဆေးမှုရှိသည်။ အထက်ပါ ရေကြောင်းဘာသာရပ် သုံးခုတွင် အရောင်ခွဲခြားမှု စစ်ဆေးပြီး Nautical Science အတွက် မျက်မှန်တပ်သူ လျှောက်ထားခွင့်မရှိပါ။",
        "လျှောက်ထားသူနှင့် မိဘနှစ်ဦး၏ နိုင်ငံသားအထောက်အထား လိုအပ်သည်။ ၂၀၂၆ စက်တင်ဘာ ၇ ရက်မှ အောက်တိုဘာ ၉ ရက်အထိ သန်လျင်ရှိ တက္ကသိုလ်သို့ တိုက်ရိုက်လျှောက်ထားရသည်။",
    ]),
}
ACADEMY = "Naypyitaw State Academy"
ACADEMY_PATH = "Naypitaw State Academy.html"
ACADEMY_PROGRAMS = (
    "B.A. (Myanmar)", "B.A. (English)", "B.A. (Geography)", "B.A. (History)",
    "B.A. (Philosophy)", "B.A. (International Relations)", "B.A. (Library and Information Studies)",
    "B.A. (Diplomacy)", "B.Sc. (Chemistry)", "B.Sc. (Physics)", "B.Sc. (Mathematics)",
    "B.Sc. (Industrial Chemistry)", "B.Sc. (Nuclear Physics)", "LL.B.", "B.A. (Law)",
    "B.A. (Economics)", "B.Econ. (Economics)", "B.Econ. (Statistics)", "B.Com.", "BBA", "BBF",
    "BTHM", "B.Sc. (Sports)", "BSW",
)
ACADEMY_CONDITION = (
    "နေပြည်တော်တွင် တာဝန်ထမ်းဆောင်နေသော နိုင်ငံ့ဝန်ထမ်း မိသားစုဝင် သားသမီးများ သို့မဟုတ် "
    "ပျဉ်းမနား၊ လယ်ဝေး၊ တပ်ကုန်း၊ ဇမ္ဗူသီရိ၊ ပုဗ္ဗသီရိ၊ ဥတ္တရသီရိ၊ ဒက္ခိဏသီရိနှင့် ဇေယျာသီရိမြို့နယ်များမှ လျှောက်ထားသူများအတွက် ဖြစ်သည်။ "
    "နိုင်ငံသားအထောက်အထား ပူးတွဲပါ။ မိဘ သို့မဟုတ် အုပ်ထိန်းသူသည် နိုင်ငံ့ဝန်ထမ်းဖြစ်ပါက ရာထူး၊ ဌာနနှင့် ဝန်ကြီးဌာနကို ဖော်ပြရမည်။"
)


def record(db, key, legacy_id, campus, programme, pages, total, streams, rules, link, source=None,
           region="Direct application", physics_minimum=None):
    description = [PASS, *rules]
    if source:
        description.append(f'<a href="{source}" target="_blank" rel="noopener">၂၀၂၆ ဝင်ခွင့်အချက်အလက်</a>')
    description.append(link)
    status = "published — specialist admissions" if legacy_id is not None else "published — new specialist admission"
    db.execute("""
        INSERT INTO admission_2026_review
        (review_key, legacy_id, university, program, printed_pages, minimum_total, minimum_combined,
         combined_subjects, stream_examples_json,
         stream_status, region_rule, burmese_requirements_html, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_key) DO UPDATE SET minimum_total=excluded.minimum_total,
          minimum_combined=excluded.minimum_combined, combined_subjects=excluded.combined_subjects,
          stream_examples_json=excluded.stream_examples_json, stream_status=excluded.stream_status,
          region_rule=excluded.region_rule, printed_pages=excluded.printed_pages,
          burmese_requirements_html=excluded.burmese_requirements_html, review_status=excluded.review_status
    """, (key, legacy_id, campus, programme, pages, total, physics_minimum,
          "Physics + Math or Physics + Chemistry" if physics_minimum is not None else None, json.dumps(streams),
          "See listed streams" if streams else "No stream filter set", region, "\n\n".join(description), status))


def detail_link(path):
    if not (ROOT / path).is_file():
        raise ValueError(f"Missing detail page: {path}")
    return f'<a href="{quote(path)}" target="_blank" style="font-weight: bold; font-size: 15px;">more details</a>'


def publish(db):
    for legacy_id, (pages, total, streams, source, rules) in ROUTES.items():
        name, group, description = db.execute(
            "SELECT name, university_group, description_html FROM legacy_admission WHERE id = ?", (legacy_id,)
        ).fetchone()
        path = unquote(re.findall(r'href="([^"]+)"', description)[-1])
        record(db, f"legacy:{legacy_id}", legacy_id, group or name, name, pages, total, streams,
               [*rules, DIRECT], detail_link(path), source)
    for index, programme in enumerate(ACADEMY_PROGRAMS, 1):
        rules = [ACADEMY_CONDITION]
        physics_minimum = None
        if programme == "B.Sc. (Sports)":
            rules.append("STEAMS-1၊ STEAMS-2 သို့မဟုတ် STAMS-1 ဖြင့် အောင်မြင်ရမည်။ အသက်နှင့် ကျန်းမာရေးသတ်မှတ်ချက်၊ ကြံ့ခိုင်မှု စစ်ဆေးချက်ရှိပြီး လက်ခံဦးရေ ၃၀ ဖြစ်သည်။")
        elif programme == "B.Sc. (Industrial Chemistry)" or programme == "B.A. (International Relations)":
            rules.append("လူတွေ့စစ်ဆေးမှု ခံယူရမည်။")
        elif programme == "B.Sc. (Nuclear Physics)":
            physics_minimum = 120
            rules.append("ရူပဗေဒနှင့် သင်္ချာပေါင်း သို့မဟုတ် ရူပဗေဒနှင့် ဓာတုဗေဒပေါင်း အနည်းဆုံး ၁၂၀ မှတ် ရရှိရမည်။")
        rules.append("LL.B. သင်တန်းကာလ ၅ နှစ် ဖြစ်သည်။" if programme == "LL.B." else "သင်တန်းကာလ ၄ နှစ် ဖြစ်သည်။")
        record(db, f"academy:2026:{index:02}", None, ACADEMY, programme, "59–61, 74–77", None,
               SPORT if programme == "B.Sc. (Sports)" else [], rules, detail_link(ACADEMY_PATH),
               region="Naypyitaw family or township eligibility; verify in person", physics_minimum=physics_minimum)
    record(db, "mandalar:bthm:2026", None, "Mandalar University", "Tourism and Hospitality Management (BTHM)",
           "77, 79", None, [], [
               "မည်သည့်ဘာသာတွဲဖြင့်မဆို အောင်မြင်သူ လျှောက်ထားနိုင်သည်။ လေးနှစ်သင်တန်းဖြစ်ပြီး ၂၅၀ ဦး လက်ခံမည်။",
               "အင်္ဂလိပ်စာ ရမှတ်မြင့်သူကို ဦးစားပေးမည်။ သတ်မှတ်ထားသော လျှောက်လွှာနှင့်အတူ တက္ကသိုလ်သို့ တိုက်ရိုက်လျှောက်ထားရသည်။",
           ], detail_link("Mandalar university.html"), "https://www.edge.com.mm/article/-bthm.html")


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
