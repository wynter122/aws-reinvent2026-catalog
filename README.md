# re:Invent 2026 세션 뷰어

AWS re:Invent 2026 세션 카탈로그를 수집해, 검색·필터·시간표 기능이 있는 단일 HTML 파일로 만드는 개인용 도구입니다.
Python 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.

## 사용법

```bash
python3 fetch_catalog.py   # 1. 최신 세션 데이터 수집 (약 1분)
python3 build_viewer.py    # 2. catalog.html 생성
open catalog.html          # 3. 브라우저로 열기
```

데이터를 새로 받지 않고 화면만 고쳤다면 2번만 실행하면 됩니다.

## 구조

```
.
├── fetch_catalog.py        수집기: 카탈로그 API → data/
├── build_viewer.py         생성기: data/ + templates/ → catalog.html
├── templates/
│   └── viewer.html         화면 템플릿 (HTML, CSS, JS)
├── data/
│   └── sessions_raw.json   API 원본 (약 21MB). git 제외
└── catalog.html            결과물. 더블클릭으로 열림. git 제외
```

`data/` 와 `catalog.html` 은 스크립트로 다시 만들 수 있어 git 에 넣지 않습니다. 저장소를 새로 받았다면 사용법의 1, 2번을 먼저 실행하세요.

## 무엇을 고치려면 어디를 보나

| 하고 싶은 일 | 파일 |
|---|---|
| 화면 모양, 필터 항목, 시간표 동작 변경 | `templates/viewer.html` |
| 화면에 쓸 필드 추가 또는 제거 | `build_viewer.py` 의 `slim_session` |

`templates/viewer.html` 안의 `__CATALOG_DATA__` 자리에 세션 데이터가 들어갑니다. 이 문자열은 지우지 마세요.

## 참고

- 즐겨찾기는 브라우저에 저장됩니다. `catalog.html` 의 위치나 이름을 바꾸면 브라우저에 따라 즐겨찾기가 사라질 수 있습니다.
- 일정과 장소는 행사 전까지 계속 바뀝니다. 등록 전에는 공식 카탈로그에서 확인하세요.
- `python3 build_viewer.py --fragment 경로` 는 `<html>` 래퍼 없는 본문만 따로 저장합니다 (Claude Artifact 게시용).
