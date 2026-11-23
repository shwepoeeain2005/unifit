"""Shared SQLite-backed chat handler and local UniFit preview."""

import argparse
from contextlib import closing
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
from urllib.error import HTTPError

from chat_model import CAMPUS_SHORT_NAMES, campus_short_paths, historical_answer, model_answer
from chat_lookup import guide_query, local_lookup


ROOT = Path(__file__).resolve().parents[1]
DATABASE = Path(__file__).with_name("unifit.sqlite")
ROUTES = (
    (r"dent|သွားဘက်", "dentistry-interview", "requirement.html"),
    (r"(?:medicine|medical|ဆေးတက္ကသိုလ်).*(?:interview|date|လူတွေ့|နှုတ်မေး|ဘယ်တော့)|(?:interview|လူတွေ့).*?(?:medicine|medical|ဆေးတက္ကသိုလ်)", "medicine-interview", "requirement.html"),
    (r"preference|rank.*choice|ဦးစားပေး|ဦးစားပေး", "preference-order", "requirement.html#step-4"),
    (r"deadline|submit|သတ်မှတ်ရက်|တင်သွင်း|ဘယ်မှာ.*တင်", "application-submission", "requirement.html#submission"),
    (r"tuition|enrollment fee|ကျောင်းလခ|ကျောင်းအပ်ကြေး", "first-year-fees", "requirement.html"),
    (r"document|paperwork|exam records|application packet|စာရွက်စာတမ်း|စာရွက်စာတန်း|အမှတ်စာရင်း|လျှောက်လွှာအစုံ", "application-documents", "requirement.html#step-1"),
)


def answer(question, language, previous):
    question = question.casefold()
    if language == "auto":
        language = "my" if re.search(r"[\u1000-\u109f]", question) else "en"
        if not re.search(r"[a-z\u1000-\u109f]", question):
            language = "my"
    my = language == "my"
    if re.search(r"\b(?:eligible|qualify)\b|where can i apply|which universit|ဘယ်တက္ကသိုလ်|ဝင်ခွင့်ရနိုင်", question):
        return {
            "text": "သင့်အမှတ်၊ ဘာသာတွဲနှင့် စာစစ်ဌာနကို Search Your Uni မှာ ထည့်ပြီး လျှောက်ထားနိုင်သည့် တက္ကသိုလ်များကို ကြည့်ပါ။" if my else
                    "Enter your marks, subject combination and exam centre in Search Your Uni to check which options match.",
            "link": "search.html", "language": language,
        }
    route = next((item for item in ROUTES if re.search(item[0], question)), None)
    if route is None and re.fullmatch(r"(?:more details?|explain(?: more)?|tell me more|အသေးစိတ်(?:ရှင်းပြပါ)?)[?. ]*", question):
        route = next((item for item in ROUTES if item[1] == previous), None)
    if route is None:
        return {"text": "ဒီမေးခွန်းအတွက် အတည်ပြုထားတဲ့ အချက်အလက် မတွေ့ပါ။ တက္ကသိုလ်နာမည်နဲ့ သိချင်တဲ့အချက်ကို ပိုတိတိကျကျ မေးနိုင်ပါတယ်။" if my else
                        "I couldn’t find a verified answer. Can you name the university and say what you’d like to know?",
                "language": language}
    _, section, link = route
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute(
            """SELECT summary_en, summary_my, printed_page FROM guide_verified_answers
               WHERE edition = 2026 AND section_key = ? LIMIT 1""", (section,),
        ).fetchone()
    if row is None:
        return {"text": "အတည်ပြုထားတဲ့ အဖြေ မတွေ့ပါ။" if my else "No verified answer is available.", "language": language}
    english, burmese, page = row
    if my and section == "dentistry-interview":
        burmese = "သွားဘက်ဆိုင်ရာ ဆေးတက္ကသိုလ်များတွင် လူတွေ့ သို့မဟုတ် နှုတ်မေးစာမေးပွဲဖြင့် ရွေးချယ်သည်။ စာမျက်နှာ ၁၃၁ တွင် ဖြေဆိုရမည့်ရက်ကို မဖော်ပြထားပါ။"
    if my and section == "medicine-interview":
        burmese += " စာမျက်နှာ ၂၃ တွင် လူတွေ့ရက်ကို မဖော်ပြထားပါ။"
    return {"text": burmese if my else english, "page": page, "section": section, "link": link, "language": language}


def application_quick_answer(question, language):
    if language == "auto":
        language = "my" if re.search(r"[\u1000-\u109f]", question) else "en"
    my = language == "my"
    question = question.casefold()
    if re.search(r"who.*(?:exam records|marksheet|mark sheet)|(?:exam records|marksheet|mark sheet).*(?:free|cost|pay)|အမှတ်စာရင်း.*(?:ဘယ်သူ|ဘယ်မှာ|အခမဲ့|ပေးရ)", question):
        text = ("သင်ဖြေဆိုခဲ့တဲ့ စာစစ်ဌာန ကြီးကြပ်ရေးမှူး (အထက်တန်းကျောင်းအုပ်ကြီး) က အမှတ်စာရင်းနဲ့ အရည်အချင်းမှတ်တမ်းချုပ် ရမှတ်အဆင့်ကို အခမဲ့ ထုတ်ပေးပါတယ်။" if my else
                "The supervisor of the exam centre where you sat the exam issues your exam records. They’re free.")
        anchor = "step-2"
    elif re.search(r"checklist.*(?:documents|paperwork)|(?:documents|paperwork).*checklist|စာရွက်စာတမ်း.*(?:စာရင်း|လိုလဲ)", question):
        text = ("လျှောက်လွှာအစုံမှာ ပါဝင်တာတွေက\n• မှတ်ပုံတင်ခွင့်လျှောက်လွှာ ၂ စောင်\n• ဝင်ခွင့်လျှောက်လွှာ\n• သင်တန်းရွေးချယ်မှုကတ်ပြား\n• ဝင်ခွင့်လမ်းညွှန်နဲ့ စာအိတ်\n\nအမှတ်စာရင်းနဲ့ အရည်အချင်းမှတ်တမ်းချုပ် ရမှတ်အဆင့်ကိုလည်း လျှောက်လွှာနဲ့အတူ ပေးပို့ပါ။" if my else
                "In the application packet:\n• Two registration forms\n• Admission application\n• Programme preference card\n• Admissions guide and envelope\n\nSubmit your exam marks sheet and academic record with the application.")
        anchor = "step-1"
    else:
        return None
    reviewed = answer("application packet", language, None)
    if "page" not in reviewed:
        return None
    return {**reviewed, "text": text, "link": f"requirement.html#{anchor}"}


CAMPUS_ALIASES = {
    "mmu": ("Myanmar Maritime University", "မြန်မာနိုင်ငံရေကြောင်းပညာတက္ကသိုလ်",
            "universities/myanmar-maritime-university-mmu.html"),
    "uit": ("University of Information Technology", "သတင်းအချက်အလက်နည်းပညာတက္ကသိုလ်",
            "universities/uit.html"),
    "ucsy": ("University of Computer Studies (Yangon)", "ရန်ကုန်ကွန်ပျူတာတက္ကသိုလ်",
             "universities/ucsy.html"),
    "nspu": ("Naypyitaw State Polytechnic University", "နေပြည်တော်ပြည်နယ်ပိုလီတက္ကနစ်တက္ကသိုလ်",
             "universities/nspu.html"),
}
INTERVIEW_GUIDE_PAGES = {"mmu": [95, 96, 97], "uit": [53, 54], "ucsy": [51, 52, 53],
                         "nspu": [34, 35, 36, 37, 113]}
MEDICINE_CAMPUSES = {
    "universities/medicine-1.html": "University of Medicine 1, Yangon",
    "universities/medicine-2.html": "University of Medicine 2, Yangon",
    **{f"universities/university-of-medicine-{city.lower()}.html": f"University of Medicine, {city}"
       for city in ("Mandalay", "Magway", "Taunggyi")},
}
INTERVIEW = re.compile(r"\binterviews?\b|လူတွေ့|နှုတ်မေး", re.I)
SHORT_CAMPUS_FOLLOWUP = re.compile(
    r"(?:(?:what|how) about |and )?(?:" + "|".join(CAMPUS_SHORT_NAMES) + r")(?: ?ကရော)?", re.I
)


def campus_interview_answer(question, language, page, history):
    query = question.casefold().strip(" ?။.!“”")
    explicit = [key for key, (name, my_name, _) in CAMPUS_ALIASES.items()
                if re.search(rf"\b{key}\b", query) or name.casefold() in query or my_name in query]
    previous = next(
        (turn["text"] for turn in reversed(history)
         if turn["user"] and not SHORT_CAMPUS_FOLLOWUP.fullmatch(turn["text"].strip(" ?။.!“”"))),
        "",
    )
    followup = SHORT_CAMPUS_FOLLOWUP.fullmatch(query)
    if not (INTERVIEW.search(query) or (followup and INTERVIEW.search(previous))):
        return None
    paths = campus_short_paths(query) | {CAMPUS_ALIASES[key][2] for key in explicit}
    if language == "auto":
        language = "my" if re.search(r"[\u1000-\u109f]", query + (previous if followup else "")) else "en"
    replies = [reply for path in sorted(paths or {page})
               if (reply := interview_for_campus(path, language, bool(paths))) is not None]
    if len(replies) < 2:
        return replies[0] if replies else None
    return {
        "text": "\n\n".join(reply["text"] for reply in replies),
        "language": language,
        "pages": sorted({number for reply in replies for number in reply.get("pages", [])}),
        "links": [{"url": reply["link"], "label": reply["link_label"]} for reply in replies],
        "sources": [source for reply in replies for source in reply.get("sources", [])],
    }


def interview_for_campus(campus_path, language, named):
    campus = next((key for key, (_, _, path) in CAMPUS_ALIASES.items() if campus_path == path), None)
    my = language == "my"
    if campus_path in MEDICINE_CAMPUSES:
        name = MEDICINE_CAMPUSES[campus_path]
        reviewed = answer("medicine interview", language, None)
        if "page" not in reviewed:
            return None
        text = (f"{name} မှာ ပဏာမရွေးချယ်ခံရသူတွေ လူတွေ့ သို့မဟုတ် နှုတ်မေးစာမေးပွဲ ဖြေဆိုရပါတယ်။ UniFit မှာ အတည်ပြုထားတဲ့ လူတွေ့ရက် မရှိသေးပါ။"
                if my else f"Yes. Shortlisted applicants to {name} must take an interview or oral examination. UniFit has no verified interview date.")
        return {**reviewed, "text": text, "pages": [reviewed["page"]], "link": campus_path, "link_label": name}
    if campus is None:
        if not named:
            return None
        with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
            row = db.execute("SELECT name FROM university_card WHERE detail_url = ?", (campus_path,)).fetchone()
        if row is None:
            return None
        name = row[0]
        return {"text": (f"{name} အတွက် လူတွေ့ဖြေဆိုရန် လိုမလို UniFit မှာ အတည်ပြုထားတဲ့ အချက်အလက် မရှိသေးပါ။" if my else
                         f"UniFit hasn’t verified whether an interview is required at {name}."),
                "language": language, "link": campus_path, "link_label": name}
    if campus == "mmu":
        text = ("MMU ဝင်ခွင့်အတွက် လူတွေ့စစ်ဆေးမှု ပါပါတယ်။ UniFit မှာ အတည်ပြုထားတဲ့ လူတွေ့ရက် မရှိသေးပါ။" if my else
                "Yes. Myanmar Maritime University (MMU) includes an interview in its admissions process. UniFit has no verified interview date.")
    else:
        name = CAMPUS_ALIASES[campus][0]
        text = (f"{campus.upper()} အတွက် ၂၀၂၆ လမ်းညွှန်မှာ လူတွေ့ဖြေဆိုရန် မဖော်ပြထားပါ။ UniFit မှာ သီးခြားလိုအပ်ချက်ကို အတည်မပြုနိုင်သေးပါ။" if my else
                f"The 2026 guide does not list an interview for {name} ({campus.upper()}). UniFit hasn’t verified a separate interview requirement.")
    pages = INTERVIEW_GUIDE_PAGES[campus]
    result = {"text": text, "language": language, "pages": pages, "link": CAMPUS_ALIASES[campus][2],
              "link_label": campus.upper() + " university details"}
    if campus == "mmu":
        result["sources"] = [{"label": "MMU admissions notice", "url": "https://www.mmu.edu.mm/News.aspx?NewsID=347"}]
    return result


def campus_name_answer(question, language):
    query = question.strip(" ?။.!“”").casefold()
    if language == "auto":
        language = "my" if re.search(r"[\u1000-\u109f]", query) else "en"
    group = re.fullmatch(r"(?:(?:what|how) about |and )?(pu|cu|tu|yueco)(?: ?ကရော)?", query)
    if group:
        abbreviation = group[1].upper()
        if abbreviation == "YUECO":
            text = ("YUECO အတွက် လှိုင်ကျောင်းဝင်းလား၊ ရွာသာကြီးကျောင်းဝင်းလား။" if language == "my" else
                    "Which Yangon University of Economics campus do you mean, Hlaing or Ywa Tha Gyi?")
        else:
            text = (f"{abbreviation} ဆိုတာ ဘယ်မြို့က တက္ကသိုလ်ကို ဆိုလိုတာလဲ။" if language == "my" else
                    f"Which campus do you mean by {abbreviation}? Please tell me the city or university name.")
        return {"text": text, "language": language}
    if query not in CAMPUS_SHORT_NAMES:
        return None
    path = next(iter(campus_short_paths(query)))
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute("SELECT name FROM university_card WHERE detail_url = ?", (path,)).fetchone()
    if row is None:
        return None
    name = row[0]
    text = (f"{name} အကြောင်း ဘာသိချင်ပါသလဲ။" if language == "my" else f"What would you like to know about {name}?")
    return {"text": text, "language": language, "link": path, "link_label": name}


ADMITTED_MARKS = re.compile(r"admitted (?:scores?|marks?)|ဝင်ခွင့်ရသူ.*အမှတ်|ဝင်ခွင့်ရမှတ်", re.I)
BURMESE_DIGITS = str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")
BETTER = re.compile(r"\bbetter\b|ဘယ်ဟာပိုကောင်း|ဘယ်.*ပိုကောင်း", re.I)


def data_quick_answer(question, language, history):
    prior_questions = [turn["text"] for turn in reversed(history) if turn["user"]]
    if language == "auto":
        language = "my" if re.search(r"[\u1000-\u109f]", question) else "en"
    my = language == "my"
    paths = campus_short_paths(question)
    if len(paths) == 2 and BETTER.search(question):
        with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
            campuses = db.execute(
                "SELECT name, detail_url FROM university_card WHERE detail_url IN (?, ?) ORDER BY name", tuple(paths)
            ).fetchall()
        if len(campuses) == 2:
            return {
                "text": ("ဘယ်အချက်ကို အဓိကထားပြီး နှိုင်းယှဉ်ချင်ပါသလဲ။ ဥပမာ သင်ချင်တဲ့ မေဂျာ၊ ကျောင်းတည်နေရာ၊ ဒါမှမဟုတ် ဝင်ခွင့်လိုအပ်ချက်တွေပါ။"
                         if my else "What matters most to you about these two universities? For example, a major you want to study, their location, or their entry requirements."),
                "language": language,
                "links": [{"url": path, "label": name} for name, path in campuses],
            }
    if not paths and prior_questions and BETTER.search(prior_questions[0]):
        comparison_paths = campus_short_paths(prior_questions[0])
        if len(comparison_paths) == 2:
            paths = comparison_paths
            if re.search(r"\blocation\b|where .*located|တည်နေရာ|ဘယ်မှာ", question, re.I):
                with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
                    campuses = db.execute(
                        "SELECT name, address, detail_url FROM university_card WHERE detail_url IN (?, ?) ORDER BY name",
                        tuple(paths),
                    ).fetchall()
                if campuses:
                    return {"text": "\n\n".join(f"{name}: {address}" for name, address, _ in campuses),
                            "language": language,
                            "links": [{"url": path, "label": name} for name, _, path in campuses]}
    years = set(re.findall(r"(?<!\d)20\d{2}(?!\d)", question.translate(BURMESE_DIGITS)))
    score_followup = re.search(r"what about|ကရော", question, re.I) and any(
        ADMITTED_MARKS.search(turn) for turn in prior_questions[:2]
    )
    if years and (ADMITTED_MARKS.search(question) or score_followup):
        if not paths:
            paths = next((matched for turn in prior_questions if (matched := campus_short_paths(turn))), set())
        if len(paths) == 1 and len(years) == 1:
            with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
                row = db.execute("SELECT id FROM university_card WHERE detail_url = ?", (next(iter(paths)),)).fetchone()
            if row:
                return historical_answer(DATABASE, row[0], int(next(iter(years))), language)
    language_campuses = {f"universities/{CAMPUS_SHORT_NAMES[alias]}.html" for alias in ("yufl", "mufl")}
    requested_major = next((major for major, pattern in (
        ("Chinese", r"\bchinese\b|တရုတ်"), ("Japanese", r"\bjapanese\b|ဂျပန်")
    ) if re.search(pattern, question, re.I)), None)
    if not paths and requested_major:
        paths = next((matched for turn in prior_questions[:3]
                      if (matched := campus_short_paths(turn))), set())
    if not language_campuses <= paths or not (requested_major or re.search(r"languages?|ဘာသာစကား", question, re.I)):
        return None
    names = ("Yangon University of Foreign Languages", "Mandalay University of Foreign Languages")
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as db:
        programmes = [
            {row[0].removeprefix("B.A. (").removesuffix(")") for row in db.execute(
                "SELECT program FROM admission_2026_review WHERE university = ? AND review_status LIKE 'published%'", (name,)
            )}
            for name in names
        ]
        descriptions = db.execute(
            "SELECT count(DISTINCT page_path) FROM detail_section WHERE title = ? AND page_path IN (?, ?)",
            (requested_major, *language_campuses),
        ).fetchone()[0]
    shared = sorted(programmes[0] & programmes[1])
    if not shared:
        return None
    translations = dict(zip(("Chinese", "English", "French", "German", "Japanese", "Korean", "Russian", "Thai"),
                            ("တရုတ်", "အင်္ဂလိပ်", "ပြင်သစ်", "ဂျာမန်", "ဂျပန်", "ကိုရီးယား", "ရုရှား", "ထိုင်း")))
    text = ("YUFL နဲ့ MUFL နှစ်ခုစလုံးမှာ " + "၊ ".join(translations.get(name, name) for name in shared) + " ဘာသာတွေ သင်လို့ရပါတယ်။"
            if my else "YUFL and MUFL both offer " + ", ".join(shared) + ".")
    if requested_major in shared and not re.search(r"languages?|ဘာသာစကား", question, re.I):
        text = (f"YUFL နဲ့ MUFL နှစ်ခုစလုံးမှာ {translations[requested_major]}ဘာသာ B.A. သင်တန်း ရှိပါတယ်။"
                if my else f"Both YUFL and MUFL offer a B.A. in {requested_major}.")
    if requested_major == "Chinese" and requested_major in shared and descriptions == 2:
        text += ("\n\nUniFit ရဲ့ တရုတ်ဘာသာ မိတ်ဆက်ချက်အရ နားထောင်၊ ပြော၊ ဖတ်၊ ရေး လေ့ကျင့်ပြီး တရုတ်စာပေနဲ့ ယဉ်ကျေးမှုကို လေ့လာရပါတယ်။ တက္ကသိုလ်အလိုက် သင်ရိုးအသေးစိတ်ကို အတည်မပြုရသေးပါ။"
                 if my else "\n\nUniFit’s major overview covers listening, speaking, reading, and writing, plus Chinese literature and culture. Campus-specific syllabi remain unverified.")
    if requested_major == "Japanese" and requested_major in shared and descriptions == 2:
        text += ("\n\nUniFit ရဲ့ ဂျပန်ဘာသာ မိတ်ဆက်ချက်အရ ဟိရဂန၊ ခတခန၊ ခန်းဂျီး၊ သဒ္ဒါ၊ အသံထွက်၊ စာပေနဲ့ ယဉ်ကျေးမှုတို့ကို လေ့လာရပါတယ်။ တက္ကသိုလ်အလိုက် တရားဝင် သင်ရိုးအသေးစိတ်ကို အတည်မပြုရသေးပါ။" if my else
                 "\n\nUniFit’s Japanese major overview covers hiragana, katakana, kanji, grammar, pronunciation, literature and culture. Campus-specific syllabi remain unverified.")
    return {"text": text, "language": language, "pages": [70, 71, 72],
            "links": [{"url": f"universities/{CAMPUS_SHORT_NAMES[alias]}.html", "label": alias.upper()}
                      for alias in ("yufl", "mufl")]}


class ChatHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32768:
                raise ValueError
            request = json.loads(self.rfile.read(size))
            question = request["question"]
            language = request.get("language", "auto")
            if not isinstance(question, str) or not 0 < len(question.strip()) <= 500:
                raise ValueError
            if language not in ("auto", "my", "en"):
                raise ValueError
            page = request.get("page", "")
            turns = request.get("history", [])
            if not isinstance(page, str) or len(page) > 300 or not isinstance(turns, list):
                raise ValueError
            history = [
                {"text": turn["text"][:600], "user": turn.get("user") is True}
                for turn in turns[-6:]
                if isinstance(turn, dict) and isinstance(turn.get("text"), str)
            ]
        except (AttributeError, KeyError, TypeError, ValueError):
            self.send_error(400)
            return
        try:
            result = campus_interview_answer(question, language, page, history)
            if result is None:
                result = data_quick_answer(question, language, history)
            if result is None:
                result = campus_name_answer(question, language)
            if result is None:
                result = application_quick_answer(question, language)
            eligibility_search = re.search(r"\b(?:eligible|qualify)\b|where can i apply|which universit.*(?:my marks|my scores)|ဘယ်တက္ကသိုလ်.*လျှောက်", question, re.I)
            distance_guide = re.search(r"\bdistance education\b|အဝေးသင်", guide_query(question))
            if result is None and (not eligibility_search or distance_guide):
                result = local_lookup(DATABASE, question, language, page, history)
            if result is None:
                if os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"):
                    result = model_answer(DATABASE, question.strip(), language, page, history)
                else:
                    result = answer(question.strip(), language, request.get("previous"))
        except (HTTPError, TimeoutError) as error:
            status = error.code if isinstance(error, HTTPError) else 504
            self.log_error("Hosted model request returned HTTP %s or timed out", status)
            if status not in (429, 503, 504):
                self.send_error(503)
                return
            result = answer(question.strip(), language, request.get("previous"))
        except (sqlite3.Error, OSError, ValueError, KeyError, TypeError) as error:
            self.log_error("Chat request failed (%s)", type(error).__name__)
            self.send_error(503)
            return
        payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class PreviewHandler(ChatHandler, SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_head(self):
        path = Path(self.translate_path(self.path)).resolve()
        relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else None
        if relative is None or (relative.parts and relative.parts[0] not in {"assets", "data", "universities"}
                                and (len(relative.parts) != 1 or path.suffix != ".html")):
            self.send_error(404)
            return None
        if path.is_dir() and relative.parts:
            self.send_error(404)
            return None
        return super().send_head()


def load_local_config():
    config = ROOT / ".env"
    if not config.is_file():
        return
    allowed = {"GEMINI_API_KEY", "UNIFIT_GEMINI_MODEL", "OPENAI_API_KEY", "UNIFIT_OPENAI_MODEL"}
    for line in config.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if separator and key in allowed and value:
            if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
                value = value[1:-1]
            os.environ[key] = value


def main():
    load_local_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8083)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), PreviewHandler) as server:
        print(f"UniFit chat preview at http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
