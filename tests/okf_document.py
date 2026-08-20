"""OKF v0.2 문서 하나를 읽는 최소 도구 — **상류에서 가져온 로직이다.**

## 출처

- 상류: `GoogleCloudPlatform/knowledge-catalog` · `okf/src/reference_agent/bundle/document.py`
- 고정 커밋: `780fe9d30b5bbca8931256edf1d0290d6bda5462`
- 라이선스: Apache 2.0 (`okf/LICENSE.md`)
- 스펙: `okf/SPEC.md` (OKF v0.2) — 아래 `§` 표기는 전부 그 문서의 절이다
- 채택 근거: `docs/adr/0024-adopt-okf-for-knowledge.md`

`parse` 의 골격 · `validate` · `normalize_verified` · `trust_tier` · `is_stale` 는
상류의 판정을 그대로 옮긴 것이다. **새로 지은 판정이 아니다.**

## 상류와 **다른 한 곳** — 여기만 읽으면 된다

상류는 frontmatter 를 `yaml.safe_load` 로 읽는다. **이 레포엔 `pyyaml` 이 없고**
(`실측` 2026-08-18: `.venv` · 시스템 파이썬 둘 다 `ModuleNotFoundError`),
`docs/adr/0024` 가 *"패키지를 설치하지 않는다"* 로 못박았다. 그래서 그 한 줄만
아래 `_parse_frontmatter` 로 갈았다. 나머지는 손대지 않았다.

⚠ **이 파서는 YAML 이 아니라 YAML 의 좁은 부분집합이다.** 그래서 **모르는 모양을
만나면 조용히 넘기지 않고 `OKFDocumentError` 를 던진다.** 관대한 파서였다면
`type:` 한 줄이 오타로 죽어도 초록이 나온다 — 그게 이 레포에서 네 번 난 사고다.
받는 것: `키: 스칼라` · `키: [a, b]` · `키: {a: b}` · 블록 목록(`- {a: b}` ·
`- a: 1` + 들여쓴 형제 키) · 한 줄 통째 주석. **그 밖은 전부 실패한다** —
블록 스칼라(`|` `>`) · 앵커 · 여러 겹 흐름 · 값 뒤 주석 · 탭.

⚠ **타입이 하나 다르다.** `yaml.safe_load` 는 `stale_after: 2026-09-23` 을
`datetime.date` 로 주지만 이 파서는 문자열로 준다. `is_stale` 이 상류에서 이미
둘 다 받게 돼 있어(`isinstance(raw, date)` 가지) **판정은 안 바뀐다.**
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

# OKF v0.2 §11: `type` is the only always-required frontmatter key.
REQUIRED_FRONTMATTER_KEYS = ("type",)

# §3.1 — 어느 층에서든 개념 문서가 아닌 이름. 적합성 검사가 이 둘을 건너뛴다.
RESERVED_FILENAMES = ("index.md", "log.md")

_FRONTMATTER_DELIM = "---"

_COMMENT = re.compile(r"^\s*#")
_INLINE_COMMENT = re.compile(r"\s#")
_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_.\-]*):(?:\s+(.*))?$")


class OKFDocumentError(ValueError):
    pass


# ------------------------------------------------- frontmatter 파서 (상류와 다른 한 곳)
def _scalar(raw: str, line: int) -> str:
    s = raw.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]                       # 따옴표 안에서는 `#` 도 주석이 아니다
    if s.startswith("#"):
        # ★ YAML 은 이 줄을 **주석**으로 읽어 값이 None 이 된다. 문자열로 받으면 우리만
        #   초록이고 상류 소비자는 부적합 판정을 낸다 — 갈리는 쪽이 하필 `type` 이다.
        raise OKFDocumentError(
            f"{line}행: 값이 `#` 로 시작한다 — YAML 은 주석으로 읽어 값이 빈다 "
            f"(내용이면 따옴표로 감싸라) — {s!r}")
    if s[:1] in ("[", "{", "|", ">", "&", "*", "!"):
        raise OKFDocumentError(f"{line}행: 이 파서가 안 받는 YAML 표기 — {s[:1]!r}")
    if _INLINE_COMMENT.search(s):
        raise OKFDocumentError(f"{line}행: 값 뒤 주석은 안 받는다 (따옴표로 감싸라) — {s!r}")
    return s


def _flow_list(s: str, line: int) -> list:
    body = s[1:-1].strip()
    if not body:
        return []
    parts = [p.strip() for p in body.split(",")]
    if any(not p for p in parts):
        raise OKFDocumentError(f"{line}행: 흐름 목록에 빈 칸이 있다 — {s!r}")
    return [_scalar(p, line) for p in parts]


def _flow_map(s: str, line: int) -> dict:
    body = s[1:-1].strip()
    out: dict[str, Any] = {}
    if not body:
        return out
    for part in body.split(","):
        key, sep, val = part.partition(":")
        key = key.strip()
        if not sep or not _NAME.match(key):
            raise OKFDocumentError(f"{line}행: 흐름 표의 `키: 값` 이 아니다 — {part!r}")
        if key in out:
            raise OKFDocumentError(f"{line}행: `{key}` 가 두 번 나온다")
        out[key] = _scalar(val, line)
    return out


def _value(raw: str, line: int):
    s = raw.strip()
    if s.startswith("[") and s.endswith("]"):
        return _flow_list(s, line)
    if s.startswith("{") and s.endswith("}"):
        return _flow_map(s, line)
    return _scalar(s, line)


def _mapping(items: list[tuple[int, str, int]], i: int, indent: int) -> tuple[dict, int]:
    out: dict[str, Any] = {}
    while i < len(items):
        col, text, line = items[i]
        if col < indent or text.startswith("- "):
            break
        if col > indent:
            raise OKFDocumentError(f"{line}행: 들여쓰기가 형제 키와 안 맞는다")
        m = _KEY.match(text)
        if not m:
            raise OKFDocumentError(f"{line}행: `키: 값` 이 아니다 — {text!r}")
        key, inline = m.group(1), m.group(2)
        if key in out:
            raise OKFDocumentError(f"{line}행: `{key}` 가 두 번 나온다")
        if inline and inline.strip():
            out[key], i = _value(inline, line), i + 1
        elif i + 1 < len(items) and items[i + 1][0] > indent:
            out[key], i = _block(items, i + 1, items[i + 1][0])
        else:
            out[key], i = "", i + 1          # 값 없는 키 — §11 의 「비어 있음」 판정에 걸린다
    return out, i


def _sequence(items: list[tuple[int, str, int]], i: int, indent: int) -> tuple[list, int]:
    out: list[Any] = []
    while i < len(items) and items[i][0] == indent and items[i][1].startswith("- "):
        _, text, line = items[i]
        rest = text[2:].strip()
        j = i + 1
        while j < len(items) and items[j][0] > indent:
            j += 1
        inner = items[i + 1:j]
        if rest.startswith("{") and rest.endswith("}"):
            if inner:
                raise OKFDocumentError(f"{line}행: 흐름 표에 블록 줄이 딸려 있다")
            out.append(_flow_map(rest, line))
        elif _KEY.match(rest):
            col = inner[0][0] if inner else indent + 2
            merged = [(col, rest, line)] + inner
            value, k = _mapping(merged, 0, col)
            if k != len(merged):
                raise OKFDocumentError(f"{line}행: 목록 항목을 끝까지 못 읽었다")
            out.append(value)
        elif inner:
            raise OKFDocumentError(f"{line}행: 스칼라 항목에 블록 줄이 딸려 있다")
        else:
            out.append(_scalar(rest, line))
        i = j
    return out, i


def _block(items: list[tuple[int, str, int]], i: int, indent: int):
    if items[i][1].startswith("- "):
        return _sequence(items, i, indent)
    return _mapping(items, i, indent)


def _parse_frontmatter(fm_text: str, offset: int = 0) -> dict:
    """`yaml.safe_load` 자리. 부분집합만 받고 나머지는 던진다 (모듈 머리말 참조)."""
    items: list[tuple[int, str, int]] = []
    for line, raw in enumerate(fm_text.splitlines(), start=1 + offset):
        if not raw.strip() or _COMMENT.match(raw):
            continue
        if "\t" in raw:
            raise OKFDocumentError(f"{line}행: 탭은 YAML 들여쓰기가 아니다")
        items.append((len(raw) - len(raw.lstrip(" ")), raw.strip(), line))
    if not items:
        return {}
    out, i = _mapping(items, 0, 0)
    if i != len(items):
        raise OKFDocumentError(
            f"{items[i][2]}행부터 못 읽었다 — frontmatter 는 표(mapping)여야 한다")
    return out


# --------------------------------------------------------------- 여기부터 상류 그대로
@dataclass
class OKFDocument:
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @classmethod
    def parse(cls, text: str) -> "OKFDocument":
        lines = text.splitlines()
        if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
            return cls(frontmatter={}, body=text)

        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == _FRONTMATTER_DELIM:
                end_idx = i
                break
        if end_idx is None:
            raise OKFDocumentError("Unterminated YAML frontmatter block")

        fm = _parse_frontmatter("\n".join(lines[1:end_idx]), offset=1)
        body = "\n".join(lines[end_idx + 1:])
        if body.startswith("\n"):
            body = body[1:]
        return cls(frontmatter=fm, body=body)

    def validate(self) -> None:
        missing = [k for k in REQUIRED_FRONTMATTER_KEYS if not self.frontmatter.get(k)]
        if missing:
            raise OKFDocumentError(
                f"Missing required frontmatter keys: {', '.join(missing)}")


def normalize_verified(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    """`verified` 를 목록으로 (§5.2).

    하나뿐인 확인자는 대시 없이 `{ by, at }` 한 표로 적어도 되고, **읽는 쪽은 그것을
    한 칸짜리 목록으로 취급해야 한다**(MUST).
    """
    verified = frontmatter.get("verified")
    if verified is None:
        return []
    if isinstance(verified, dict):
        return [verified]
    if isinstance(verified, list):
        return [v for v in verified if isinstance(v, dict)]
    return []


def trust_tier(frontmatter: dict[str, Any]) -> str:
    """`verified` 에 **누가 있느냐**에서 신뢰 등급을 유도한다 (§5.3).

    - `verified` 가 없다 ⇒ `unverified`
    - `human:` 아닌 배우만 있다 ⇒ `machine-confirmed`
    - `human:<id>` 배우가 있다 ⇒ `human-reviewed`

    저장하는 값이 아니라 **유도하는 값이다.** 그래서 등급을 손으로 매기는 행위가 없다.
    """
    events = normalize_verified(frontmatter)
    if not events:
        return "unverified"
    for event in events:
        by = str(event.get("by") or "")
        if by.startswith("human:"):
            return "human-reviewed"
    return "machine-confirmed"


def is_stale(frontmatter: dict[str, Any], today: date | None = None) -> bool:
    """`stale_after` 로 본 낡음 (§5.5). `today >= stale_after` 면 낡았다.

    ⚠ **낡음은 파손이 아니다.** 이 함수가 True 를 줘도 적합성 검사는 안 빨개진다 —
      날짜가 지나는 건 사실이지 깨진 게 아니다 (`docs/adr/0024` §Consequences).
    """
    raw = frontmatter.get("stale_after")
    if not raw:
        return False
    if isinstance(raw, date):
        stale_after = raw
    else:
        try:
            stale_after = date.fromisoformat(str(raw)[:10])
        except ValueError:
            return False
    return (today or date.today()) >= stale_after
