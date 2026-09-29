#!/usr/bin/env python3
"""AWS re:Invent 2026 세션 카탈로그 수집기.

카탈로그 페이지가 내부적으로 호출하는 RainFocus 검색 API를 그대로 사용한다.
표준 라이브러리만 사용하므로 별도 설치 없이 `python3 fetch_catalog.py` 로 실행.

출력:
  data/sessions_raw.json  API 원본 그대로
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

REG_BASE = "https://registration.awsevents.com/"
CATALOG_BASE = "https://catalog.awsevents.com/"
WORKFLOW_TOKEN = "awsevents.reinvent2026.eventcatalog"
PAGE_URL = REG_BASE + "flow/awsevents/reinvent2026/eventcatalog/page/eventcatalog"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
PAGE_SIZE = 50
DELAY_SEC = 0.5  # 서버 부담을 줄이기 위한 요청 간 대기
OUT_DIR = Path(__file__).resolve().parent / "data"


def request_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))


def load_widget_conf():
    """페이지 설정에서 검색 API용 위젯 ID / API 프로필 토큰을 읽는다."""
    query = urllib.parse.urlencode(
        {"workflowApiToken": WORKFLOW_TOKEN, "pageUri": "eventcatalog", "page": "eventcatalog"}
    )
    conf = request_json(REG_BASE + "flow/loadPage?" + query, headers={"Referer": PAGE_URL})
    widget = conf["data"]["widgetConf"]
    return widget["widgetId"], widget["apiProfileToken"]


def fetch_sessions(widget_id, api_profile):
    headers = {
        "rfapiprofileid": api_profile,
        "rfwidgetid": widget_id,
        "Origin": REG_BASE.rstrip("/"),
        "Referer": REG_BASE,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    sessions = {}
    offset = 0
    total = None
    while total is None or offset < total:
        body = urllib.parse.urlencode(
            {"type": "session", "catalogDisplay": "list", "size": PAGE_SIZE, "from": offset}
        ).encode()
        res = request_json(CATALOG_BASE + "api/search", data=body, headers=headers)
        if res.get("responseCode") != "0":
            raise RuntimeError(f"API 오류: {res.get('responseCode')} {res.get('responseMessage')}")
        # 첫 페이지는 sectionList 로 감싸져 오고, 이후 페이지는 최상위에 바로 온다
        section = res["sectionList"][0] if "sectionList" in res else res
        total = section["total"]
        items = section.get("items") or []
        if not items:
            break
        for item in items:
            sessions[item["sessionID"]] = item
        offset += PAGE_SIZE
        print(f"  {min(offset, total)}/{total}")
        time.sleep(DELAY_SEC)
    return list(sessions.values()), total


def main():
    print("위젯 설정 조회...")
    widget_id, api_profile = load_widget_conf()
    print("세션 수집...")
    sessions, total = fetch_sessions(widget_id, api_profile)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "sessions_raw.json").write_text(
        json.dumps(sessions, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"완료: {len(sessions)}개 저장 (API 보고 총계 {total}) -> {OUT_DIR}")


if __name__ == "__main__":
    main()
