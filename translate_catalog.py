#!/usr/bin/env python3
"""세션 제목·설명 번역 관리기.

번역은 translations/ko.json 에 "원문 해시 -> 한국어" 로 쌓아 두고 git 에 함께 넣는다.
원문이 바뀐 문장만 키가 달라지므로, 카탈로그를 다시 받아도 새로 번역할 것만 남는다.
번역 자체는 이 스크립트가 하지 않는다. 할 일을 파일로 내보내면 사람이든 Claude 든
translations/STYLE.md 를 따라 번역해 결과 파일을 두고, import 로 받아들인다.

  python3 translate_catalog.py status   번역된 것 / 남은 것 / 쓰이지 않는 것 세기
  python3 translate_catalog.py export   남은 문장을 data/translate/todo/NNN.json 으로 나누어 저장
  python3 translate_catalog.py import   data/translate/done/*.json 을 ko.json 에 합치기
  python3 translate_catalog.py prune    현재 카탈로그에 없는 원문의 번역 지우기

todo 파일:  {"items": [{"k": 키, "code": 세션 코드, "field": "title"|"abstract", "en": 원문}, ...]}
done 파일:  {키: 번역, ...}  (todo 파일과 같은 이름으로 저장)
"""
import argparse
import json
import re
from pathlib import Path

from build_viewer import BASE_DIR, KO_PATH, RAW_PATH, load_translations, slim_session, text_key

WORK_DIR = BASE_DIR / "data" / "translate"
TODO_DIR = WORK_DIR / "todo"
DONE_DIR = WORK_DIR / "done"
BATCH_CHARS = 25000  # todo 파일 하나에 담을 원문 글자 수. 한 세션의 제목과 설명은 나누지 않는다
HANGUL = re.compile(r"[가-힣]")


def source_items():
    """현재 카탈로그에서 번역할 문장. 같은 원문은 한 번만, 세션 코드 순으로."""
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    items = {}
    for row in sorted((slim_session(s) for s in raw), key=lambda r: r["c"]):
        for field, src in (("title", "t"), ("abstract", "a")):
            text = row.get(src)
            if text:
                items.setdefault(text_key(text), {"k": text_key(text), "code": row["c"], "field": field, "en": text})
    return items


def save_translations(ko):
    KO_PATH.parent.mkdir(exist_ok=True)
    # 한 줄에 한 항목씩 두어 git diff 로 바뀐 번역을 보기 쉽게 한다
    KO_PATH.write_text(json.dumps(ko, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")


def cmd_status(items, ko):
    todo = [i for i in items.values() if i["k"] not in ko]
    stale = [k for k in ko if k not in items]
    print(f"원문 {len(items)}개 중 번역 {len(items) - len(todo)}개, 남은 것 {len(todo)}개"
          f" (원문 {sum(len(i['en']) for i in todo):,}자)")
    if stale:
        print(f"현재 카탈로그에 없는 번역 {len(stale)}개 (prune 으로 지울 수 있음)")


def cmd_export(items, ko):
    TODO_DIR.mkdir(parents=True, exist_ok=True)
    for old in TODO_DIR.glob("*.json"):
        old.unlink()
    batches, batch, size = [], [], 0
    for item in items.values():
        if item["k"] in ko:
            continue
        # 같은 세션의 제목과 설명은 한 파일에 두어 번역할 때 문맥을 함께 보게 한다
        if batch and size + len(item["en"]) > BATCH_CHARS and item["code"] != batch[-1]["code"]:
            batches.append(batch)
            batch, size = [], 0
        batch.append(item)
        size += len(item["en"])
    if batch:
        batches.append(batch)
    for n, batch in enumerate(batches, 1):
        path = TODO_DIR / f"{n:03d}.json"
        path.write_text(json.dumps({"items": batch}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"남은 문장 {sum(map(len, batches))}개를 {len(batches)}개 파일로 저장 -> {TODO_DIR}")
    print(f"번역 결과는 같은 이름으로 {DONE_DIR} 에 두고 import 를 실행하세요.")


def cmd_import(items, ko):
    added, problems = 0, []
    for path in sorted(DONE_DIR.glob("*.json")):
        try:
            done = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{path.name}: JSON 오류 ({e})")
            continue
        for key, text in done.items():
            text = " ".join(str(text).split())
            if key not in items:
                problems.append(f"{path.name}: 알 수 없는 키 {key}")
            # 제품 이름뿐인 제목처럼 원문 그대로 두는 것은 허용한다
            elif not text or (not HANGUL.search(text) and text != items[key]["en"]):
                problems.append(f"{path.name}: {items[key]['code']} {items[key]['field']} 번역이 비었거나 한글이 없음")
            else:
                added += ko.get(key) != text
                ko[key] = text
    save_translations(ko)
    print(f"번역 {added}개 반영 -> {KO_PATH}")
    for p in problems:
        print("  건너뜀:", p)
    cmd_status(items, ko)


def cmd_prune(items, ko):
    kept = {k: v for k, v in ko.items() if k in items}
    save_translations(kept)
    print(f"쓰이지 않는 번역 {len(ko) - len(kept)}개 삭제")


def main():
    commands = {"status": cmd_status, "export": cmd_export, "import": cmd_import, "prune": cmd_prune}
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=commands)
    args = parser.parse_args()
    commands[args.command](source_items(), load_translations())


if __name__ == "__main__":
    main()
