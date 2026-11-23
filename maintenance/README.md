# Maintaining UniFit

Open `maintenance/unifit.sqlite` with a SQLite connection in DBeaver. In the current DBeaver workspace, the connection named `unifit.sqlite 2` points to this file. Check the full path in the connection settings before editing. The 2026 admissions audit is in the neighboring `2026-guide` folder.

- `university_card` controls the University List cards in ID order.
- `legacy_admission` holds the baseline rows and original search rules. The exporter applies approved changes and adds published routes from `admission_2026_review`.
- `detail_section` holds the content shown inside each university accordion, including the Burmese descriptions and career paths. Edit `title` for the accordion heading and `content_html` for the body text. Profile pages render majors from this table at export/runtime.
- `section_image` controls image paths and alt text for the existing image slots in each section. Paths are relative to the detail page.
- `detail_page` maps the existing detail URLs to their browser data files. Each page retains its existing layout, headings and other page-specific markup.

Save and commit edits in DBeaver. From the UniFit folder, regenerate the browser files and preview the site:

```powershell
Set-Location -LiteralPath 'D:\UNIFit\unifit'
python maintenance/export-site.py
python maintenance/check-links.py
node maintenance/test_admission_rules.mjs
```

CI runs the same three commands on every push via `.github/workflows/site-checks.yml`.

To recompress raster assets (JPG/PNG → WebP when smaller, max edge 1600px):

```powershell
python maintenance/optimize_images.py
python maintenance/export-site.py
python maintenance/check-links.py
```


To preview from inside `unifit`, run `python -m http.server 8082 --bind 127.0.0.1` and open `http://127.0.0.1:8082/index.html`. The JavaScript files in `data/` are generated from SQLite. `data/admissions.js` stores a compact packed payload and expands it to `window.unifitAdmissions` in the browser. University profile URLs use kebab-case slugs; old spaced filenames remain as redirect stubs.

## Verify the migration

Run `python maintenance/check-links.py` from the UniFit folder after exporting. It checks local HTML and CSS references, search result links, card links and images, and detail image paths. It reports missing files, filename case mismatches, and links to empty pages.

Run these queries in the SQLite connection:

```sql
PRAGMA integrity_check;
PRAGMA foreign_key_check;
SELECT COUNT(*) FROM university_card;
SELECT COUNT(*) FROM legacy_admission;
SELECT COUNT(*) FROM detail_page;
SELECT COUNT(*) FROM detail_section;
SELECT COUNT(*) FROM section_image;
```

As of 22 November 2026, these tables contain 158 baseline card rows, 802 baseline admissions rows, 166 detail-page records, 1,417 detail sections and 3,467 image references. The active export contains 155 cards and 850 search routes. The integrity check returns `ok` and the foreign-key check returns no rows.

- On University List, check that cards appear, test a category button, and open Yangon's or YTU's detail page.
- On YTU's page, expand Civil Engineering and check the Burmese description, career list and three images.
- On Search Your Uni, select STEAMS-1 and enter 80 in all six subjects. The total should be 480. Use **More Details** to open the matching campus under `universities/` and jump to the shared admissions box or the relevant programme rules. Both the links and the Burmese requirements come from the same SQLite export.
- The project root contains the main pages. University profiles are under `universities/`, stylesheets under `assets/css/`, images under `assets/images/`, and generated browser data under `data/`.

The source snapshot is `UniFit-before-cleanup.zip` one directory above this project. Some source pages already referenced missing assets or detail files. Abbreviation search also had a JavaScript error in the baseline.

## 2026 admissions

Open `maintenance/unifit.sqlite` in DBeaver. Browse `admission_2026_review` for the printed guide page, score conditions, Burmese wording and publication status of each reviewed route. It links existing routes to `legacy_admission` through `legacy_id`. New routes have their own review keys. Approved changes are exported by `maintenance/export-site.py`; refresh the preview after exporting.

The current export contains 155 University List cards and 850 Search Your Uni routes. Thaton's 2026 intake is unverified and its search route is withheld. The campus tracker and implementation checklist in the adjacent `2026-guide` folder list the outstanding source checks.

### Find a record in DBeaver

Open a SQL editor on the active connection. These read-only examples show the schema, the YTU card, its major sections and its current admissions rule:

```sql
SELECT name, sql
FROM sqlite_schema
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;

SELECT id, name, detail_url
FROM university_card
WHERE detail_url = 'universities/YTU.html';

SELECT position, title
FROM detail_section
WHERE page_path = 'universities/YTU.html'
ORDER BY position;

SELECT review_key, university, program, printed_pages,
       minimum_total, minimum_combined, combined_subjects,
       stream_status, region_rule, review_status, burmese_requirements_html
FROM admission_2026_review
WHERE university = 'Yangon Technological University';
```

YTU's card is ID 17. Its admissions row is `legacy:690` and cites printed pages 38–41. The current rule has a combined minimum of 300 and a blank total minimum.

### Apply the next approved update

1. Commit or roll back any existing DBeaver edits. Disconnect before making a dated copy of `maintenance/unifit.sqlite`, then reconnect to the active file.
2. Find the exact campus, programme and review key. Record the printed guide page or official notice in the 2026 review notes. For admissions, review the structured score, stream and region fields alongside the full Burmese text. The exporter uses the route's publication status to decide which fields and rules apply.
3. Save the verified change in the corresponding SQLite record. For detail text, use `detail_section.content_html`. For an existing image slot, use `section_image.image_path` and keep the image under `assets/images/`. Paths in university detail sections start with `../assets/images/` because those pages live under `universities/`. Commit the edit before exporting.
4. Run the integrity queries, export and link audit above. Refresh the preview and check the specific university in University List, Search Your Uni and its detail page. For a score rule change, try a score immediately below and at the minimum, plus any applicable stream or regional case.

The active SQLite file already contains the imported data and review records. The scripts in `maintenance/migrations/` document past batch updates and assume the folder layout that existed when they ran. Routine updates to an existing reviewed record use DBeaver and `export-site.py`.
## Local chat preview

Run `python maintenance/serve-chat.py --port 8084` from the UniFit checkout and open
`http://127.0.0.1:8084/requirement.html`.

The preview uses reviewed SQLite answers by default. For hosted model replies, configure
`GEMINI_API_KEY` in the server environment and restart the preview to use Gemini.
For local development, place `GEMINI_API_KEY=your-key` in the ignored `.env` file
at the checkout root. The server reads it at startup. Values in that file override
the same settings in the terminal. Gemini takes precedence when both keys are present.
`UNIFIT_GEMINI_MODEL` overrides
the default `gemini-3.8-flash`. The server sends the question, recent conversation,
and relevant reviewed records to Google in Gemini mode.

For OpenAI instead, configure
`OPENAI_API_KEY` in the environment of the server process and restart it. Keep the key
outside Git and the browser. Optionally set `UNIFIT_OPENAI_MODEL` to an accessible model
that supports Responses API structured outputs. The default is `gpt-4.1-mini`.
In hosted-model mode, the server sends the question, recent conversation and relevant
reviewed records to OpenAI. The API request disables response storage.

## Vercel deployment

Import the UniFit repository into Vercel with the repository root as the project root.
The checked-in configuration builds the public HTML and assets into `dist` and serves
`POST /api/chat` as a Python Function. The function reads the bundled SQLite database
in read-only mode. Keep the build command and output directory from `vercel.json`.

1. Create a Preview deployment. In the Vercel project environment variables, add
   `GEMINI_API_KEY` for Preview as a sensitive variable. Set `UNIFIT_GEMINI_MODEL` only
   if you need to override the default. Enter the key directly in Vercel and redeploy.
2. In Preview, check a reviewed lookup such as “What does page 149 say?” and a
   conversational question that reaches Gemini. Check the function logs for any
   provider errors. A local lookup reply can succeed without a configured Gemini key.
3. Verify that the preview returns 404 for `/.env` and `/maintenance/unifit.sqlite`.
   Before sharing the public URL, configure a POST rate limit for `/api/chat` using
   the Vercel project's firewall and check the Gemini project's usage limits.
4. Add the key to the Production environment and deploy after Preview checks pass.
