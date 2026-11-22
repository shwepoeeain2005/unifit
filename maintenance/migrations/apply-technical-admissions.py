"""Apply reviewed regular 2026 engineering and technical-college admissions."""
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REGIONAL = {693, *range(695, 706), 708, 709, *range(711, 715)}
COLLEGES = {
    715: "Civil Engineering၊ Electrical Power Engineering နှင့် Mechanical Engineering",
    716: "Civil Engineering၊ Electronics၊ Electrical Power Engineering၊ Mechanical Engineering နှင့် Information Technology",
    717: "Civil Engineering၊ Electrical Power Engineering နှင့် Mechanical Engineering",
    718: "Civil Engineering၊ Electronics၊ Electrical Power Engineering၊ Mechanical Engineering နှင့် Information Technology",
}
SPECIFIC = {
    690: ("38–41", 300, "pcm_eng_combo", "B.E. / B.Arch."),
    691: ("41–44", 300, "pcm_eng_combo", "B.E. / B.Arch."),
    692: ("41–44", 260, "pcm_bio_combo", "B.S. (Biotechnology)"),
    694: ("44–46", 280, "pcm_eng_combo", "B.E."),
    801: ("46–48", 280, "pcm_eng_combo", "B.E."),
}
IDENTITY = "သတ်မှတ်ထားသည့် နိုင်ငံသားစိစစ်ရေးကတ်ပြား ကိုင်ဆောင်ရမည်။"
PRACTICAL = "လက်တွေ့လုပ်ငန်းနှင့် ကွင်းဆင်းလေ့လာမှုများ ဆောင်ရွက်နိုင်ရမည်။"
SCIENCE = "၂၀၂၆ တက္ကသိုလ်ဝင်စာမေးပွဲကို သင်္ချာ၊ ဓာတုဗေဒနှင့် ရူပဗေဒပါဝင်သော ဘာသာတွဲဖြင့် အောင်မြင်ရမည်။"
PRIORITY = ("သက်ဆိုင်ရာ တိုင်းဒေသကြီး သို့မဟုတ် ပြည်နယ်မှ လျှောက်ထားသူများကို ဦးစားပေးမည်။ "
            "သတ်မှတ်ဦးရေ မပြည့်ပါက အခြားဒေသမှ သတ်မှတ်ချက်ပြည့်မီသူများကို စဉ်းစားနိုင်သည်။")


def publish(db):
    for id_ in sorted(REGIONAL | COLLEGES.keys() | SPECIFIC.keys()):
        name, group, previous = db.execute("""
            SELECT name, university_group, description_html FROM legacy_admission WHERE id=?
        """, (id_,)).fetchone()
        link = re.search(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', previous, re.I)
        if id_ in {691, 692}:
            link_html = link[0].replace('href="TUM.html"', 'href="MTU.html"')
            destination = "MTU.html"
        else:
            link_html, destination = link[0], unquote(link[1])
        if not (ROOT / destination).is_file():
            raise ValueError(f"Missing detail link for {name}")
        region = "Existing center mapping retained"
        stream = "STEAMS-1 or STEAMS-2"
        rules = [SCIENCE, IDENTITY, PRACTICAL]
        if id_ in COLLEGES:
            pages, score, field = "49–50, 145", None, None
            rules.extend([
                "လမ်းညွှန်တွင် သတ်မှတ်အနိမ့်ဆုံး စုစုပေါင်းရမှတ်ကို ဖော်ပြမထားပါ။ ဝင်ခွင့်ကို ရမှတ်အစဉ်နှင့် သတ်မှတ်ဦးရေအရ ရွေးချယ်မည်။",
                "သင်တန်းကာလ ၄ နှစ် ဖြစ်ပြီး B.Tech ဘွဲ့ရရှိမည်။",
                f"လမ်းညွှန်ပါ ဤကောလိပ်၏ သင်တန်းများမှာ {COLLEGES[id_]} ဖြစ်သည်။",
            ])
        else:
            if id_ in REGIONAL:
                pages, score, field, degree = "48–49", 240, "pcm_eng_combo", "B.E. / B.Arch. / B.S. (Bio-Tech)"
                region = "Local priority; outside region if places remain"
                rules.append(PRIORITY)
            else:
                pages, score, field, degree = SPECIFIC[id_]
            if field == "pcm_bio_combo":
                stream = "STEAMS-1"
                rules[0] = "၂၀၂၆ တက္ကသိုလ်ဝင်စာမေးပွဲကို သင်္ချာ၊ ဓာတုဗေဒ၊ ရူပဗေဒနှင့် ဇီဝဗေဒပါဝင်သော ဘာသာတွဲဖြင့် အောင်မြင်ရမည်။"
                subjects = "သင်္ချာ၊ ဓာတုဗေဒ၊ ရူပဗေဒနှင့် ဇီဝဗေဒ"
            else:
                subjects = "အင်္ဂလိပ်စာ၊ သင်္ချာ၊ ဓာတုဗေဒနှင့် ရူပဗေဒ"
            digits = str(score).translate(str.maketrans("0123456789", "၀၁၂၃၄၅၆၇၈၉"))
            rules.insert(1, f"{subjects} လေးဘာသာပေါင်း အနည်းဆုံး {digits} မှတ် ရရှိရမည်။")
            if id_ not in REGIONAL:
                rules.append(f"သက်ဆိုင်ရာ သင်တန်းပြီးဆုံးပါက {degree} ဘွဲ့ ရရှိမည်။")
            if id_ == 801:
                rules.append("လူတွေ့စစ်ဆေးမှုနှင့် ကျန်းမာရေးစစ်ဆေးမှုကို အောင်မြင်ရမည်။ အရောင်ခွဲခြားနိုင်စွမ်းကိုလည်း စစ်ဆေးမည်။")
            rules.append("သတ်မှတ်ထားသော ဝင်ခွင့်လျှောက်လွှာပုံစံဖြင့် လျှောက်ထားရမည်။")
        db.execute("""
            INSERT INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, minimum_combined, combined_subjects,
             stream_status, region_rule, burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published — technical admissions')
            ON CONFLICT(review_key) DO UPDATE SET burmese_requirements_html=excluded.burmese_requirements_html
        """, (f"legacy:{id_}", id_, group or name, name, pages, score, field, stream, region,
              "\n\n".join(rules) + "\n\n" + link_html))


if __name__ == "__main__":
    database = ROOT / "maintenance" / "unifit.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        publish(db)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
