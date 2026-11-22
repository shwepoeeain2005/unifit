"""Apply the confirmed regional tables and resolve outstanding 2026 route identities."""

import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# Regional arts/science entries use the first legacy ID as the campus key.
REGIONS = {
    "kcn": ("ကချင်ပြည်နယ်", 103, (297, 566, 637), (763,)),
    "kyh": ("ကယားပြည်နယ်", 103, (458,), (764,)),
    "kyn": ("ကရင်ပြည်နယ်", 103, (441,), (765,)),
    "chn": ("ချင်းပြည်နယ်", 103, (130, 424, 520, 650), (766,)),
    "sgg": ("စစ်ကိုင်းတိုင်းဒေသကြီး", 104, (279, 520, 596, 610, 663), (767, 768, 769)),
    "tni": ("တနင်္သာရီတိုင်းဒေသကြီး", 104, (114, 349), (770,)),
    "bgo": ("ပဲခူးတိုင်းဒေသကြီး", 105, (315, 331, 580), (771, 772)),
    "mgy": ("မကွေးတိုင်းဒေသကြီး", 105, (260, 424, 624), (773, 774)),
    "mdy": ("မန္တလေးတိုင်းဒေသကြီး", 105, (177, 365, 381, 396, 409), (775, 776)),
    "mon": ("မွန်ပြည်နယ်", 106, (75,), (777,)),
    "rke": ("ရခိုင်ပြည်နယ်", 106, (130, 674), (778,)),
    "ygn": ("ရန်ကုန်တိုင်းဒေသကြီး", 106, (149, 206, 226), (779, 780, 781)),
    "shan": ("ရှမ်းပြည်နယ်", 107, (241, 505, 536, 551), (782, 783, 784)),
    "ayy": ("ဧရာဝတီတိုင်းဒေသကြီး", 107, (94, 473, 490), (785, 786, 787)),
}
MEDICINE_NOTICE = "https://www.hrh.gov.mm/post/announcements/2026-steams1-entrance-list"
REGION_PREFIX = "၂၀၂၆ လမ်းညွှန်အရ သတ်မှတ်ထားသော ဒေသ"
STREAM_NOTE = "ဤဘာသာရပ်အတွက် ဘာသာတွဲအလိုက် အသေးစိတ် သတ်မှတ်ချက်များကို သက်ဆိုင်ရာတက္ကသိုလ်တွင် အတည်ပြုပါ။"
UNVERIFIED_STREAM = "2026 stream unverified; show with confirmation note"
SCIENCE = [["myan", "eng", "math", "phy", "chem", subject] for subject in ("bio", "eco")]
SPORT = [*SCIENCE, ["myan", "eng", "math", "geo", "hist", "eco"]]
SUPPORTED_STREAMS = [*SPORT, ["myan", "eng", "math", "customMyan", "eco", "social"]]


def set_region(db, key, pages, description, region_codes, text):
    parts = [part for part in description.split("\n\n")
             if not part.startswith(REGION_PREFIX) and not part.startswith("ကျောင်းအလိုက် လျှောက်ထားနိုင်သည့် ဒေသ")]
    parts.insert(len(parts) - 1, text)
    base_pages = re.sub(r", 10[3-7](?:–10[3-7])?$", "", pages)
    db.execute("""
        UPDATE admission_2026_review SET centers_2026_json=?, region_rule=?,
          printed_pages=?, burmese_requirements_html=? WHERE review_key=?
    """, (json.dumps(region_codes), "2026 guide designated regions",
          f"{base_pages}, {pages_for_regions(region_codes)}", "\n\n".join(parts), key))


def pages_for_regions(codes):
    pages = sorted({REGIONS["shan" if code in {"north", "south", "east"} else code][1] for code in codes})
    return str(pages[0]) if len(pages) == 1 else f"{pages[0]}–{pages[-1]}"


def regional_routes(db):
    campuses = {}
    colleges = {}
    for code, (_, _, campus_ids, college_ids) in REGIONS.items():
        for campus_id in campus_ids:
            name, = db.execute("SELECT university_group FROM legacy_admission WHERE id=?", (campus_id,)).fetchone()
            campuses.setdefault(name, []).append(code)
        colleges.update((id_, code) for id_ in college_ids)
    assert len(campuses) == 37 and len(colleges) == 25
    rows = db.execute("""
        SELECT review_key, legacy_id, university, program, printed_pages, burmese_requirements_html
        FROM admission_2026_review
        WHERE review_status IN ('published — general arts and science', 'published — new general arts and science',
                               'published — education admissions')
    """).fetchall()
    count = 0
    for key, legacy_id, campus, programme, pages, description in rows:
        if legacy_id in colleges:
            codes = [colleges[legacy_id]]
        elif campus in campuses:
            if programme in {"အဏ္ဏဝါသိပ္ပံ", "အားကစားပညာ"}:
                subjects = SCIENCE if programme == "အဏ္ဏဝါသိပ္ပံ" else SPORT
                db.execute("UPDATE admission_2026_review SET stream_examples_json=? WHERE review_key=?",
                           (json.dumps(subjects), key))
                continue
            if programme == "နျူကလိယရူပဗေဒ":
                # The published subject-pair score already excludes streams without Physics.
                parts = [part for part in description.split("\n\n") if part != STREAM_NOTE]
                db.execute("""
                    UPDATE admission_2026_review SET stream_examples_json='[]', stream_status=?,
                      burmese_requirements_html=? WHERE review_key=?
                """, ("Published subject-pair rule", "\n\n".join(parts), key))
                continue
            codes = campuses[campus]
        else:
            continue
        text = REGION_PREFIX + "မှာ " + "၊ ".join(REGIONS[code][0] for code in codes) + " ဖြစ်သည်။"
        if "chn" in codes and campus in {"Sittwe University", "Pakokku University", "Kalay University"}:
            text += " ချင်းပြည်နယ်မှ လျှောက်ထားသူများအတွက် လမ်းညွှန်ပါ သတ်မှတ်မြို့နယ်များနှင့် ကိုက်ညီရမည်။"
        center_codes = ["north", "south", "east"] if codes == ["shan"] else codes
        set_region(db, key, pages, description, center_codes, text)
        count += 1
    assert count == 634


def resolve_law(db):
    for id_, file in ((30, "YU.html"), (61, "MU.html")):
        pages, description = db.execute(
            "SELECT printed_pages, burmese_requirements_html FROM admission_2026_review WHERE legacy_id=?",
            (id_,),
        ).fetchone()
        rule = "၂၀၂၆ လမ်းညွှန်တွင် ဥပဒေဘွဲ့ LL.B. သင်တန်းကို ဖော်ပြထားပြီး သင်တန်းကာလ ၅ နှစ် ဖြစ်သည်။"
        parts = [part for part in description.split("\n\n") if part != rule]
        parts.insert(len(parts) - 1, rule)
        # The earlier review already used the LL.B. name in SQLite. Export it as well.
        db.execute("""
            UPDATE admission_2026_review SET printed_pages=?, stream_status=?, burmese_requirements_html=?
            WHERE legacy_id=?
        """, (pages if pages.startswith("10–11, ") else "10–11, " + pages,
              "Any 2026 matriculation stream" if id_ == 61 else "No exclusive stream list confirmed",
              "\n\n".join(parts), id_))
        db.execute("UPDATE detail_section SET title='Law (LL.B.)' WHERE page_path=? AND title='Law'", (file,))


def academy_medicine(db):
    description, = db.execute(
        "SELECT burmese_requirements_html FROM admission_2026_review WHERE legacy_id=1"
    ).fetchone()
    rules = [part for part in description.split("\n\n") if not part.startswith("<a")]
    rules.append("Naypyitaw State Academy ဆေးပညာဌာနကို ၂၀၂၆ လမ်းညွှန်၏ ဆေးတက္ကသိုလ်စာရင်းတွင် ထည့်သွင်းထားပြီး ကျန်းမာရေးဝန်ကြီးဌာန၏ ပထမနှစ် ဝင်ခွင့်စာရင်းတွင် အတည်ပြုထားသည်။")
    rules.append(f'<a href="{MEDICINE_NOTICE}" target="_blank" rel="noopener">၂၀၂၆ ဆေးပညာဝင်ခွင့်ကြေညာချက်</a>')
    rules.append('<a href="Naypitaw%20State%20Academy.html" target="_blank" style="font-weight: bold; font-size: 15px;">more details</a>')
    db.execute("""
        INSERT INTO admission_2026_review
        (review_key, university, program, printed_pages, minimum_total, stream_examples_json,
         stream_status, region_rule, burmese_requirements_html, review_status)
        VALUES ('academy:medicine:2026', 'Naypyitaw State Academy', 'Medicine (M.B.B.S.)',
                '23–25, 61, 108; 2026 Ministry of Health final notice', 450, ?,
                'STEAMS-1', 'Common medical placement route', ?, 'published — new specialist admission')
        ON CONFLICT(review_key) DO UPDATE SET burmese_requirements_html=excluded.burmese_requirements_html
    """, (json.dumps(SCIENCE[:1]), "\n\n".join(rules)))
    db.execute("""
        INSERT OR IGNORE INTO admission_2026_review
        (review_key, legacy_id, university, program, printed_pages, stream_status,
         region_rule, burmese_requirements_html, review_status)
        VALUES ('legacy:754',754,'Naypyitaw State Academy','Campus-wide legacy listing','59–61',
                'Superseded','Superseded','','superseded — 2026 programme routes')
    """)


def publish_polytechnic(db):
    for id_, pages, combined, field in ((738, "34–36, 113", 300, "pcm_eng_combo"),
                                        (739, "37, 113", 140, "math_eng_combo")):
        name, group, score, description = db.execute(
            "SELECT name, university_group, required_total, description_html FROM legacy_admission WHERE id=?",
            (id_,),
        ).fetchone()
        description = description.replace("Requirements:", "၂၀၂၆ ခုနှစ် ဝင်ခွင့်သတ်မှတ်ချက်များ", 1)
        db.execute("""
            INSERT OR IGNORE INTO admission_2026_review
            (review_key, legacy_id, university, program, printed_pages, minimum_total, minimum_combined,
             combined_subjects, stream_status, region_rule, burmese_requirements_html, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'STEAMS-1 or STEAMS-2', 'Nationwide', ?,
                    'published — technical admissions')
        """, (f"legacy:{id_}", id_, group, name, pages, score, combined, field, description))


def flag_unverified_streams(db):
    rows = db.execute("""
        SELECT r.review_key, r.burmese_requirements_html, a.required_subjects_json
        FROM admission_2026_review r
        JOIN legacy_admission a ON a.id=r.legacy_id
        WHERE (a.id BETWEEN 16 AND 47 OR a.id BETWEEN 75 AND 685)
          AND r.review_status IN ('published — score and wording only', 'published — general arts and science')
          AND r.stream_status IN ('Major stream list needs confirmation', 'Campus stream follow-up',
                                  'Legacy stream filter retained; 2026 exclusion unverified', ?)
    """, (UNVERIFIED_STREAM,)).fetchall()
    changes = []
    for key, description, raw in rows:
        options = json.loads(raw)
        if not options:
            continue
        if isinstance(options[0], str):
            options = [options]
        if any(not any(set(option).issubset(stream) for option in options) for stream in SUPPORTED_STREAMS):
            parts = [part for part in description.split("\n\n") if part != STREAM_NOTE]
            parts.insert(len(parts) - 1, STREAM_NOTE)
            changes.append((UNVERIFIED_STREAM, "\n\n".join(parts), key))
    db.executemany("""
        UPDATE admission_2026_review SET stream_status=?, burmese_requirements_html=? WHERE review_key=?
    """, changes)
    return len(changes)


if __name__ == "__main__":
    with sqlite3.connect((ROOT / "maintenance/unifit.sqlite").as_uri() + "?mode=rw", uri=True) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        columns = {row[1] for row in db.execute("PRAGMA table_info(admission_2026_review)")}
        if "centers_2026_json" not in columns:
            db.execute("ALTER TABLE admission_2026_review ADD COLUMN centers_2026_json TEXT")
        regional_routes(db)
        changed = db.execute("""
            UPDATE admission_2026_review SET stream_status='Any 2026 matriculation stream'
            WHERE legacy_id BETWEEN 48 AND 74 AND review_status='published — score and wording only'
        """).rowcount
        assert changed == 27
        resolve_law(db)
        academy_medicine(db)
        publish_polytechnic(db)
        print(f"{flag_unverified_streams(db)} routes shown with an exam-stream confirmation note")
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
