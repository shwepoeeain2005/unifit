"""Export the editable UniFit SQLite data to static browser scripts."""

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ADMISSIONS_ID = "admission-requirements"
NO_PROGRAMME_CUTOFF = "ဤဘာသာရပ်အတွက် ၂၀၂၆ လမ်းညွှန်တွင် သီးခြားအနည်းဆုံးရမှတ် မဖော်ပြထားပါ။"
LINK = re.compile(r'<a\b[^>]*\bhref="([^"]+)"[^>]*>.*?</a>', re.IGNORECASE | re.DOTALL)


def write_script(path, name, value, trailing_script=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.{name} = {data};\n{trailing_script}", encoding="utf-8")


def pack_admissions(admissions):
    """Deduplicate repeated subject lists and detail page URLs for a smaller download."""
    pages = []
    page_index = {}
    subjects = []
    subject_index = {}
    routes = []
    for entry in admissions:
        page, _, fragment = entry["detailUrl"].partition("#")
        if page not in page_index:
            page_index[page] = len(pages)
            pages.append(page)
        subject_key = json.dumps(entry.get("requiredSubjects"), ensure_ascii=False, separators=(",", ":"))
        if subject_key not in subject_index:
            subject_index[subject_key] = len(subjects)
            subjects.append(entry.get("requiredSubjects"))
        route = {
            "n": entry["name"],
            "u": page_index[page],
            "h": fragment,
            "r": subject_index[subject_key],
        }
        if entry.get("group") is not None:
            route["g"] = entry["group"]
        if entry.get("requiredTotal") is not None:
            route["t"] = entry["requiredTotal"]
        if entry.get("subjectSpecific"):
            route["s"] = entry["subjectSpecific"]
        if entry.get("allowedCenters") is not None:
            route["c"] = entry["allowedCenters"]
        if entry.get("totalOrMathEnglish"):
            route["o"] = True
        if entry.get("confirmExamStream"):
            route["x"] = True
        routes.append(route)
    return {"pages": pages, "subjects": subjects, "routes": routes}


ADMISSIONS_EXPAND = """window.unifitAdmissions = (window.unifitAdmissionsPacked.routes || []).map(function (route) {
  var entry = {
    name: route.n,
    detailUrl: window.unifitAdmissionsPacked.pages[route.u] + (route.h ? "#" + route.h : ""),
    requiredSubjects: window.unifitAdmissionsPacked.subjects[route.r]
  };
  if (route.g !== undefined) entry.group = route.g;
  if (route.t !== undefined) entry.requiredTotal = route.t;
  if (route.s !== undefined) entry.subjectSpecific = route.s;
  if (route.c !== undefined) entry.allowedCenters = route.c;
  if (route.o) entry.totalOrMathEnglish = true;
  if (route.x) entry.confirmExamStream = true;
  return entry;
});
"""


def write_admissions_script(path, admissions):
    write_script(path, "unifitAdmissionsPacked", pack_admissions(admissions), ADMISSIONS_EXPAND)


def unpack_admissions(packed):
    routes = []
    for route in packed["routes"]:
        entry = {
            "name": route["n"],
            "detailUrl": packed["pages"][route["u"]] + (f"#{route['h']}" if route.get("h") else ""),
            "requiredSubjects": packed["subjects"][route["r"]],
        }
        if "g" in route:
            entry["group"] = route["g"]
        if "t" in route:
            entry["requiredTotal"] = route["t"]
        if "s" in route:
            entry["subjectSpecific"] = route["s"]
        if "c" in route:
            entry["allowedCenters"] = route["c"]
        if route.get("o"):
            entry["totalOrMathEnglish"] = True
        if route.get("x"):
            entry["confirmExamStream"] = True
        routes.append(entry)
    return routes


def admission_sections(admissions, cards):
    by_page = {card["detail_url"]: [] for card in cards}
    for entry in admissions:
        description = entry.pop("description")
        links = []
        for match in LINK.finditer(description):
            url = urlsplit(match[1])
            page = unquote(url.path)
            if not url.scheme and not url.netloc and page in by_page:
                links.append((page, match))
        if len(links) != 1:
            raise ValueError(f"Expected one university detail link for {entry['name']}")
        page, link = links[0]
        description = description[:link.start()] + description[link.end():]
        repeated_title = f"{entry['name']} ဘွဲ့သင်တန်း။"
        rules = list(dict.fromkeys(line for raw in description.splitlines()
                                   if (line := raw.strip()) and line != repeated_title))
        by_page[page].append((entry, rules))

    content = {}
    for page, routes in by_page.items():
        if not routes:
            content[page] = {"shared": [], "programmes": []}
            continue
        shared = [rule for rule in routes[0][1] if all(rule in rules for _, rules in routes)]
        specific = defaultdict(list)
        for entry, rules in routes:
            specific[tuple(rule for rule in rules if rule not in shared)].append(entry)
        programmes = []
        score_exceptions = all(
            rules == (NO_PROGRAMME_CUTOFF,) or all(entry.get("subjectSpecific", {}).get("eng") is not None for entry in entries)
            for rules, entries in specific.items()
        )
        for rules, entries in specific.items():
            anchor = ADMISSIONS_ID
            if rules == (NO_PROGRAMME_CUTOFF,) and len(specific) > 1 and score_exceptions:
                shared.append("သီးခြားရမှတ် ဖော်ပြထားသည့် အောက်ပါဘာသာရပ်များမှအပ အခြားဘာသာရပ်များအတွက် ၂၀၂၆ လမ်းညွှန်တွင် သတ်မှတ်အနည်းဆုံးရမှတ် မဖော်ပြထားပါ။")
            elif rules:
                names = list(dict.fromkeys(entry["name"] for entry in entries))
                digest = sha256(repr((Path(page).name, names)).encode("utf-8")).hexdigest()[:16]
                anchor = f"admission-{digest}"
                programmes.append({"id": anchor, "names": names, "rules": rules})
            for entry in entries:
                entry["detailUrl"] = f"{quote(page)}#{anchor}"
        content[page] = {"shared": shared, "programmes": programmes}
    return content


def export_site(root):
    database = root / "maintenance" / "unifit.sqlite"
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        campuses = {row["technology_card_id"]: row for row in db.execute("SELECT * FROM regional_polytechnic_campus")}
        retired_cards = {row["computing_card_id"] for row in campuses.values()}
        cards = []
        for row in db.execute("SELECT * FROM university_card ORDER BY id"):
            if row["id"] in retired_cards:
                continue
            card = dict(row)
            if campus := campuses.get(row["id"]):
                card.update(name=campus["university"], address=campus["location"],
                            categories="pu", detail_url=campus["detail_url"])
            cards.append(card)
        write_script(root / "data" / "universities.js", "unifitCards", cards)

        science_streams = [
            ["myan", "eng", "math", "phy", "chem", "bio"],
            ["myan", "eng", "math", "phy", "chem", "eco"],
        ]
        admissions = []
        for row in db.execute("""
            SELECT a.*, r.minimum_total AS published_total, r.minimum_english AS published_english,
                   r.burmese_requirements_html AS published_description,
                   r.program AS published_program,
                   r.review_status AS publication_type,
                   r.minimum_combined AS published_combined,
                   r.combined_subjects AS published_combined_subjects,
                   r.region_rule AS published_region_rule,
                   r.stream_examples_json AS published_subjects,
                   r.stream_status AS published_stream_status,
                   r.centers_2026_json AS published_centers,
                   o.legacy_id AS either_threshold
            FROM legacy_admission a
            LEFT JOIN admission_total_or_math_english o ON o.legacy_id = a.id
            LEFT JOIN admission_2026_review r
              ON r.legacy_id = a.id AND r.review_status IN (
                  'published — score and wording only', 'published — regional wording only',
                  'published — technical admissions', 'published — computing admissions',
                  'published — economics and management', 'published — education admissions',
                  'published — foreign languages', 'published — general arts and science',
                  'published — specialist admissions'
              )
            WHERE NOT EXISTS (
                SELECT 1 FROM admission_2026_review p
                WHERE p.legacy_id = a.id AND p.review_status IN (
                    'published — regional polytechnic', 'withheld — unverified 2026 intake',
                    'superseded — 2026 programme routes'
                )
            )
            ORDER BY a.id, r.review_key
        """):
            entry = dict(name=row["name"], requiredTotal=row["required_total"],
                         description=row["description_html"])
            if row["university_group"] is not None:
                entry["group"] = row["university_group"]
            for key, column in (("subjectSpecific", "subject_minimums_json"),
                                ("requiredSubjects", "required_subjects_json"),
                                ("allowedCenters", "allowed_centers_json")):
                value = json.loads(row[column])
                if value is not None:
                    entry[key] = value
            if row["publication_type"] in {
                "published — score and wording only", "published — economics and management",
                "published — education admissions",
                "published — general arts and science",
            }:
                entry["requiredTotal"] = row["published_total"]
                entry["subjectSpecific"] = {}
            if row["publication_type"] == "published — score and wording only":
                entry["name"] = row["published_program"]
                if row["published_stream_status"] == "Any 2026 matriculation stream":
                    entry["requiredSubjects"] = []
            if row["publication_type"] == "published — education admissions":
                entry["allowedCenters"] = "all"
                entry["requiredSubjects"] = json.loads(row["published_subjects"] or "[]")
            if row["publication_type"] == "published — foreign languages":
                english = row["published_english"]
                entry.update(name=row["published_program"], group=row["name"],
                             requiredTotal=row["published_total"], allowedCenters="all",
                             requiredSubjects=[], subjectSpecific={} if english is None else {"eng": english})
            if row["publication_type"] == "published — general arts and science":
                if row["published_subjects"] is not None:
                    entry["requiredSubjects"] = json.loads(row["published_subjects"])
                if row["published_combined_subjects"] == "Physics + Math or Physics + Chemistry":
                    entry["subjectSpecific"] = {"phy_math_or_chem_combo": row["published_combined"]}
                    if row["university_group"] == "Yadanabon University":
                        entry["allowedCenters"] = [center for center in entry["allowedCenters"] if center != "npt"]
            if row["publication_type"] == "published — specialist admissions":
                entry.update(requiredTotal=row["published_total"], allowedCenters="all", subjectSpecific={},
                             requiredSubjects=json.loads(row["published_subjects"] or "[]"))
            if row["publication_type"] == "published — economics and management":
                entry["requiredSubjects"] = []
                if row["published_region_rule"] == "Designated areas; up to 10% outside designated areas":
                    entry["allowedCenters"] = "all"
            if row["publication_type"] in {"published — technical admissions", "published — computing admissions"}:
                if row["publication_type"] == "published — computing admissions":
                    entry["name"] = row["published_program"]
                entry["requiredTotal"] = row["published_total"]
                entry["subjectSpecific"] = {}
                entry["requiredSubjects"] = science_streams
                if row["published_combined"] is not None:
                    field = row["published_combined_subjects"]
                    if field not in {"pcm_eng_combo", "pcm_bio_combo", "math_eng_combo"}:
                        raise ValueError(f"Unknown score combination: {field}")
                    entry["subjectSpecific"][field] = row["published_combined"]
                    if field == "pcm_bio_combo":
                        entry["requiredSubjects"] = ["myan", "eng", "math", "phy", "chem", "bio"]
                if row["published_region_rule"] == "Local priority; outside region if places remain":
                    entry["allowedCenters"] = "all"
            if row["published_description"] is not None:
                entry["description"] = row["published_description"]
            if row["published_centers"] is not None:
                entry["allowedCenters"] = json.loads(row["published_centers"])
            if row["published_stream_status"] == "2026 stream unverified; show with confirmation note":
                entry["requiredSubjects"] = []
                entry["confirmExamStream"] = True
            if row["either_threshold"] is not None:
                if not isinstance(entry["requiredTotal"], int) or not isinstance(
                    entry.get("subjectSpecific", {}).get("math_eng_combo"), int
                ):
                    raise ValueError(f"Missing alternative score thresholds for admission {row['id']}")
                entry["totalOrMathEnglish"] = True
            admissions.append(entry)
        for row in db.execute("""
            SELECT * FROM admission_2026_review
            WHERE review_status = 'published — regional polytechnic'
            ORDER BY university, program DESC
        """):
            minimums = {}
            if row["minimum_combined"] is not None:
                minimums["pcm_eng_combo"] = row["minimum_combined"]
            admissions.append(dict(
                name=row["program"], group=row["university"],
                requiredTotal=row["minimum_total"], requiredSubjects=science_streams,
                subjectSpecific=minimums, allowedCenters="all",
                description=row["burmese_requirements_html"],
            ))
        for row in db.execute("""
            SELECT university, program, burmese_requirements_html, centers_2026_json FROM admission_2026_review
            WHERE review_status = 'published — new general arts and science'
            ORDER BY university, program
        """):
            admissions.append(dict(name=row["program"], group=row["university"], requiredTotal=None,
                                   allowedCenters=json.loads(row["centers_2026_json"] or '"all"'),
                                   description=row["burmese_requirements_html"]))
        for row in db.execute("""
            SELECT * FROM admission_2026_review
            WHERE review_status = 'published — new specialist admission'
            ORDER BY university, review_key
        """):
            admissions.append(dict(name=row["program"], group=row["university"], requiredTotal=row["minimum_total"],
                                   allowedCenters="all", requiredSubjects=json.loads(row["stream_examples_json"] or "[]"),
                                   subjectSpecific={"phy_math_or_chem_combo": row["minimum_combined"]}
                                   if row["combined_subjects"] == "Physics + Math or Physics + Chemistry" else {},
                                   description=row["burmese_requirements_html"]))
        pages = db.execute("SELECT page_path, export_key FROM detail_page ORDER BY export_key").fetchall()
        requirements = admission_sections(admissions, cards)
        missing_pages = requirements.keys() - {path for path, _ in pages}
        if missing_pages:
            raise ValueError(f"Admission boxes need detail data for: {', '.join(sorted(missing_pages))}")
        write_admissions_script(root / "data" / "admissions.js", admissions)

        unverified = [
            dict(university=row["university"], program=row["program"], status=row["review_status"])
            for row in db.execute(
                """
                SELECT university, program, review_status
                FROM admission_2026_review
                WHERE review_status LIKE '%withheld%' OR review_status LIKE '%unverified%'
                ORDER BY university, program
                """
            )
        ]
        write_script(root / "data" / "unverified.js", "unifitUnverified", unverified)

        card_by_url = {card["detail_url"]: card for card in cards}
        for page_path, export_key in pages:
            sections = []
            for section_id, title, content in db.execute(
                "SELECT id, title, content_html FROM detail_section WHERE page_path = ? ORDER BY position",
                (page_path,),
            ):
                images = [dict(row) for row in db.execute(
                    "SELECT image_path, alt_text FROM section_image WHERE section_id = ? ORDER BY position",
                    (section_id,),
                )]
                sections.append({"title": title, "html": content, "images": images})
            card = card_by_url.get(page_path)
            campus = None
            if card:
                campus = {"name": card["name"], "address": card["address"]}
            else:
                poly = db.execute(
                    "SELECT university, location FROM regional_polytechnic_campus WHERE detail_url = ?",
                    (page_path,),
                ).fetchone()
                if poly:
                    campus = {"name": poly["university"], "address": poly["location"]}
            write_script(
                root / "data" / "details" / f"{export_key}.js",
                "unifitDetail",
                {"campus": campus, "sections": sections, "admissions": requirements.get(page_path)},
                "window.unifitSections = window.unifitDetail.sections;\n",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    export_site(parser.parse_args().root)
