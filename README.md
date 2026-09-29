# re:Invent 2026 Session Viewer

A personal tool that fetches the AWS re:Invent 2026 session catalog and builds it into a single HTML file with search, filters, and a timetable.
It uses only the Python standard library, so there is nothing to install.

This is an unofficial viewer. The interface is in Korean.

## Usage

```bash
python3 fetch_catalog.py   # 1. Fetch the latest session data (about 1 minute)
python3 build_viewer.py    # 2. Build catalog.html
open catalog.html          # 3. Open it in a browser
```

If you only changed the page and don't need fresh data, run step 2 alone.

## Layout

```
.
├── fetch_catalog.py        Fetcher: catalog API → data/
├── build_viewer.py         Builder: data/ + templates/ → catalog.html
├── templates/
│   └── viewer.html         Page template (HTML, CSS, JS)
├── data/
│   └── sessions_raw.json   Raw API response (about 21MB). Not in git
└── catalog.html            The output. Double-click to open. Not in git
```

`data/` and `catalog.html` are kept out of git because the scripts can recreate them. After a fresh clone, run steps 1 and 2 first.

## Where to make changes

| To change | Edit |
|---|---|
| Page appearance, filter options, timetable behavior | `templates/viewer.html` |
| Which fields the page receives | `slim_session` in `build_viewer.py` |

The session data is inserted where `__CATALOG_DATA__` appears in `templates/viewer.html`. Do not remove that string.

## Notes

- Favorites are stored in the browser. If you move or rename `catalog.html`, some browsers will lose them.
- When the page is published as a Claude Artifact, favorites are also saved to the viewer's account and stay in sync across devices. The local file cannot do this.
- The Export (내보내기) menu saves the list as it is currently filtered, searched, and sorted, as CSV, Excel (.xlsx), or JSON. It includes rows not yet loaded by "더 보기". In the 내 일정 tab it saves your favorites. As a Claude Artifact this needs the `downloads` capability, and the viewer confirms each save.
- Times and rooms keep changing until the event. Check the official catalog before you register.
- `python3 build_viewer.py --fragment PATH` also saves the page body without the `<html>` wrapper, for publishing as a Claude Artifact.
