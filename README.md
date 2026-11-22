# UniFit

UniFit helps students explore universities and colleges in Myanmar and compare their matriculation marks with published 2026 admission requirements.

- **University Lists** lets you browse and filter campuses, then open a profile for majors, images, and Burmese admission requirements.
- **Search Your Uni** uses your subject set, marks, and exam center to show matching programmes. Select **More Details** to jump to the relevant requirements.

Search results are a guide to published criteria. Where a campus has unconfirmed exam-stream restrictions, UniFit asks you to confirm your stream with the university.

## Preview locally

Open this repository folder in VS Code. From its terminal, run:

```powershell
python -m http.server 8082 --bind 127.0.0.1
```

Keep the terminal open and visit [UniFit on localhost](http://127.0.0.1:8082/index.html). The preview uses the generated files included in this repository.

## Project layout

| Location | Contents |
| --- | --- |
| `universities/` | University profile pages |
| `assets/` | Stylesheets, JavaScript, and images |
| `data/` | Generated university, admissions, and profile data |
| `maintenance/` | SQLite database, exporter, link checker, and maintenance guide |

## Update the data

Open `maintenance/unifit.sqlite` in DBeaver using a SQLite connection. After committing an approved update to the database, run these commands from the repository root:

```powershell
python maintenance/export-site.py
python maintenance/check-links.py
```

See the [maintenance guide](maintenance/README.md) for the database tables, sample queries, and update workflow.
