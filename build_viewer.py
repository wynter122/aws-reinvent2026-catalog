#!/usr/bin/env python3
"""세션 카탈로그 뷰어 생성기.

fetch_catalog.py 가 만든 data/sessions_raw.json 에서 화면에 필요한 필드만 추려
templates/viewer.html 에 끼워 넣고, 단일 파일 catalog.html 을 만든다.
translations/ko.json 에 번역이 있으면 제목과 설명의 한국어도 함께 넣는다.
표준 라이브러리만 사용하므로 `python3 build_viewer.py` 로 실행.

옵션:
  --fragment PATH  <html>/<head> 래퍼 없는 본문만 따로 저장 (Artifact 게시용)
"""
import argparse
import hashlib
import html
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from fetch_catalog import PAGE_URL

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "data" / "sessions_raw.json"
TEMPLATE_PATH = BASE_DIR / "templates" / "viewer.html"
OUT_PATH = BASE_DIR / "catalog.html"
KO_PATH = BASE_DIR / "translations" / "ko.json"
DATA_PLACEHOLDER = "__CATALOG_DATA__"
LOCAL_HEAD = (
    '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
)

# 뷰어의 짧은 키 -> 원본 attribute 이름
LIST_ATTRIBUTES = {
    "tp": "Topic",
    "ai": "Area of Interest",
    "sv": "Services",
    "ro": "Role",
    "in": "Industry",
    "ft": "Features",
}
AWS_COMPANY = re.compile(r"^\s*(aws|amazon web services)\b", re.IGNORECASE)
REPEAT_SUFFIX = re.compile(r"-R\d*$")
REPEAT_TITLE = re.compile(r"\s*\[REPEAT\]\s*$", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def attribute_values(session, name):
    values = [
        av.get("value", "")
        for av in session.get("attributevalues") or []
        if av.get("attribute") == name
    ]
    return list(dict.fromkeys(v for v in values if v))


def clean_text(text):
    return " ".join(html.unescape(TAG.sub(" ", text or "")).split())


def text_key(text):
    """번역 캐시의 키. 원문이 바뀌면 키도 바뀌어 그 문장만 다시 번역된다."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_translations():
    if not KO_PATH.exists():
        return {}
    return json.loads(KO_PATH.read_text(encoding="utf-8"))


def slim_speaker(p):
    company = (p.get("globalCompany") or p.get("companyName") or "").strip()
    if AWS_COMPANY.match(company):
        company = "AWS"
    speaker = {
        "n": (p.get("fullName") or p.get("globalFullName") or "").strip(),
        "j": (p.get("globalJobtitle") or p.get("jobTitle") or "").strip(),
        "o": company,
    }
    return {k: v for k, v in speaker.items() if v}


def slim_session(session):
    code = session.get("code", "")
    parts = session.get("codeParts") or {}
    times = sorted(session.get("times") or [], key=lambda t: t.get("dayTimeSort", ""))
    first = times[0] if times else {}
    room = first.get("room", "")
    venue = room.split(" | ")[0] if room else next(iter(attribute_values(session, "Venue")), "")
    level = next(iter(attribute_values(session, "Level")), "")
    appendices = attribute_values(session, "Session Appendices")

    row = {
        "c": code,
        "g": REPEAT_SUFFIX.sub("", code),
        "t": REPEAT_TITLE.sub("", session.get("title", "")).strip(),
        "y": session.get("type", ""),
        "l": level[:3] if level[:3].isdigit() else "",
        "tr": parts.get("alpha0", ""),
        "a": clean_text(session.get("abstract")),
        "d": first.get("date", ""),
        "s": first.get("startTime", ""),
        "e": first.get("endTime", ""),
        "sm": int(first["startTimeMin"]) if first.get("startTimeMin") is not None else None,
        "em": int(first["endTimeMin"]) if first.get("endTimeMin") is not None else None,
        "r": room,
        "v": venue,
        "cap": first.get("capacity", ""),
        "len": int(session["length"]) if session.get("length") else None,
        "sp": [slim_speaker(p) for p in session.get("participants") or []],
        "lap": 1 if "Laptop required" in appendices else 0,
        "spon": 1 if "Sponsored" in appendices or parts.get("alpha2") == "S" else 0,
        "u": PAGE_URL + "?search=" + urllib.parse.quote(code),
    }
    for key, name in LIST_ATTRIBUTES.items():
        row[key] = attribute_values(session, name)
    return {k: v for k, v in row.items() if v not in ("", None, [], 0)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fragment", type=Path, help="래퍼 없는 본문을 저장할 경로")
    args = parser.parse_args()

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    sessions = sorted((slim_session(s) for s in raw), key=lambda r: r["c"])
    ko = load_translations()
    for row in sessions:
        for src, dst in (("t", "tk"), ("a", "ak")):
            if row.get(src) and ko.get(text_key(row[src])):
                row[dst] = ko[text_key(row[src])]
    translated = sum(1 for row in sessions if "tk" in row)
    payload = {
        "meta": {
            "event": "re:Invent 2026",
            "count": len(sessions),
            "ko": translated,
            "modified": max((s.get("modified", "") for s in raw), default=""),
            "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "sessions": sessions,
    }
    # <script> 안에 넣으므로 "<" 를 이스케이프해 "</script>" 로 끊기지 않게 한다
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if DATA_PLACEHOLDER not in template:
        raise RuntimeError(f"템플릿에 {DATA_PLACEHOLDER} 자리가 없습니다")
    page = template.replace(DATA_PLACEHOLDER, data)

    out = OUT_PATH
    out.write_text(LOCAL_HEAD + page, encoding="utf-8")
    print(f"완료: 세션 {len(sessions)}개 (번역 {translated}개) -> {out} ({out.stat().st_size / 1e6:.1f}MB)")
    if args.fragment:
        args.fragment.write_text(page, encoding="utf-8")
        print(f"본문만 저장: {args.fragment}")


if __name__ == "__main__":
    main()
