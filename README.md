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

## Korean translations

The page shows each session's title in Korean with the English original underneath, and the description in Korean with a button to switch to the original. Translations live in `translations/ko.json`, keyed by a hash of the English text. When the catalog is refreshed, only the text that changed needs translating again.

`translate_catalog.py` only manages the files; it does not translate. After fetching new data:

```bash
python3 translate_catalog.py status   # How much is translated and how much is left
python3 translate_catalog.py export   # Write untranslated text to data/translate/todo/NNN.json
# Translate each todo file into data/translate/done/NNN.json as {"key": "Korean", ...},
# following translations/STYLE.md. Claude Code can do this if you point it at the two folders.
python3 translate_catalog.py import   # Merge done files into translations/ko.json
python3 build_viewer.py
```

`python3 translate_catalog.py prune` removes translations for text that is no longer in the catalog. Sessions without a translation are shown in English.

## Layout

```
.
├── fetch_catalog.py        Fetcher: catalog API → data/
├── translate_catalog.py    Translation queue: data/ ⇄ translations/
├── build_viewer.py         Builder: data/ + translations/ + templates/ → catalog.html
├── templates/
│   └── viewer.html         Page template (HTML, CSS, JS)
├── translations/
│   ├── ko.json             Korean titles and descriptions, keyed by source-text hash
│   └── STYLE.md            Translation style guide and glossary
├── data/
│   ├── sessions_raw.json   Raw API response (about 21MB). Not in git
│   └── translate/          todo/ and done/ work files. Not in git
└── catalog.html            The output. Double-click to open. Not in git
```

`data/` and `catalog.html` are kept out of git because the scripts can recreate them. `translations/` is kept in git because recreating it means translating everything again. After a fresh clone, run steps 1 and 2 first.

## Where to make changes

| To change | Edit |
|---|---|
| Page appearance, filter options, timetable behavior | `templates/viewer.html` |
| Which fields the page receives | `slim_session` in `build_viewer.py` |
| Translation wording and glossary | `translations/STYLE.md`, then re-translate the affected entries |

The session data is inserted where `__CATALOG_DATA__` appears in `templates/viewer.html`. Do not remove that string.

## Notes

- The 전체 세션 tab has a 목록 / 시간표 switch. 시간표 shows one day at a time, with buildings as columns and 30-minute start slots as rows. Search and filters still apply, and every run of a repeated session is shown. Click a card for its details.
- Favorites are stored in the browser. If you move or rename `catalog.html`, some browsers will lose them.
- When the page is published as a Claude Artifact, favorites are also saved to the viewer's account and stay in sync across devices. The local file cannot do this.
- The Export (내보내기) menu saves the list as it is currently filtered, searched, and sorted, as CSV, Excel (.xlsx), or JSON. It includes rows not yet loaded by "더 보기". In the 내 일정 tab it saves your favorites. As a Claude Artifact this needs the `downloads` capability, and the viewer confirms each save.
- Times and rooms keep changing until the event. Check the official catalog before you register.
- `python3 build_viewer.py --fragment PATH` also saves the page body without the `<html>` wrapper, for publishing as a Claude Artifact.
