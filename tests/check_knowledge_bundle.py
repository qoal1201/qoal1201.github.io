"""`knowledge/` 번들이 OKF v0.2 형식을 지키는지 본다.

판정 로직은 짓지 않는다 — `okf_document.py` 가 상류에서 가져온 것을 그대로 쓴다
(`diff` 0 으로 복사. 출처·라이선스 표기는 그 파일 머리말에 있다).
이 파일이 하는 일은 **번들 전체를 돌면서 그 판정을 먹이는 것**뿐이다.

`python3 tests/check_knowledge_bundle.py`             — 번들을 검사한다
`python3 tests/check_knowledge_bundle.py --selftest`  — 검사가 실제로 빨개지는지 본다

## ⚠ 남의 레포 하한을 안 들여왔다 — 이게 이 파일에서 제일 중요한 결정이다

`kaggle-team` 판에는 `MIN_CONCEPTS = 3` 과 `MIN_BODY_CHARS = 200` 이 모듈 상수로 있고,
`brain` 판은 앞의 것만 뽑고 뒤의 것과 「카드마다 `# 한계` 절 필수」는 남겼다.
그 숫자들은 **그 레포들의 역사가 인코딩된 값**이다 — *"씨앗이 셋이었고"* ·
*"이 레포에서 한계 없는 주장이 네 번 틀렸다"*.

`실측 2026-08-20`: 그 상수를 안 묻고 베낀 레포 둘에서 **초록을 맞추려고 에이전트가
개념 카드를 혼자 채우는** 일이 벌어졌다. 하한이 내용을 강제한 것이다.

→ **이 레포는 하한을 합의한 적이 없으므로 하한 없이 깐다.** 개수 하한만 예외적으로
   `knowledge/index.md` frontmatter 의 `min_concepts` 에서 읽는다 — **적혀 있으면
   이 레포가 스스로 정한 것이고, 없으면 하한이 없다.** 본문 길이·절 구성은 안 센다.

⚠ 그래서 **빈 번들은 초록이다.** 그게 맞다 — 카드가 0장인 것은 형식 위반이 아니다.
   초록을 「지식이 있다」로 읽으면 안 된다(아래 「초록의 뜻」).

## 검사가 보는 것

1. 예약 이름(`index.md`·`log.md`)이 아닌 모든 `.md` 에 **파싱 가능한 frontmatter** (스펙 §11)
2. **`type` 이 비어 있지 않다** — 스펙이 항상 요구하는 유일한 키 (§11)
3. **인용한 레포 안 출처가 실재한다** — 카드가 딛고 선 것이 죽으면 빨개진다
4. 신뢰 등급이 `verified` 에서 정상적으로 유도된다 (§5.3)
5. `index.md` 가 있고 **「한계」 절을 갖는다** — 검사가 못 보는 것을 적는 자리

   ⚠ 4번·5번 구분: 「한계」를 **카드마다** 요구하는 것은 `brain` 의 역사라 안 들여왔다.
   `index.md` 한 곳에만 요구하는 것은 하한이 아니라 **번들이 자기 사각을 적는 장치**다.

## 초록의 뜻

**부재는 검사할 수 없다.** 초록은 *"적힌 것이 형식을 지킨다"* 는 뜻이지
*"지식이 최신이다"* 도 *"이 레포가 아는 것이 다 여기 있다"* 도 아니다.
이 레포에서 그 사각이 특히 넓은 이유는 `knowledge/index.md` 「한계」 절이 갖는다.

## ⚠ 아직 무엇에도 안 물려 있다

이 검사를 언제 돌릴지가 **미정**이다. 이 레포의 지식 뭉치 대부분이 `.gitignore` 안이라
GitHub Actions 는 그것을 볼 수 없고(체크아웃에 없다), 커밋 훅은 커밋이 드물어 안 돈다
(`실측`: 2026-07-29 → 08-20 커밋 0건, 그 사이 파일 변경은 있었다).
지금은 **손으로 돌리는 검사**다 — 그 상태를 초록으로 포장하지 않으려고 여기 적어둔다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from okf_document import (RESERVED_FILENAMES, OKFDocument, OKFDocumentError,
                          trust_tier)

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "knowledge"
TIERS = ("unverified", "machine-confirmed", "human-reviewed")


def _label(path: Path) -> str:
    """레포 안이면 레포 기준 경로, 샌드박스면 번들 기준 경로."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return f"knowledge/{path.name}"


def _declared_floor(index: Path) -> int:
    """개수 하한은 이 레포가 index.md 에 적은 것만 인정한다. 없으면 0."""
    if not index.is_file():
        return 0
    try:
        fm = OKFDocument.parse(index.read_text(encoding="utf-8")).frontmatter
        return int(fm.get("min_concepts", 0))
    except (OKFDocumentError, TypeError, ValueError):
        return 0


def check(bundle: Path = BUNDLE) -> list[str]:
    bad: list[str] = []
    if not bundle.is_dir():
        return ["knowledge/ 가 없다"]

    index = bundle / "index.md"
    if not index.is_file():
        bad.append("knowledge/index.md 가 없다 — 번들 진입점은 예약 이름이다")
    elif "한계" not in index.read_text(encoding="utf-8"):
        bad.append("knowledge/index.md 에 「한계」 절이 없다 — 검사가 못 보는 것을 적어야 한다")

    concepts = sorted(p for p in bundle.glob("*.md") if p.name not in RESERVED_FILENAMES)

    floor = _declared_floor(index)
    if floor and len(concepts) < floor:
        bad.append(f"개념이 {len(concepts)}장이다 — 이 레포가 index.md 에 선언한 하한 {floor}")

    for path in concepts:
        rel = _label(path)
        try:
            doc = OKFDocument.parse(path.read_text(encoding="utf-8"))
            doc.validate()
        except OKFDocumentError as exc:
            bad.append(f"{rel}: {exc}")
            continue

        fm = doc.frontmatter
        if not str(fm.get("type", "")).strip():
            bad.append(f"{rel}: type 이 비었다")

        for src in fm.get("sources", []) or []:
            res = str((src or {}).get("resource", ""))
            if not res or res.startswith("http"):
                continue
            if not (ROOT / res).exists():
                bad.append(f"{rel}: 인용한 출처 {res} 이 실재하지 않는다")

        tier = trust_tier(fm)
        if tier not in TIERS:
            bad.append(f"{rel}: 신뢰 등급이 이상하다 — {tier!r}")
    return bad


def selftest() -> int:
    """깨뜨리면 실제로 빨개지나. 안 도는 검사보다 나쁜 건 안 빨개지는 검사다."""
    import shutil
    import tempfile

    body = "가" * 300
    cases: dict[str, str | None] = {
        "type 이 빈 카드": f"---\ntype:\ntitle: x\n---\n\n# 정의\n\n{body}\n",
        "frontmatter 가 깨진 카드": f"---\ntype: Concept\n\ttitle: x\n---\n\n{body}\n",
        "없는 출처를 인용한 카드": (
            "---\ntype: Concept\ntitle: x\n"
            "sources:\n  - id: a\n    resource: paper-reviews/없는파일.qmd\n    title: x\n"
            f"---\n\n# 정의\n\n{body}\n"),
        "선언한 하한에 못 미치는 번들": None,
    }

    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp) / "knowledge"
        shutil.copytree(BUNDLE, sandbox)
        for name, text in cases.items():
            if text is None:
                idx = sandbox / "index.md"
                keep = idx.read_text(encoding="utf-8")
                idx.write_text(keep.replace('okf_version: "0.2"',
                                            'okf_version: "0.2"\nmin_concepts: 99'),
                               encoding="utf-8")
                reddened = bool(check(sandbox))
                idx.write_text(keep, encoding="utf-8")
            else:
                probe = sandbox / "_break.md"
                probe.write_text(text, encoding="utf-8")
                reddened = bool(check(sandbox))
                probe.unlink()
            print(f"  {'통과' if reddened else '✗ 실패'} — {name} 를 넣으니 "
                  f"{'빨개진다' if reddened else '초록이다'}")
            failed += 0 if reddened else 1

        if check(sandbox):
            print("  ✗ 실패 — 되돌렸는데 초록이 안 돌아온다")
            failed += 1
        else:
            print("  통과 — 되돌리니 초록 복귀")
    return failed


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        n = selftest()
        print("검사가 빨개진다" if n == 0 else f"{n}건이 안 빨개진다")
        sys.exit(1 if n else 0)
    problems = check()
    for p in problems:
        print(p)
    print(f"knowledge/ — {'초록' if not problems else str(len(problems)) + '건 빨감'}")
    sys.exit(1 if problems else 0)
