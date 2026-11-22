"""Reconcile the regional arts and science search routes with the 2026 guide."""

import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
COMMON = (
    "မြန်မာစာ", "အင်္ဂလိပ်စာ", "ပထဝီဝင်", "သမိုင်း", "ဓာတုဗေဒ", "ရူပဗေဒ",
    "သင်္ချာ", "သတ္တဗေဒ", "ရုက္ခဗေဒ", "ရသစာပေအရေးအသား", "ဒဿနိကဗေဒ",
)
# Campus identifiers are the first legacy admission ID in each campus group.
# The Yangon, Mandalay and Naypyitaw State Academy routes are outside this batch.
OFFERINGS = {
    "အဏ္ဏဝါသိပ္ပံ": ("8", (75, 94, 114, 130)),
    "ကုန်ထုတ်ဓာတုဗေဒ": ("8", (149, 177, 206, 226)),
    "ကွန်ပျူတာသိပ္ပံ": ("8", (149, 177)),
    "အားကစားပညာ": ("8", (149, 177)),
    "နိုင်ငံတကာဆက်ဆံရေးပညာ": ("10", (149, 177, 206, 279)),
    "ဥပဒေပညာ LLB & ဥပဒေပညာ B.A(Law)": ("10–11", (
        75, 94, 130, 149, 177, 206, 241, 260, 279, 297, 315, 331, 349, 441, 458, 505, 650,
    )),
    "ဥပဒေပညာ B.A(Law)": ("11", (114, 226, 365, 381, 424, 473, 490, 520, 536, 551, 566, 580, 596)),
    "စီးပွားရေးပညာ": ("12", (
        75, 94, 114, 130, 149, 177, 241, 260, 297, 315, 331, 349, 365, 424,
        441, 458, 473, 490, 505, 520, 536, 551, 566, 596,
    )),
    "စိတ်ပညာ": ("13", (75, 94, 130, 149, 177, 206, 241, 260, 279, 297, 315, 331, 349)),
    "ရှေးဟောင်းသုတေသနပညာ": ("15", (149, 177)),
    "မနုဿဗေဒ": ("15", (149, 177, 206)),
    "အရှေ့တိုင်းပညာ": ("15–16", (
        75, 94, 114, 130, 149, 177, 206, 226, 241, 260, 279, 297, 315, 331, 349,
        365, 381, 396, 409, 424, 441, 458, 473, 490, 505, 520, 551, 580, 610,
    )),
    "စာကြည့်တိုက်နှင့်သုတပညာ": ("16", (177, 206)),
    "မြန်မာမှုပညာ": ("16", (149, 177)),
    "နျူကလိယရူပဗေဒ": ("17", (149, 177)),
    "အဏုဇီဝဗေဒ": ("17", (75, 94, 130, 149, 177, 241, 260, 279, 297, 331)),
    "ဇီဝဓာတုဗေဒ": ("17", (75, 94, 130, 149, 177, 241, 260, 279, 297, 331, 441)),
    "Business Information Technology": ("18", (149,)),
    "Records & Archives Management": ("19", (177,)),
    "ပတ်ဝန်းကျင်ဆိုင်ရာလေ့လာမှုပညာ": ("19", (
        94, 177, 206, 241, 279, 331, 365, 381, 409, 424, 441, 520, 536, 610, 624, 637,
    )),
    "Myanmar Tradition & Culture(MTC)": ("19", (424,)),
    "Environmental Science": ("20", (297, 349, 409, 490)),
    "Biotechnology": ("20", (149,)),
    "Agricultural Science": ("20", (315,)),
    "Agricultural Chemistry": ("20", (473,)),
    "Fishery Science": ("20", (473,)),
    "Renewable Energy": ("20", (260,)),
    "Tourism Studies": ("20", (580,)),
    "Petroleum Geology": ("20", (624,)),
}
IDENTITY_MAJORS = {
    "အဏ္ဏဝါသိပ္ပံ", "ကုန်ထုတ်ဓာတုဗေဒ", "ဘူမိဗေဒ", "နိုင်ငံတကာဆက်ဆံရေးပညာ",
    "နိုင်ငံရေးသိပ္ပံ", "နျူကလိယရူပဗေဒ", "ကွန်ပျူတာသိပ္ပံ", "Business Information Technology",
    "ဥပဒေပညာ LLB & ဥပဒေပညာ B.A(Law)", "ဥပဒေပညာ B.A(Law)",
}
IDENTITY = ("နိုင်ငံသားစိစစ်ရေးကတ်ပြား သို့မဟုတ် နိုင်ငံသားအထောက်အထား မိတ္တူပူးတွဲပါ။ "
            "နိုင်ငံသားဖြစ်ရန် လျှောက်ထားဆဲဆိုပါက လူဝင်မှုကြီးကြပ်ရေးဌာန၏ ထောက်ခံစာမူရင်းကို ပူးတွဲတင်ပြရမည်။")
ADDITIONAL = {
    "အဏ္ဏဝါသိပ္ပံ": ("STEAMS-1 သို့မဟုတ် STEAMS-2 ဖြင့် အောင်မြင်ရမည်။ လူတွေ့စစ်ဆေးမှု ခံယူရမည်။ "
                    "လျှောက်ထားလိုသည့် တက္ကသိုလ်များကို ဦးစားပေးအစီအစဉ်အတိုင်း ဖော်ပြရမည်။"),
    "ကုန်ထုတ်ဓာတုဗေဒ": "လူတွေ့စစ်ဆေးမှု ခံယူရမည်။",
    "နိုင်ငံတကာဆက်ဆံရေးပညာ": "လူတွေ့စစ်ဆေးမှု ခံယူရမည်။",
    "ဘူမိဗေဒ": ("တက္ကသိုလ်အလိုက် လက်ခံဦးရေ၏ ၁၀ ရာခိုင်နှုန်းအထိ အမျိုးသမီးများကို လက်ခံမည်။ မိုင် ၂၀ လမ်းလျှောက်နိုင်ရမည်။ "
                 "ကျန်းမာရေး (က) အဆင့်ရရှိပြီး အမြင်နှင့် အရောင်ခွဲခြားမှု စစ်ဆေးရမည်။"),
    "ဥပဒေပညာ LLB & ဥပဒေပညာ B.A(Law)": "B.A. (Law) သင်တန်းကာလ ၄ နှစ်ဖြစ်ပြီး LL.B. သင်တန်းကာလ ၅ နှစ် ဖြစ်သည်။",
    "ဥပဒေပညာ B.A(Law)": ("B.A. (Law) သင်တန်းကာလ ၄ နှစ် ဖြစ်သည်။ B.A. (Law) ရရှိပြီး သတ်မှတ်ချက်ပြည့်မီပါက "
                              "LL.B. ဖွင့်လှစ်သည့် တက္ကသိုလ်တွင် ၂ နှစ် ဆက်လက်တက်ရောက်နိုင်သည်။"),
    "အားကစားပညာ": (
        "STEAMS-1၊ STEAMS-2 သို့မဟုတ် STAMS-1 ဖြင့် အောင်မြင်ရမည်။ B.Sc. (Sports) သင်တန်းကာလ ၄ နှစ် ဖြစ်သည်။ "
        "ဒဂုံနှင့် ရတနာပုံ တက္ကသိုလ်တစ်ခုစီတွင် ၅၀ ဦး လက်ခံမည်။ အမျိုးသား ၆၀% နှင့် အမျိုးသမီး ၄၀% အချိုးအစားဖြင့် ရွေးချယ်မည်။ "
        "နိုင်ငံသားဖြစ်ရမည်။ ၂၀၂၆ ဒီဇင်ဘာ ၃၁ ရက်တွင် အသက် ၂၁ နှစ်ထက် မကြီးရဘဲ အိမ်ထောင်မပြုဖူးသူ ဖြစ်ရမည်။ "
        "ကျန်းမာရေးထောက်ခံချက်နှင့် ကြံ့ခိုင်မှုစစ်ဆေးချက် လိုအပ်သည်။ အားကစားအောင်မြင်မှုရှိသူများကို ဦးစားပေးမည်။ "
        "နိုင်ငံတော်ထောက်ပံ့မှုဖြင့် တက်ရောက်သူသည် လိုအပ်ပါက သက်ဆိုင်ရာ အားကစားတာဝန်ကို ၂ နှစ် ထမ်းဆောင်ရမည်။"
    ),
}
NUCLEAR = {
    149: "ကရင်၊ တနင်္သာရီ၊ ပဲခူး၊ မွန်၊ ရခိုင်၊ ရန်ကုန်နှင့် ဧရာဝတီ",
    177: "ကချင်၊ ကယား၊ ချင်း၊ စစ်ကိုင်း၊ မကွေး၊ မန္တလေးနှင့် ရှမ်း",
}


def publish(db):
    db.row_factory = sqlite3.Row
    campuses = {}
    for row in db.execute("SELECT * FROM legacy_admission WHERE id BETWEEN 75 AND 685 ORDER BY id"):
        campuses.setdefault(row["university_group"], {})[row["name"]] = row
    counts = Counter()
    for university, previous in campuses.items():
        anchor = next(iter(previous.values()))
        campus = anchor["id"]
        expected = dict.fromkeys(COMMON, "21")
        expected["ဒဿနိကဗေဒ"] = "13–15"
        if campus != 663:
            expected["ဘူမိဗေဒ"] = "8–10"
        expected.update({name: pages for name, (pages, ids) in OFFERINGS.items() if campus in ids})
        for name, pages in expected.items():
            old = previous.get(name)
            reference = old if old is not None else anchor
            link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', reference["description_html"], re.I | re.S)
            if link is None or not (ROOT / unquote(link[1])).is_file():
                raise ValueError(f"Missing detail page for {university}, {name}")
            rules = ["၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်ရမည်။"]
            combined = None
            if name in IDENTITY_MAJORS:
                rules.append(IDENTITY)
                pages += ", 73–74"
            if name in ADDITIONAL:
                rules.append(ADDITIONAL[name])
                if name not in {"ဥပဒေပညာ LLB & ဥပဒေပညာ B.A(Law)", "ဥပဒေပညာ B.A(Law)"}:
                    pages += ", 74–77"
            if name == "နျူကလိယရူပဗေဒ":
                pages += ", 75"
                combined = 120
                rules.extend([
                    f"သတ်မှတ်ဒေသများမှာ {NUCLEAR[campus]} ဖြစ်သည်။",
                    "ရူပဗေဒနှင့် သင်္ချာပေါင်း ၁၂၀ မှတ် သို့မဟုတ် ရူပဗေဒနှင့် ဓာတုဗေဒပေါင်း ၁၂၀ မှတ် အနည်းဆုံး ရရှိရမည်။",
                ])
            else:
                rules.append("ဤဘာသာရပ်အတွက် ၂၀၂၆ လမ်းညွှန်တွင် သီးခြားအနည်းဆုံးရမှတ် မဖော်ပြထားပါ။")
            if old is None:
                rules.append("ဘာသာတွဲနှင့် ဒေသအလိုက် အသေးစိတ်သတ်မှတ်ချက်များကို သက်ဆိုင်ရာတက္ကသိုလ်တွင် စစ်ဆေးပါ။")
            status = "published — general arts and science" if old is not None else "published — new general arts and science"
            count_key = "updated" if old is not None else "added"
            counts[count_key] += 1
            if old is None:
                print("Added", university, name)
            key = f"legacy:{old['id']}" if old is not None else f"general-arts:{campus}:{name}"
            db.execute("""
                INSERT INTO admission_2026_review
                    (review_key, legacy_id, university, program, printed_pages, minimum_combined,
                     combined_subjects, stream_status, region_rule, burmese_requirements_html, review_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_key) DO UPDATE SET printed_pages=excluded.printed_pages,
                    minimum_total=NULL, minimum_combined=excluded.minimum_combined,
                    combined_subjects=excluded.combined_subjects, stream_status=excluded.stream_status,
                    region_rule=excluded.region_rule, burmese_requirements_html=excluded.burmese_requirements_html,
                    review_status=excluded.review_status
            """, (
                key, old["id"] if old is not None else None, university, name, pages, combined,
                "Physics + Math or Physics + Chemistry" if combined is not None else None,
                "Guide stream verified" if name in {"အဏ္ဏဝါသိပ္ပံ", "အားကစားပညာ"} else "Campus stream follow-up",
                "Designated regions" if combined is not None else "Campus catchment follow-up",
                "\n\n".join([*rules, link[0]]), status,
            ))
        for name in previous.keys() - expected.keys():
            old = previous[name]
            counts["withheld"] += 1
            print("Withheld", university, name)
            db.execute("""
                INSERT INTO admission_2026_review
                    (review_key, legacy_id, university, program, printed_pages, stream_status,
                     region_rule, burmese_requirements_html, review_status)
                VALUES (?, ?, ?, ?, '8–21', 'Unverified', 'Unverified', '',
                        'withheld — unverified 2026 intake')
                ON CONFLICT(review_key) DO UPDATE SET review_status=excluded.review_status
            """, (f"legacy:{old['id']}", old["id"], university, name))
    print(dict(counts))


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
