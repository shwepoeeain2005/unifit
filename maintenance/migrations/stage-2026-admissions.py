"""Record the reviewed 2026 admissions evidence without exporting it to the site."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "maintenance" / "unifit.sqlite"
GROUPS = {"University of Yangon": (16, 47, "61–63"),
          "University of Mandalay": (48, 74, "63–65")}
STEAMS_1 = {21, 30, 32, 34, 35, 38, 40, 53, 61, 63, 65, 66, 69, 71}
STEAMS_2 = {16, 18, 22, 34, 35, 39, 40, 48, 50, 54, 65, 66, 70, 71}
STAMS_1 = {16, 21, 23, 25, 29, 30, 35, 48, 53, 55, 57}
STAMS_2 = {18, 21, 22, 29, 30, 35, 50, 53, 54, 61, 66}
SPECIFIC = {18: {"STEAMS-2": 126}, 30: {"STAMS-1": 127}, 35: {"STAMS-1": 127}}
POLYTECHNICS = ("Myitkyina", "Bhamo", "Lashio", "Panglong", "Kengtung", "Maubin",
                "Dawei", "Myeik", "Taunggyi", "Mawlamyine", "Loikaw")


def stage(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS admission_2026_review (
        review_key TEXT PRIMARY KEY,
        legacy_id INTEGER REFERENCES legacy_admission(id),
        university TEXT NOT NULL,
        program TEXT NOT NULL,
        printed_pages TEXT NOT NULL,
        minimum_total INTEGER,
        minimum_english INTEGER,
        centers_2026_json TEXT,
        minimum_combined INTEGER,
        combined_subjects TEXT,
        stream_examples_json TEXT,
        stream_status TEXT NOT NULL,
        region_rule TEXT NOT NULL,
        burmese_requirements_html TEXT NOT NULL,
        review_status TEXT NOT NULL
    );
    """)
    rows = []
    for university, (first, last, pages) in GROUPS.items():
        legacy = db.execute(
            "SELECT id, name, description_html FROM legacy_admission WHERE university_group=? ORDER BY id",
            (university,),
        ).fetchall()
        if [row[0] for row in legacy] != list(range(first, last + 1)):
            raise ValueError(f"Unexpected baseline IDs for {university}")
        for legacy_id, program, description in legacy:
            examples = {
                label: {"printed_page": page, "scope": "general major example"}
                for label, ids, page in (
                    ("STEAMS-1", STEAMS_1, 125), ("STEAMS-2", STEAMS_2, 126),
                    ("STAMS-1", STAMS_1, 127), ("STAMS-2", STAMS_2, 128),
                )
                if legacy_id in ids
            }
            examples.update({label: {"printed_page": page, "scope": "university named in example"}
                             for label, page in SPECIFIC.get(legacy_id, {}).items()})
            status = "Major stream list needs confirmation"
            program_note = ""
            if legacy_id in {30, 61}:
                program = "ဥပဒေပညာ (LLB)"
                program_note = "\n၂၀၂၆ တက္ကသိုလ်အလိုက် ဘာသာရပ်ဇယားတွင် LLB ကို ဖော်ပြထားပါသည်။"
                status += "; confirm LLB versus B.A. (Law) listing"
            link = re.search(r"<a\b[^>]*>.*?</a>", description, re.I | re.S)
            mandalay = university == "University of Mandalay"
            exam = ("မည်သည့်ဘာသာတွဲဖြင့်မဆို " if mandalay else "")
            rules = (
                "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲကို " + exam + "အောင်မြင်ထားရမည်။\n"
                "ဝင်ခွင့်လျှောက်ထားချိန်တွင် နိုင်ငံသားဖြစ်မှုဆိုင်ရာ သတ်မှတ်ချက်နှင့် ကိုက်ညီရမည်။ "
                "မှတ်ပုံတင်မိတ္တူများ ပူးတွဲတင်ပြရမည်။\n"
                "မြန်မာနိုင်ငံအတွင်း မည်သည့်ဒေသမှမဆို လျှောက်ထားနိုင်သည်။\n"
                "၂၀၂၆ လမ်းညွှန်၏ တက္ကသိုလ်အလိုက် ကဏ္ဍတွင် ဤဘာသာရပ်အတွက် သတ်မှတ်အနိမ့်ဆုံးရမှတ်ကို ဖော်ပြမထားပါ။"
            )
            if not mandalay:
                rules += "\nတက္ကသိုလ်မှ သတ်မှတ်ထားသည့် စည်းကမ်းများကို လိုက်နာရမည်။"
            if link is None:
                raise ValueError(f"Missing detail link for admission {legacy_id}")
            rows.append((f"legacy:{legacy_id}", legacy_id, university, program, pages, None, None,
                         None, json.dumps(examples), status, "Nationwide",
                         rules + program_note + "\n\n" + link[0], "draft — stream review"))

    for campus in POLYTECHNICS:
        university = f"Polytechnic University ({campus})"
        for route, total, combination in (
            ("Engineering", None, 240), ("Computer Science and Technology", 320, None)
        ):
            threshold = (
                "အင်္ဂလိပ်စာ၊ သင်္ချာ၊ ဓာတုဗေဒနှင့် ရူပဗေဒ လေးဘာသာပေါင်း အနည်းဆုံး ၂၄၀ မှတ် ရရှိရမည်။"
                if combination else "တက္ကသိုလ်ဝင်စာမေးပွဲ စုစုပေါင်း အနည်းဆုံး ၃၂၀ မှတ် ရရှိရမည်။"
            )
            rules = (
                "၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲတွင် သင်္ချာ၊ ဓာတုဗေဒနှင့် ရူပဗေဒပါဝင်သည့် "
                "ဘာသာတွဲဖြင့် အောင်မြင်ထားရမည်။\n" + threshold + "\n"
                "သက်ဆိုင်ရာတိုင်းဒေသကြီး သို့မဟုတ် ပြည်နယ်မှ လျှောက်ထားသူများကို ဦးစားပေးမည်။ "
                "နေရာလွတ်ကျန်ပါက အခြားတိုင်းဒေသကြီး သို့မဟုတ် ပြည်နယ်မှ "
                "သတ်မှတ်ချက်နှင့် ကိုက်ညီသူများကို စဉ်းစားနိုင်သည်။"
            )
            rows.append((f"polytechnic:{campus}:{route}", None, university, route, "56–59",
                         total, combination, "English + Math + Chemistry + Physics" if combination else None,
                         None, "Pass with Math, Chemistry and Physics", "Local priority; outside region if places remain",
                         rules, "draft — campus mapping and full wording review"))
    db.executemany(
        """INSERT OR IGNORE INTO admission_2026_review
        (review_key, legacy_id, university, program, printed_pages, minimum_total, minimum_combined,
         combined_subjects, stream_examples_json, stream_status, region_rule, burmese_requirements_html,
         review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", rows
    )
    return len(rows)


if __name__ == "__main__":
    before = sha256((ROOT / "data/admissions.js").read_bytes()).hexdigest()
    with sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys = ON")
        expected = stage(db)
        assert db.execute("SELECT COUNT(*) FROM admission_2026_review").fetchone()[0] >= expected
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    assert sha256((ROOT / "data/admissions.js").read_bytes()).hexdigest() == before
    print(f"{expected} draft records saved. The browser export is unchanged.")
