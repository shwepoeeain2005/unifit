# UniFit

UniFit helps students in Myanmar explore universities and colleges, check published 2026 admission requirements, and decide where to apply.

## Explore UniFit

### Home

![UniFit homepage with search and university list shortcuts](docs/screenshots/home.jpg)

### University Lists

Browse campuses by category or search by name. You can search within a selected category, then open a university profile to see its majors, descriptions, images, and available website link. The profile has one admissions section for the university. Returning to the list takes you back to your previous filters and position.

![University Lists with campus cards and category filters](docs/screenshots/university-list.jpg)

### University profile

![University of Medicine 1 profile opened from University Lists](docs/screenshots/university-profile.jpg)

### Search Your Uni

Choose your matriculation subject set to reveal the marks fields. Enter your marks and select your exam centre to see programmes that match the published criteria. Use **More Details** to open the university's admissions section. A match is guidance for applying. Final admission decisions are made by the university.

The **Ask UniFit** panel on this page sends questions to the Node assistant API (`POST /api/assistant/chat`) with optional match context from your search.

Example search using STEAMS 1, 85 marks in each subject, and a Yangon exam centre.

![Search Your Uni form with STEAMS 1 selected, 85 entered for all six subjects, and Yangon selected as the exam centre](docs/screenshots/search-marks.jpg)

![Search Your Uni results showing a total of 510 marks and 100 programme matches](docs/screenshots/search-results.jpg)

### Saved universities

Save universities as you browse and revisit them from the saved-universities shortcut. UniFit stores the shortlist in your browser, so it stays on the device and browser you used to save it.

### Requirements

The [Requirements page](req1.html) explains the application process, including the forms and exam records students need to prepare.

![Requirements overview showing the admissions guidance and application sample cards](docs/screenshots/requirements-overview.jpg)

![Burmese application requirements page showing the first application step](docs/screenshots/requirements.jpg)

### UniFit Chat

Open the chat from the navigation icon and ask in Burmese or English. It opens alongside the page on desktop and fills the screen on mobile. Try questions like these:

- What documents do I need to apply?
- Compare computing entry requirements at UCSY, UCSM, and NSPU.
- အဝေးသင် သင်တန်းကြေး ဘယ်လောက်လဲ။

Chat can link to university profiles, the Requirements page, or Search Your Uni. When a question has a verified answer in UniFit's data, replies can cite the relevant guide pages. Historical admitted scores may be unavailable.

![UniFit Chat answering questions about exam records, interviews, and where to check eligibility](docs/screenshots/chat.jpg)

## How it works

### Admissions matching

The search page applies published criteria using the selected subject set, marks, and exam centre. Some routes use a total score, while others use specific subjects, score combinations, or regional conditions. Where a stream restriction is still unconfirmed, UniFit asks students to confirm it with the university.

### Chat answers

- **Navigation chat** — The browser sends questions to the Python endpoint at `/api/chat`. The server looks up reviewed records in SQLite and can use Gemini for questions that need a model response.
- **Ask UniFit (Search Your Uni)** — Uses the Node backend at `/api/assistant/chat` (OpenRouter). API keys stay on the server only.

## Tech stack

- **Frontend** — HTML, CSS, and JavaScript
- **Data** — SQLite and generated JSON files
- **Navigation chat** — Python (`api/chat.py`) and optional Gemini
- **Search assistant** — Node.js (`server/`) and OpenRouter
- **Deployment** — Netlify (static site) + Render (Node API); Vercel config remains for the Python chat path

## Repository layout

| Location | Contents |
| --- | --- |
| `universities/` | University profile pages |
| `assets/` | Stylesheets, JavaScript, and images |
| `data/` | Generated university, admissions, and profile data |
| `maintenance/` | SQLite database, exporter, link checker, and maintenance guide |
| `api/chat.py` | Vercel entry point for navigation chat |
| `vercel.json` | Vercel build and function configuration |
| `server/` | Node backend for the OpenRouter search assistant (`npm run start:api`) |

## Run locally

Open the repository folder in VS Code and run the command for the features you want to try.

### Website preview

```powershell
python -m http.server 8082 --bind 127.0.0.1
```

Keep the terminal open and visit [the website preview](http://127.0.0.1:8082/). The website uses the generated data included in the repo.

### Ask UniFit API (Search Your Uni)

Copy `.env.example` to `.env`. Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. In a second terminal:

```powershell
npm run start:api
```

The server listens on `http://127.0.0.1:3001` and exposes **`POST /api/assistant/chat`**. On localhost, Ask UniFit uses that URL automatically (no `UNIFIT_API_BASE` required).

### Chat preview

```powershell
python maintenance/serve-chat.py --port 8084
```

Visit [the chat preview](http://127.0.0.1:8084/) and click the chat icon. SQLite lookup works without a Gemini key. To enable Gemini, put `GEMINI_API_KEY` in the Git-ignored local `.env` file or set it in the server environment before starting the preview.

## Deploy on Netlify and Render

**Netlify** serves the public pages, assets, and generated site data from `dist/` (see `netlify.toml`). Both Render URLs are public origins. Store provider keys in the corresponding Render service settings.

| Netlify setting | Value |
| --- | --- |
| Build command | `node maintenance/netlify-build.mjs` or `npm run build:netlify` |
| Publish directory | `dist` |
| Build environment | `UNIFIT_API_BASE` = Node Render origin. `UNIFIT_CHAT_API_BASE` = Python Render HTTPS origin. |

**Ask UniFit** uses the Node Render service from the repository root.

| Render setting | Value |
| --- | --- |
| Build command | `npm install` |
| Start command | `npm run start:api` |
| Environment | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `CORS_ORIGINS` (your Netlify origin), `OPENROUTER_SITE_URL` |

Optional Gemini rollback: set `ENABLE_GEMINI_ROLLBACK_ROUTE=1` and `GEMINI_*` only when needed.

**UniFit Chat** in the navigation uses a second Render Web Service with the Python runtime. Keep its root at the repository root so the bundled SQLite database is available.

| Render setting | Value |
| --- | --- |
| Build command | `python -m compileall -q maintenance` |
| Start command | `python maintenance/serve-render-chat.py` |
| Health check path | `/health` |
| Optional model environment | `GEMINI_API_KEY` and `UNIFIT_GEMINI_MODEL` (use `gemini-3.5-flash-lite` to match the local demo configuration) |

Set the Netlify variables and redeploy to generate the same-origin `/api/chat` proxy. In a Netlify preview, run a marks search, ask Ask UniFit about the results, and ask UniFit Chat “Who gives me my exam records?” Then check a model-backed reply with each provider configured.

## Maintain and deploy

Open `maintenance/unifit.sqlite` in DBeaver with a SQLite connection. After saving a reviewed data update, regenerate the site files and check links:

```powershell
python maintenance/export-site.py
python maintenance/check-links.py
```

For the Python navigation chat on Vercel, use the checked-in `vercel.json` and set `GEMINI_API_KEY` as a sensitive environment variable. See the [maintenance guide](maintenance/README.md) for deployment verification, database tables, and sample queries.