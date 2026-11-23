"""Import visually checked 2026 guide summaries and facts into UniFit."""

from contextlib import closing
from pathlib import Path
import sqlite3


DATABASE = Path(__file__).with_name("unifit.sqlite")
EDITION = 2026
SOURCE = "2026-university-admissions-guide.pdf"

PAGES = (
    (23, 9, "Medical university admissions",
     "ဆေးတက္ကသိုလ်များအတွက် STEAMS-1 ဖြင့် အောင်မြင်ပြီး ခြောက်ဘာသာစုစုပေါင်း ၄၅၀ နှင့်အထက် ရရှိရမည်။ "
     "အင်္ဂလိပ်စာ၊ ဓာတုဗေဒနှင့် ဇီဝဗေဒ သုံးဘာသာပေါင်းရမှတ်ဖြင့် ပဏာမရွေးချယ်ပြီး "
     "ပဏာမရွေးချယ်ခံရသူများ လူတွေ့/နှုတ်မေးစာမေးပွဲ ဖြေဆိုရမည်။"),
    (123, 54, "Application forms and accompanying records",
     "တက္ကသိုလ်ဝင်ခွင့် လျှောက်လွှာအစုံကို မိမိဖြေဆိုခဲ့သည့် စာစစ်ဌာနကြီးကြပ်ရေးမှူး "
     "(အထက်တန်းကျောင်းအုပ်ကြီး) ထံမှ တစ်စုံလျှင် ၁၅၀၀ ကျပ်ဖြင့် ရယူနိုင်သည်။ "
     "အစုံတွင် မှတ်ပုံတင်ခွင့်လျှောက်လွှာ နှစ်စောင်၊ ဝင်ခွင့်လျှောက်လွှာ၊ သင်တန်းရွေးချယ်မှုကတ်ပြား၊ "
     "လမ်းညွှန်စာအုပ်နှင့် စာအိတ် ပါဝင်သည်။ လျှောက်လွှာနှင့်အတူ ပေးပို့ရမည့် အမှတ်စာရင်းနှင့် "
     "အရည်အချင်းမှတ်တမ်းချုပ် ရမှတ်အဆင့်ကို စာစစ်ဌာနကြီးကြပ်ရေးမှူးက အခမဲ့ ထုတ်ပေးမည်။"),
    (124, 55, "Ordering university and programme preferences",
     "မိမိဖြေဆိုခဲ့သည့် ဘာသာတွဲအလိုက် တက်ရောက်လိုသည့် တက္ကသိုလ်နှင့် အထူးပြုဘာသာရပ်များကို "
     "နှစ်သက်ရာ ဦးစားပေးအစီအစဉ်အတိုင်း လျှောက်လွှာတွင် ဖြည့်သွင်းရမည်။ "
     "ဦးစားပေးစာရင်းတွင် မဖော်ပြထားသည့် တက္ကသိုလ်နှင့် ဘာသာရပ်များကို စဉ်းစားမည်မဟုတ်ပါ။ "
     "စာမျက်နှာပါ STEAMS-1 စာရင်းသည် ဦးစားပေးစာရင်းဖြည့်ရန် ဥပမာဖြစ်သည်။"),
    (128, 59, "Completing and submitting the application",
     "လျှောက်လွှာများနှင့် သင်တန်းရွေးချယ်မှုကတ်ပြားကို ပြည့်စုံရှင်းလင်းစွာ ဖြည့်ပါ။ "
     "အကြောင်းပြန်ကြားစာတွင် ဆက်သွယ်နိုင်မည့် လိပ်စာနှင့် ဖုန်းနံပါတ်ကို ရေးပါ။ "
     "နိုင်ငံပိုင်သတင်းစာများတွင် ကြေညာသည့် သတ်မှတ်ရက်အတွင်း တင်သွင်းပါ။"),
    (129, 60, "Late applications",
     "သာမန်လျှောက်လွှာ သတ်မှတ်ရက်ကျော်ပါက ရန်ကုန်၊ ကမာရွတ်၊ သထုံလမ်းရှိ အဆင့်မြင့်ပညာဦးစီးဌာနသို့ ပေးပို့ရမည်။ "
     "လက်ခံနိုင်သည့် နေရာပေါ် မူတည်သည်။ ဆေးနှင့် သွားဘက်ဆိုင်ရာ တက္ကသိုလ်များကို ပထမဦးစားပေးလျှောက်လျှင် နောက်ကျလျှောက်လွှာကို လက်မခံပါ။"),
    (130, 61, "Documents to submit in the application envelope",
     "သင်တန်းရွေးချယ်မှုကတ်၊ မှတ်ပုံတင်ခွင့်လျှောက်လွှာ နှစ်စောင်၊ ဝင်ခွင့်လျှောက်လွှာ၊ "
     "တက္ကသိုလ်ဝင်စာမေးပွဲ အမှတ်စာရင်းမူရင်းနှင့် ကျောင်းအုပ်ကြီးထုတ်ပေးသည့် အရည်အချင်းမှတ်တမ်းချုပ် ရမှတ်အဆင့်ကို ပေးထားသောစာအိတ်ထဲ ထည့်သွင်းပါ။"),
    (131, 62, "Interview and competitive selection",
     "ဆေးနှင့် သွားဘက်ဆိုင်ရာ တက္ကသိုလ်များတွင် လူတွေ့ သို့မဟုတ် နှုတ်မေးစာမေးပွဲဖြင့် ရွေးချယ်သည်။ "
     "ဆေးဝါး၊ ဆေးဘက်ဆိုင်ရာနည်းပညာ၊ သူနာပြုနှင့် အခြေခံကျန်းမာရေး တက္ကသိုလ်များတွင် "
     "ခြောက်ဘာသာစုစုပေါင်းရမှတ်ဖြင့် ယှဉ်ပြိုင်ရွေးချယ်သည်။"),
    (133, 64, "How ranked preferences are processed",
     "သင်တန်းရွေးချယ်မှုကတ်ပြားပါ ဦးစားပေးအစီအစဉ်အတိုင်း စိစစ်သည်။ "
     "နေရာပြည့်ပါက နောက်ဦးစားပေးကို စဉ်းစားပြီး ဝင်ခွင့်ရပြီးပါက အောက်ဦးစားပေးများကို မစဉ်းစားပါ။"),
    (147, 77, "Day-programme exams and attendance",
     "ပညာရေးဝန်ကြီးဌာနအောက်ရှိ နေ့သင်တန်းများတွင် နှစ်ဝက်တစ်ခုစီအပြီး စာမေးပွဲ ကျင်းပသည်။ "
     "နှစ်ဝက်နှစ်ခု စုစုပေါင်း ကျောင်းခေါ်ချိန် ၇၅% မပြည့်ပါက ဒုတိယနှစ်ဝက်စာမေးပွဲ ဖြေခွင့်မရဘဲ 1F အဖြစ် သတ်မှတ်သည်။ "
     "ခိုင်လုံသော ဆေးလက်မှတ်ဖြင့် ပညာသင်နှစ်တစ်နှစ်လုံးအတွက် ခွင့်ရက် ၂၁ ရက်အထိ ခွင့်ပြုနိုင်သည်။"),
    (149, 78, "First-year Ministry of Education enrollment fees",
     "ပညာရေးဝန်ကြီးဌာနရှိ တက္ကသိုလ်၊ ဒီဂရီကောလိပ်နှင့် ကောလိပ်များ၏ ပထမနှစ်အတွက် "
     "မှတ်ပုံတင်ကြေး ၂၀၀၀ ကျပ်၊ ကျောင်းဝင်ကြေး ၂၀၀၀ ကျပ်၊ ကျောင်းလခ တစ်လ ၅၀၀၀ ကျပ် "
     "(တစ်နှစ် ၆၀၀၀၀ ကျပ်) နှင့် အားကစားကြေး ၂၀၀၀ ကျပ် ဖြစ်သည်။ လက်တွေ့ရှိသော သိပ္ပံဘာသာရပ်များအတွက် "
     "ဓာတ်ခွဲခန်းကြေး ၆၀၀၀ ကျပ်၊ လက်တွေ့ရှိသော ဝိဇ္ဇာဘာသာရပ်များအတွက် ၃၀၀၀ ကျပ် ဖြစ်သည်။ "
     "စာမေးပွဲကြေးနှင့် စာကြည့်တိုက်ကြေး တစ်မျိုးလျှင် ၅၀၀၀ ကျပ် ဖြစ်သည်။ "
     "လမ်းညွှန်တွင် ကျောင်းအပ်ခြင်းနှင့် ပေးသွင်းခြင်းအတွက် sms.moe.gov.mm နှင့် Myanmar Pay (MMQR) ကို ဖော်ပြထားသည်။"),
    (153, 80, "Distance education entry requirement",
     "ဤလမ်းညွှန်ပါ အဝေးသင်ဝင်ခွင့်အတွက် ၂၀၂၆ ခုနှစ် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်ထားရမည်။"),
    (155, 81, "First-year distance education majors",
     "အဝေးသင် ပထမနှစ်တွင် မြန်မာစာ၊ အင်္ဂလိပ်စာ၊ ပထဝီဝင်၊ သမိုင်း၊ ဒဿနိကဗေဒ၊ စိတ်ပညာ၊ အရှေ့တိုင်းပညာ၊ "
     "ဥပဒေပညာ (B.A. Law)၊ စီးပွားရေးပညာ၊ စီးပွားစီမံပညာ၊ ဓာတုဗေဒ၊ ရူပဗေဒ၊ သင်္ချာ၊ သတ္တဗေဒနှင့် ရုက္ခဗေဒတို့ကို လမ်းညွှန်တွင် ဖော်ပြထားသည်။"),
    (179, 95, "Distance education enrollment and first-year fees",
     "အဝေးသင် ပထမနှစ်အတွက် မှတ်ပုံတင်ကြေး ၂၀၀၀ ကျပ်၊ ကျောင်းဝင်ကြေး ၂၀၀၀ ကျပ်၊ သင်တန်းကြေး တစ်နှစ် ၂၀၀၀၀ ကျပ်၊ "
     "သိပ္ပံဘာသာ ဓာတ်ခွဲခန်းကြေး ၄၀၀၀ ကျပ်နှင့် စာမေးပွဲကြေး ၃၀၀၀ ကျပ် ဖြစ်သည်။ စာအုပ်နှင့် သင်ကြားရေးပစ္စည်းများအတွက် သတ်မှတ်ကြေး သီးခြားရှိသည်။ "
     "သတ်မှတ်ရက်အတွင်း sms.moe.gov.mm မှ Myanmar Pay (MMQR) ဖြင့် ပေးသွင်းနိုင်သည်။"),
    (181, 96, "Distance education exams",
     "အဝေးသင် အတန်းတင်စာမေးပွဲကို တစ်နှစ်တစ်ကြိမ် ကျင်းပသည်။ နောက်ဆက်တွဲနှင့် အရစ်ကျစာမေးပွဲ မရှိပါ။ "
     "ဖြေဆိုရန် ဝင်ခွင့်ရထားရမည်၊ သိပ္ပံလက်တွေ့သင်တန်း ၇၅% တက်ရောက်ရမည် (သိပ္ပံဘာသာတွဲအတွက်)၊ "
     "သတ်မှတ်အလုပ်များ ဖြေဆိုပြီး သင်တန်းကြေးပေးဆောင်ကာ စာမေးပွဲလျှောက်လွှာကို အချိန်မီတင်ရမည်။"),
    (183, 97, "Distance education transfers and withdrawal",
     "အဝေးသင် ဘာသာပြောင်း၊ ကျောင်းပြောင်းရန် ဝင်ခွင့်ရထားသော တက္ကသိုလ်၏ အဝေးသင်ဌာနခွဲကို တိုက်ရိုက်ဆက်သွယ်ပါ။ "
     "ဆက်သွယ်ရန်လိပ်စာ ပြောင်းလဲပါက အမြန်ဆုံး အကြောင်းကြားပါ။ ကျောင်းဝင်မှတ်ပုံတင်ပြီးမှ စာမေးပွဲမတိုင်မီ နုတ်ထွက်ခွင့် လျှောက်ထားနိုင်သည်။"),
)

SECTIONS = (
    (23, "medicine-interview", "interview", "medical-university admissions",
     "Shortlisted applicants take an interview or oral examination. Page 23 gives no interview date.",
     "လူတွေ့ နှုတ်မေး ဆေးတက္ကသိုလ် STEAMS-1"),
    (123, "application-documents", "documents", "general university application",
     "The packet includes two registration application forms, the admission application, a preference card, "
     "the guide and an envelope. The exam-centre supervisor issues the accompanying exam records free of charge.",
     "စာရွက်စာတမ်း လျှောက်လွှာ အမှတ်စာရင်း စာစစ်ဌာန"),
    (124, "preference-order", "application", "general university application",
     "List desired institutions and majors in order of preference. Only listed choices are considered. "
     "The STEAMS-1 list illustrates how to complete the form.",
     "ဦးစားပေး သင်တန်းရွေးချယ်မှု မေဂျာ"),
    (128, "application-submission", "application", "general university application",
     "Complete the registration form, preference card and admission form. Give a reachable address and telephone number "
     "on the reply form. Submit to the designated receiving institution within the period announced in state newspapers.",
     "လျှောက်လွှာတင်သွင်းရန် လိပ်စာ ဖုန်းနံပါတ် သတ်မှတ်ရက်"),
    (129, "late-application", "late application deadline", "general university application medicine dentistry",
     "For a late general application, send it to the Department of Higher Education on Thaton Road, Kamayut, Yangon. "
     "Admission depends on whether the university can accommodate the applicant. First-choice medicine and dentistry applications received after the deadline are not accepted.",
     "နောက်ကျလျှောက်လွှာ သတ်မှတ်ရက်ကျော် ဆေးတက္ကသိုလ် သွားဘက်"),
    (130, "application-originals", "original marksheet documents envelope", "submission documents",
     "Submit the preference card, two registration forms, the admission application, the original matriculation marks sheet, "
     "and the academic record grade issued by the school principal in the supplied envelope.",
     "အမှတ်စာရင်းမူရင်း စာအိတ် စာရွက်စာတမ်းတင်သွင်း"),
    (131, "dentistry-interview", "interview", "medicine and dentistry",
     "Medicine and dentistry use a qualifying interview or oral examination. Page 131 does not give an interview date.",
     "ဆေး သွားဘက်ဆိုင်ရာ လူတွေ့ နှုတ်မေး"),
    (131, "allied-health-score", "selection", "pharmacy, medical technology, nursing and community health",
     "Selection is competitive and based on the total matriculation marks across six subjects.",
     "ဆေးဝါး ဆေးဘက်ဆိုင်ရာနည်းပညာ သူနာပြု အခြေခံကျန်းမာရေး ခြောက်ဘာသာ"),
    (133, "preference-selection", "selection", "general university application",
     "If a choice is full, the next ranked choice is considered. Once an applicant is placed, lower-ranked choices "
     "are no longer considered. The committee only considers choices listed on the preference card.",
     "ဦးစားပေး နေရာပြည့် သင်တန်းရွေးချယ်မှု"),
    (147, "day-exams", "day programme exams attendance medical leave", "Ministry of Education universities and degree colleges",
     "An exam is held after each semester. Students below 75% combined attendance across both semesters cannot sit the second-semester exam and are marked 1F for the year. "
     "A valid medical certificate can support up to 21 days of leave for the academic year. Other ministries' institutions follow their own published rules.",
     "ကျောင်းခေါ်ချိန် နေ့သင်တန်း နှစ်ဝက်စာမေးပွဲ ဆေးလက်မှတ် ခွင့်ရက်"),
    (149, "first-year-fees", "fees", "Ministry of Education universities, degree colleges and colleges",
     "The first-year schedule specifies tuition and separate fees, with different practical fees for science and arts.",
     "ကျောင်းလခ ကျောင်းအပ်ကြေး အခကြေးငွေ ဓာတ်ခွဲခန်း"),
    (153, "distance-entry", "distance education entry eligibility requirements matriculation", "distance learning admissions",
     "Entry to the distance education programmes covered in this section requires passing the 2026 matriculation exam.",
     "အဝေးသင် ဝင်ခွင့် ဝင်ခွင့်သတ်မှတ်ချက် တက္ကသိုလ်ဝင်စာမေးပွဲ အောင်မြင်"),
    (155, "distance-majors", "distance education first-year majors subjects programmes courses", "distance learning programme offerings",
     "The first-year distance education list includes Myanmar, English, Geography, History, Philosophy, Psychology, Oriental Studies, Law (B.A. Law), Economics, Business Management, Chemistry, Physics, Mathematics, Zoology, and Botany.",
     "အဝေးသင် မေဂျာ ဘာသာရပ် အထူးပြု ဥပဒေ သင်လို့"),
    (179, "distance-fees", "distance education tuition enrollment fees payment", "first-year distance learning",
     "First-year distance education fees are 2,000 MMK registration, 2,000 MMK admission, 20,000 MMK annual tuition, "
     "4,000 MMK for science laboratory work, and 3,000 MMK for exams. Study materials carry separate charges. "
     "Use the Ministry enrollment portal and Myanmar Pay (MMQR) by the deadline.",
     "အဝေးသင် ကျောင်းလခ သင်တန်းကြေး ကျောင်းအပ် ပေးသွင်း"),
    (181, "distance-exams", "distance education examination exams attendance assignments resit", "distance learning exam eligibility",
     "Distance education holds one promotion exam each academic year, with no supplementary or staggered exams. "
     "Students need admission, completed assignments, paid fees and an on-time exam application. Science students also need 75% practical attendance.",
     "အဝေးသင် စာမေးပွဲ လက်တွေ့ တက်ရောက် နောက်ဆက်တွဲ"),
    (183, "distance-student-services", "distance education transfer withdrawal address change", "distance learning student services",
     "Contact the distance education branch of the admitting university directly to request a major or campus transfer. "
     "Report a change of contact address promptly. After registration, submit a withdrawal request to that branch before the exam.",
     "အဝေးသင် ကျောင်းပြောင်း ဘာသာပြောင်း လိပ်စာပြောင်း နုတ်ထွက်"),
)

FACTS = (
    ("day-exams", "minimum_attendance", "Combined attendance to sit the second-semester exam", 75, "percent", "Across both semesters"),
    ("day-exams", "medical_leave", "Medical leave with a valid certificate", 21, "days", "Up to this amount per academic year"),
    ("distance-entry", "matriculation_year", "Required matriculation exam year", 2026, "year", "Applicants must have passed"),
    ("application-originals", "original_marksheet", "Original matriculation marks sheet", None, None, "Send with the application"),
    ("distance-fees", "registration", "Distance education registration fee", 2000, "MMK", "First year"),
    ("distance-fees", "admission", "Distance education admission fee", 2000, "MMK", "First year"),
    ("distance-fees", "annual_tuition", "Distance education tuition", 20000, "MMK", "Per year"),
    ("distance-fees", "science_lab", "Distance education science laboratory fee", 4000, "MMK", "Science subjects"),
    ("distance-fees", "exam", "Distance education exam fee", 3000, "MMK", "First year"),
    ("distance-exams", "frequency", "Promotion exams per academic year", 1, "exam", "Distance education"),
    ("distance-exams", "practical_attendance", "Science practical attendance", 75, "percent", "Distance education science courses"),
    ("application-documents", "application_packet", "Application packet", 1500, "MMK", "Per set from the exam-centre supervisor"),
    ("medicine-interview", "interview_required", "Interview or oral examination", None, None, "Required for shortlisted applicants"),
    ("dentistry-interview", "interview_selection", "Interview or oral examination", None, None, "Selection for medicine and dentistry"),
    ("allied-health-score", "subjects_counted", "Subjects counted for ranking", 6, "subjects", "Total for the four listed allied-health university types"),
    ("first-year-fees", "late_payment_request", "Additional period for a late payment request", 15, "days",
     "For unavoidable delay with a valid reason. The institution decides whether to allow late payment."),
    ("first-year-fees", "registration", "Registration fee", 2000, "MMK", "First year"),
    ("first-year-fees", "admission", "Admission fee", 2000, "MMK", "First year"),
    ("first-year-fees", "monthly_tuition", "Tuition", 5000, "MMK", "Per month"),
    ("first-year-fees", "annual_tuition", "Tuition", 60000, "MMK", "For one year"),
    ("first-year-fees", "sports", "Sports fee", 2000, "MMK", "First year"),
    ("first-year-fees", "science_practical", "Laboratory fee", 6000, "MMK", "Science subjects with practical work"),
    ("first-year-fees", "arts_practical", "Laboratory fee", 3000, "MMK", "Arts subjects with practical work"),
    ("first-year-fees", "exam", "Examination fee", 5000, "MMK", "First year"),
    ("first-year-fees", "library", "Library fee", 5000, "MMK", "First year"),
)

SCORES = (
    (20, 2024, "First-year intake", "Total marks", 479, 330, "https://hbtu.edu.mm/detail_news/145"),
    (59, 2025, "Computer Studies first-year intake", "Total marks", 418, 331, "https://ucsh.edu.mm/?p=7096"),
)

SCHEMA = """
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS guide_page (
    edition INTEGER NOT NULL,
    printed_page INTEGER NOT NULL CHECK (printed_page > 0),
    pdf_scan INTEGER NOT NULL CHECK (pdf_scan > 0),
    source_file TEXT NOT NULL,
    title TEXT NOT NULL,
    summary_my TEXT NOT NULL,
    PRIMARY KEY (edition, printed_page)
);
CREATE TABLE IF NOT EXISTS guide_section (
    edition INTEGER NOT NULL,
    section_key TEXT NOT NULL,
    printed_page INTEGER NOT NULL,
    topic TEXT NOT NULL,
    scope TEXT NOT NULL,
    summary_en TEXT NOT NULL,
    keywords_my TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    PRIMARY KEY (edition, section_key),
    FOREIGN KEY (edition, printed_page) REFERENCES guide_page (edition, printed_page)
);
CREATE INDEX IF NOT EXISTS guide_section_lookup ON guide_section (edition, topic, scope);
CREATE TABLE IF NOT EXISTS guide_fact (
    edition INTEGER NOT NULL,
    section_key TEXT NOT NULL,
    fact_key TEXT NOT NULL,
    label TEXT NOT NULL,
    amount INTEGER CHECK (amount >= 0),
    unit TEXT,
    conditions TEXT NOT NULL,
    PRIMARY KEY (edition, section_key, fact_key),
    FOREIGN KEY (edition, section_key) REFERENCES guide_section (edition, section_key)
);
CREATE TABLE IF NOT EXISTS historical_admitted_score (
    university_id INTEGER NOT NULL REFERENCES university_card (id),
    exam_cohort INTEGER NOT NULL,
    intake TEXT NOT NULL,
    score_basis TEXT NOT NULL,
    highest_score INTEGER CHECK (highest_score >= 0),
    lowest_score INTEGER CHECK (lowest_score >= 0),
    source_url TEXT NOT NULL,
    PRIMARY KEY (university_id, exam_cohort, intake, score_basis),
    CHECK (highest_score IS NOT NULL OR lowest_score IS NOT NULL),
    CHECK (highest_score >= lowest_score)
);
DROP VIEW IF EXISTS guide_verified_answers;
CREATE VIEW guide_verified_answers AS
SELECT s.edition, s.section_key, s.topic, s.scope, s.summary_en, s.keywords_my,
       p.summary_my, s.printed_page, p.pdf_scan, p.source_file,
       f.fact_key, f.label, f.amount, f.unit, f.conditions
FROM guide_section s
JOIN guide_page p ON p.edition = s.edition AND p.printed_page = s.printed_page
LEFT JOIN guide_fact f ON f.edition = s.edition AND f.section_key = s.section_key
WHERE s.verification_status = 'checked against scan';
"""


def main():
    with closing(sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=rw", uri=True)) as db, db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA)
        db.executemany(
            """INSERT INTO guide_page VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (edition, printed_page) DO UPDATE SET
                title = excluded.title, summary_my = excluded.summary_my
            WHERE guide_page.summary_my = ''""",
            [(EDITION, page, scan, SOURCE, title, summary) for page, scan, title, summary in PAGES],
        )
        db.executemany(
            "INSERT INTO guide_section VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [(EDITION, key, page, topic, scope, summary, keywords, "checked against scan")
             for page, key, topic, scope, summary, keywords in SECTIONS],
        )
        db.executemany(
            "INSERT INTO guide_fact VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            [(EDITION, *fact) for fact in FACTS],
        )
        db.executemany(
            "INSERT INTO historical_admitted_score VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            SCORES,
        )


if __name__ == "__main__":
    main()
