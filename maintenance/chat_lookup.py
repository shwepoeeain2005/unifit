"""Search the published admissions and reviewed guide data for local answers."""

from contextlib import closing
from html.parser import HTMLParser
import re
import sqlite3
from unicodedata import normalize
from urllib.parse import unquote, urlsplit

from chat_model import campus_short_paths


class ArticleText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.links = []
        self.feed(html or "")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "a" and (href := dict(attrs).get("href")):
            url = urlsplit(href)
            if not url.scheme and not url.netloc:
                self.links.append(unquote(url.path).removeprefix("./"))

    @property
    def text(self):
        return " ".join(" ".join(self.parts).split())


MAJOR = re.compile(r"\b(?:majors?|program(?:me)?s?|study|courses?|syllab\w*|subjects?)\b|မေဂျာ|ဘာသာရပ်|ဘာသာစကား|သင်ရ|သင်လို့", re.I)
ENTRY = re.compile(r"\b(?:entry|admissions?|requirements?|scores?|marks?|cut[ -]?off|minimum)\b|ဝင်ခွင့်|လိုအပ်ချက်|အမှတ်|ဘယ်နှမှတ်|ဘယ်နှစ်မှတ်", re.I)
COMPARE = re.compile(r"\b(?:compare|comparison|better|versus|vs|differences?)\b|နှိုင်းယှဉ်|ပိုကောင်း|ကွာခြား", re.I)
LOCATION = re.compile(r"\b(?:location|locations|located|addresses?)\b|တည်နေရာ|ဘယ်နား|ဘယ်မှာ", re.I)
FOLLOWUP = re.compile(r"^\s*(?:what about|how about|and )|ကရော[။?\s]*$", re.I)
COMPUTING = re.compile(r"\bcomput(?:ing|er science|er technology)\b|ကွန်ပျူတာ", re.I)
SUBJECT_GROUPS = {
    "math_eng_combo": "Math + English",
    "pcm_eng_combo": "Physics + Chemistry + Math + English",
    "phy_math_or_chem_combo": "Physics + Math or Physics + Chemistry",
    "pcm_bio_combo": "Physics + Chemistry + Math + Biology",
}
MAJOR_ALIASES = {
    "chinese": "တရုတ်", "japanese": "ဂျပန်", "english": "အင်္ဂလိပ်",
    "physics": "ရူပဗေဒ", "chemistry": "ဓာတုဗေဒ", "mathematics": "သင်္ချာ",
    "geography": "ပထဝီဝင်", "history": "သမိုင်း", "law": "ဥပဒေ",
    "engineering": "အင်ဂျင်နီယာ", "economics": "စီးပွားရေးပညာ",
    "computer science": "ကွန်ပျူတာသိပ္ပံ",
}


def normalized(value):
    value = normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[a-z0-9]+|[\u1000-\u109f]+", value))


GUIDE_CONCEPTS = (
    (r"\b(?:remote learning|distance learning|study from home|correspondence courses?)\b|အဝေး\s*သင်", "distance education အဝေးသင်"),
    (r"\b(?:can i apply|who can apply|qualify|prerequisites)\b", "entry eligibility"),
    (r"\b(?:degree options|fields of study|what can i study)\b", "majors programmes"),
    (r"\b(?:school fees|course fees|study costs)\b", "tuition fees"),
    (r"\b(?:doctor s note|doctor note|sick leave)\b", "medical certificate leave"),
    (r"\b(?:missed the deadline|after the closing date)\b", "late application deadline"),
    (r"\b(?:redo the exam|retake the exam|makeup exams?)\b|ပြန်ဖြေ", "resit exams နောက်ဆက်တွဲ"),
    (r"\b(?:switch majors?|switch programmes?)\b|မေဂျာပြောင်း", "transfer major ဘာသာပြောင်း"),
)


def guide_query(question):
    query = normalized(question)
    for pattern, replacement in GUIDE_CONCEPTS:
        query = re.sub(pattern, replacement, query)
    return query


def mentioned(label, question):
    label = normalized(label)
    return bool(label and re.search(r"(?<![a-z0-9])" + re.escape(label) + r"(?![a-z0-9])", question))


def campus_matches(question, cards, admissions_names):
    query = normalized(question)
    paths = campus_short_paths(question)
    matches = [(normalized(name), path) for name, path in admissions_names
               if mentioned(name, query)]
    for label, path in matches:
        if not any(path != other_path and label in other for other, other_path in matches):
            paths.add(path)
    return {path for path in paths if path in cards}


def page_numbers(raw):
    pages = set()
    for start, end in re.findall(r"(\d+)(?:\s*[–-]\s*(\d+))?", raw or ""):
        first, last = int(start), int(end or start)
        if 1 <= first <= last <= 217:
            pages.update(range(first, last + 1))
    return pages


def major_label(title):
    return normalized(re.sub(r"^B\.A\. \((.+)\)$|\s*\(B\.[^)]+\)$", r"\1", title, flags=re.I))


def local_lookup(database, question, language, page, history):
    query = normalized(question)
    my = language == "my" or (language == "auto" and bool(re.search(r"[\u1000-\u109f]", question)))
    language = "my" if my else "en"
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        guide_question = guide_query(question)
        if FOLLOWUP.search(question) and not campus_short_paths(question):
            previous = next((turn["text"] for turn in reversed(history) if turn["user"]), "")
            if re.search(r"\bdistance education\b|အဝေးသင်", guide_query(previous)):
                guide_question += " distance education အဝေးသင်"
        if re.search(r"\bdistance education\b|အဝေးသင်|\bpage [0-9၀-၉]|စာမျက်နှာ ?[0-9၀-၉]", guide_question):
            reviewed = guide_lookup(db, guide_question, language)
            if reviewed:
                return reviewed
        cards = {row["detail_url"]: row for row in db.execute("SELECT * FROM university_card")}
        cards.update({row["detail_url"]: row for row in db.execute(
            """SELECT detail_url, university AS name, location AS address FROM regional_polytechnic_campus"""
        )})
        admissions = {path: [] for path in cards}
        names = [(row["name"], path) for path, row in cards.items()]
        for row in db.execute("""SELECT r.*, o.legacy_id AS alternative
                                 FROM admission_2026_review r LEFT JOIN admission_total_or_math_english o
                                 ON o.legacy_id = r.legacy_id WHERE r.review_status LIKE 'published%'"""):
            article = ArticleText(row["burmese_requirements_html"])
            path = next((link for link in article.links if link in cards), None)
            if path:
                admissions[path].append((row, article))
                names.append((row["university"], path))
        sections = [row for row in db.execute("SELECT page_path, title, content_html FROM detail_section")
                    if row["page_path"] in cards and row["title"].casefold() not in {"website link", "admission requirements"}]
        paths = campus_matches(question, cards, set(names))
        if paths and FOLLOWUP.search(question) and not (ENTRY.search(question) or MAJOR.search(question)
                                                        or LOCATION.search(question)):
            previous = next((turn["text"] for turn in reversed(history) if turn["user"]
                             and (ENTRY.search(turn["text"]) or MAJOR.search(turn["text"])
                                  or LOCATION.search(turn["text"]))), "")
            if previous:
                question = f"{question} {previous}"
                query = normalized(question)
        if not paths:
            previous = next((paths for turn in reversed(history) if turn["user"]
                             and (paths := campus_matches(turn["text"], cards, set(names)))), set())
            paths = {page} if page in cards else previous

        labels = {major_label(section["title"]) for section in sections}
        labels.update(major_label(row["program"]) for path in paths for row, _ in admissions[path])
        labels.discard("")
        requested = {label for label in labels if mentioned(label, query)
                     or (label in MAJOR_ALIASES and MAJOR_ALIASES[label] in question)}
        requested = {label for label in requested if not any(label != other and label in other for other in requested)}
        if COMPUTING.search(question) and not requested:
            requested = {"computing"}
        entry, location, compare = ENTRY.search(question), LOCATION.search(question), COMPARE.search(question)
        if paths and (requested or entry or location or compare or MAJOR.search(question)):
            scoped = sorted(paths, key=lambda path: cards[path]["name"].casefold())
            links = [{"url": path + ("#admission-requirements" if entry and admissions[path] else ""),
                      "label": cards[path]["name"]} for path in scoped]
            if compare and len(paths) >= 2 and not (requested or entry or location or MAJOR.search(question)):
                text = ("ဘယ်အချက်ကို အဓိကထားပြီး နှိုင်းယှဉ်ချင်ပါသလဲ။ မေဂျာ၊ တည်နေရာ၊ ဒါမှမဟုတ် ဝင်ခွင့်လိုအပ်ချက်တွေပါ။"
                        if my else "What matters most to you: the major, campus location, or entry requirements?")
                return {"text": text, "language": language, "links": links}
            blocks, citations = [], set()
            for path in scoped:
                card = cards[path]
                rows = [(row, article) for row, article in admissions[path]
                        if not requested or matches_major(row["program"], requested, question)]
                descriptions = [section for section in sections if section["page_path"] == path and requested
                                and matches_major(section["title"], requested, question)]
                if location:
                    body = card["address"] or ("တည်နေရာ မဖော်ပြထားပါ။" if my else "No address is listed.")
                elif entry and rows:
                    for row, _ in rows:
                        citations.update(page_numbers(row["printed_pages"]))
                    body = entry_summary(rows, my)
                elif not entry and (rows or descriptions):
                    programmes = list(dict.fromkeys(row["program"] for row, _ in rows))
                    for row, _ in rows:
                        citations.update(page_numbers(row["printed_pages"]))
                    body = ("၂၀၂၆ သင်တန်းများ — " if my else "2026 programmes: ") + ", ".join(programmes) if programmes else ""
                    if descriptions:
                        overview = " ".join(f"{section['title']} — {overview_excerpt(section['content_html'])}"
                                            for section in descriptions[:3])
                        body = (body + "\n" if body else "") + ("UniFit မေဂျာမိတ်ဆက် — " if my else "UniFit major overview: ") + overview
                else:
                    body = ("ဒီမေးခွန်းအတွက် အတည်ပြုထားတဲ့ အချက်အလက် မရှိသေးပါ။" if my else
                            "UniFit has no verified record for this question.")
                blocks.append(f"{card['name']}\n{body}")
            return {"text": "\n\n".join(blocks), "language": language, "pages": sorted(citations), "links": links}

        if requested and not paths:
            matched = [section for section in sections if matches_major(section["title"], requested, question)]
            if matched:
                examples = {section["page_path"]: cards[section["page_path"]]["name"] for section in matched}
                example = matched[0]
                name = cards[example["page_path"]]["name"]
                text = (f"UniFit မေဂျာမိတ်ဆက် ({name} မှ နမူနာ)\n" if my else
                        f"UniFit major overview (example from {name})\n")
                text += f"{example['title']} — {overview_excerpt(example['content_html'])}"
                text += ("\n\nဘယ်တက္ကသိုလ်အတွက် သိချင်ပါသလဲ။" if my else
                         "\n\nWhich university would you like to ask about for this major?")
                return {
                    "text": text,
                    "language": language,
                    "links": [{"url": path, "label": name} for path, name in list(examples.items())[:5]],
                }
        return guide_lookup(db, guide_question, language)


def overview_excerpt(html):
    text = ArticleText(html).text
    if len(text) <= 650:
        return text
    return text[:650].rsplit(" ", 1)[0] + "…"


def matches_major(title, requested, question):
    label = major_label(title)
    return any(mentioned(term, label) or (term in MAJOR_ALIASES and MAJOR_ALIASES[term] in title)
               or (label in MAJOR_ALIASES and MAJOR_ALIASES[label] in term) for term in requested) or (
        bool(COMPUTING.search(question)) and (bool(COMPUTING.search(title)) or "computer studies" in label)
    )


def entry_summary(rows, my):
    lines = []
    seen = set()
    for row, article in rows:
        total, combined, subjects, english = (row[key] for key in (
            "minimum_total", "minimum_combined", "combined_subjects", "minimum_english"
        ))
        either = row["alternative"] and total is not None and combined is not None
        facts = []
        if total is not None:
            facts.append(f"{total} စုစုပေါင်း" if my else f"{total} total")
        if combined is not None:
            group = SUBJECT_GROUPS.get(subjects, "ဘာသာရပ်ပေါင်း" if my else "combined subjects")
            facts.append(f"{combined} ({group})")
        if english is not None:
            facts.append(f"{english} အင်္ဂလိပ်စာ" if my else f"{english} in English")
        scores = ((" သို့မဟုတ် " if my else " or ") if either else ", ").join(facts)
        if my and article.text:
            scores = article.text.removesuffix("more details").strip()
        if not scores:
            scores = "သီးခြားရမှတ် စည်းမျဉ်း မတွေ့ပါ။" if my else "No numeric minimum in this reviewed record."
        key = (scores, row["printed_pages"])
        if key not in seen:
            lines.append(f"• {row['program']}: {scores}")
            seen.add(key)
    return "\n".join(lines)


def guide_lookup(db, query, language):
    terms = set(query.split()) - {"what", "when", "where", "which", "how", "the", "is", "a", "i", "to", "for", "of"}
    rows = db.execute("SELECT * FROM guide_verified_answers WHERE edition = 2026").fetchall()
    page_match = re.search(r"(?:\bpage |စာမျက်နှာ ?)([0-9၀-၉]{1,3})(?![0-9၀-၉])", query)
    if page_match:
        page = int(page_match[1].translate(str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")))
        checked = [row for row in rows if row["printed_page"] == page]
        if checked:
            my = language == "my"
            text = "\n\n".join(dict.fromkeys(row["summary_my"] if my else row["summary_en"] for row in checked))
            return {"text": text, "language": language, "pages": [page]}
        coverage = db.execute("SELECT coverage FROM guide_page_coverage WHERE printed_page = ?", (page,)).fetchone()
        present = coverage and coverage[0] != "not in supplied files"
        if language == "my":
            text = f"စာမျက်နှာ {page} ကို စစ်ဆေးအတည်ပြုဆဲ ဖြစ်ပါတယ်။" if present else f"UniFit မှာ စာမျက်နှာ {page} ရဲ့ မိတ္တူ မရှိသေးပါ။"
        else:
            text = f"UniFit has a scan for page {page}, and its text is awaiting review." if present else f"UniFit does not have a copy of page {page}."
        return {"text": text, "language": language}
    scored = []
    distance = bool(re.search(r"\bdistance\b|အဝေးသင်", query))
    for row in rows:
        if row["section_key"].startswith("distance-") != distance:
            continue
        label = normalized(row["label"] or "")
        simple = set(normalized(row["topic"] + " " + row["scope"]).split())
        english_match = len(terms & simple)
        burmese_match = sum(keyword in query for keyword in normalized(row["keywords_my"]).split())
        score = english_match + 2 * burmese_match + (4 if mentioned(label, query) else 0)
        if score:
            scored.append((score, row))
    if not scored:
        return None
    score, row = max(scored, key=lambda item: item[0])
    if score < 2 and not any(mentioned(term, query) for term in ("tuition", "fees", "documents", "preference")):
        return None
    my = language == "my"
    text = row["summary_my"] if my else row["summary_en"]
    if not my and row["amount"] is not None and mentioned(row["label"], query):
        text = f"{row['label']}: {row['amount']} {row['unit'] or ''}. {row['conditions']}"
    return {"text": text, "language": language, "pages": [row["printed_page"]],
            "link": "requirement.html"}
