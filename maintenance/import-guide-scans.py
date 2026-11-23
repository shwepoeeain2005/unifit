"""Import local OCR results and page coverage for the supplied 2026 guide."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3


DATABASE = Path(__file__).with_name("unifit.sqlite")
PDF = "2026-university-admissions-guide.pdf"

SINGLE_FOLIOS = {
    3: 1, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 23,
    38: 77, 39: 78, 40: 95, 41: 96, 42: 97,
    **{scan: scan + 60 for scan in range(43, 54)},
    **{scan: scan + 69 for scan in range(54, 65)},
    **{scan: scan + 70 for scan in range(65, 78)},
    78: 149, 79: 151, 80: 153, 81: 155, 82: 157, 83: 158, 84: 159,
    85: 167, 86: 169,
    **{scan: scan + 83 for scan in range(87, 95)},
    95: 179, 96: 181, 97: 183,
    **{scan: scan + 91 for scan in range(98, 109)},
    **{scan: scan + 92 for scan in range(109, 119)},
    119: 213, 120: 214, 121: 216, 122: 217,
}
INFERRED_FOLIOS = {39, 41, 46, 87, 90, 98, 107}

TOPICS = (
    (1, 3, "Front matter and general eligibility"),
    (4, 8, "Day-programme institution roster"),
    (9, 37, "Day-programme admission criteria"),
    (38, 39, "Direct-application institutions"),
    (40, 42, "Myanmar Maritime University"),
    (43, 47, "Designated regions"),
    (48, 53, "Institution and intake tables"),
    (54, 64, "Application, preferences and selection"),
    (65, 68, "Placement and study guidance"),
    (69, 76, "Degree and duration tables"),
    (77, 77, "Examinations"),
    (78, 78, "First-year enrollment and fees"),
    (79, 79, "Honours and programme conditions"),
    (80, 97, "Distance education"),
    (98, 107, "GCE A Level and IB requirements"),
    (108, 118, "Vocational and alternate entry pathways"),
    (119, 122, "Examination and student conduct appendices"),
)

SCHEMA = """
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS guide_source_text (
    edition INTEGER NOT NULL,
    source_file TEXT NOT NULL,
    source_position INTEGER NOT NULL CHECK (source_position > 0),
    scan_part INTEGER NOT NULL CHECK (scan_part IN (1, 2)),
    pdf_scan INTEGER CHECK (pdf_scan > 0),
    printed_page INTEGER CHECK (printed_page > 0),
    folio_status TEXT NOT NULL CHECK (folio_status IN ('printed', 'inferred', 'unnumbered')),
    topic TEXT NOT NULL,
    ocr_text TEXT NOT NULL,
    ocr_confidence REAL NOT NULL CHECK (ocr_confidence BETWEEN 0 AND 100),
    PRIMARY KEY (edition, source_file, source_position, scan_part)
);
CREATE INDEX IF NOT EXISTS guide_source_folio ON guide_source_text (edition, printed_page);
CREATE INDEX IF NOT EXISTS guide_source_topic ON guide_source_text (edition, topic);
CREATE VIEW IF NOT EXISTS guide_page_coverage AS
WITH RECURSIVE folios(printed_page) AS (
    SELECT 1 UNION ALL SELECT printed_page + 1 FROM folios WHERE printed_page < 217
)
SELECT 2026 AS edition, f.printed_page,
       CASE WHEN COUNT(s.printed_page) = 0 THEN 'not in supplied files'
            WHEN MAX(s.folio_status = 'printed') = 0 THEN 'folio inferred'
            ELSE 'source available' END AS coverage,
       GROUP_CONCAT(CASE WHEN s.pdf_scan IS NOT NULL THEN 'PDF scan ' || s.pdf_scan
                         ELSE s.source_file END, '; ') AS locations
FROM folios f LEFT JOIN guide_source_text s
ON s.edition = 2026 AND s.printed_page = f.printed_page
GROUP BY f.printed_page;
CREATE VIEW IF NOT EXISTS guide_page_lookup AS
SELECT s.edition, s.printed_page, s.source_file, s.pdf_scan, s.scan_part,
       s.folio_status, s.topic, s.ocr_confidence,
       NULLIF(p.summary_my, '') AS reviewed_summary_my,
       s.ocr_text AS draft_ocr_text
FROM guide_source_text s LEFT JOIN guide_page p
ON p.edition = s.edition AND p.printed_page = s.printed_page;
"""


def source_plan():
    for scan in range(1, 123):
        topic = next(label for first, last, label in TOPICS if first <= scan <= last)
        folios = (2 * scan + 4, 2 * scan + 5) if 10 <= scan <= 37 else (SINGLE_FOLIOS.get(scan),)
        for part, folio in enumerate(folios, 1):
            status = "unnumbered" if folio is None else "inferred" if scan in INFERRED_FOLIOS else "printed"
            yield f"{scan:03}-{part}", PDF, scan, part, scan, folio, status, topic
    for folio in range(8, 22):
        yield (
            f"photo-{folio:03}", f"printed-page-{folio:03}.jpg", 1, 1, None, folio,
            "printed", "Campus and programme offering tables",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ocr_directory", type=Path)
    args = parser.parse_args()
    records = []
    for key, *source in source_plan():
        data = json.loads((args.ocr_directory / f"{key}.json").read_text(encoding="utf-8"))
        records.append((2026, *source, data["text"].strip(), data["confidence"]))

    with closing(sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=rw", uri=True)) as db, db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA)
        db.executemany(
            """INSERT INTO guide_source_text VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (edition, source_file, source_position, scan_part) DO UPDATE SET
                printed_page = excluded.printed_page, folio_status = excluded.folio_status,
                topic = excluded.topic, ocr_text = excluded.ocr_text,
                ocr_confidence = excluded.ocr_confidence""", records,
        )
        db.execute(
            """INSERT INTO guide_page (edition, printed_page, pdf_scan, source_file, title, summary_my)
            SELECT edition, printed_page, MIN(pdf_scan), source_file, topic, ''
            FROM guide_source_text
            WHERE edition = 2026 AND printed_page IS NOT NULL AND pdf_scan IS NOT NULL
            GROUP BY edition, printed_page
            ON CONFLICT (edition, printed_page) DO NOTHING"""
        )


if __name__ == "__main__":
    main()
