#!/usr/bin/env python3
"""사이트 정합 lint — 공개 qmd의 기계적 결함을 잡는다.

검사 항목:
1. 깨진 파이프 표 — 헤더 구분선 없는 표 블록 (2026-07-07 용어집에서 실측된 버그 클래스:
   표 사이 빈 줄 때문에 뒷부분이 헤더 없는 블록으로 떨어져 파이프 문자가 그대로 렌더됨)
2. 내부 링크 — 로컬 .qmd/.md 링크의 대상 파일 존재 + {#앵커} 존재 (앵커는 경고 수준)
3. 방문자 표면의 내부 운영 용어 — 전 공개 파일 대상 (일지 예외는 2026-07-10 재구조로 폐지)
4. 가든 문서 상단 상태 줄 존재
5. 문체 쿼터 — 3급 형태 패턴(산문 대시·산문 볼드·이모지). check_style
6. kaggle 점수 동기화 — foundations 랜딩 표 vs kaggle repo README. check_kaggle_sync
7. 용어집 골격 — 중복 앵커·항목 문단 수·최장 항목 참고 출력. check_glossary

(2026-07-27: 1~4만 적혀 있어 감사 세션이 5~7을 모르고 중복 수작업할 수 있었다. 코드가 진실원이므로
 항목이 늘거나 줄면 이 목록을 같이 고친다.)

사용: python3 _tools/site_lint.py  (repo 어디서든)
종료 코드: 오류(error)가 있으면 1, 경고만 있으면 0
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# _quarto.yml render 목록과 동기화된 공개 파일 집합
PUBLIC_FILES = (
    sorted(ROOT.glob("*.qmd"))
    + sorted((ROOT / "paper-reviews").glob("*.qmd"))
    + sorted((ROOT / "experiments").glob("*.qmd"))
    + sorted((ROOT / "foundations").glob("*.qmd"))
)

# 내부 운영 용어 — 방문자 표면에서 금지 (CLAUDE.md "방문자 표면 vs 운영 용어")
JARGON_ERROR = ["load-bearing", "just-in-time", "작업호", "진실원"]
# 2026-07-26: 개명 미반영 수리 — 2026-07-19에 load-bearing→밑돌로 바꿨는데 lint는 구 단어만
# 검사하고 있었다(현행 용어를 아무도 안 보던 상태). "밑돌다"(수치가 기준에 못 미침)는 정상
# 한국어라 통짜 문자열로 넣으면 오탐이 나므로 동사 활용형을 제외한 명사형만 잡는다.
JARGON_ERROR_RE = [(re.compile(r"밑돌(?![다았아어며면지게던])"), "밑돌")]
JARGON_WARN = ["마일스톤", "체크포인트", "BACKLOG", "승격"]

# 상단에 "> 상태:" 줄이 있어야 하는 가든 문서 — 오독 방지 기능이 있는 곳만
# (2026-07-12 선호 결정: 장식성 상태 줄은 제거 — 용어집·실험 랜딩·foundations 랜딩은 제외.
#  reading-list.qmd는 2026-07-22 지도에 흡수·삭제돼 목록에서 뺌)
#  2026-07-26: 기초 개념 글(논문 정독이 아니라 밑돌 개념을 세우는 글)은 읽은 범위 자체가
#  없어 상태 줄이 장식이 된다 — paper-reviews/ 안에 있어도 제외한다.
NOT_PAPER_REVIEW = {"before-attention.qmd"}

# 2026-07-26: 죽은 항목 수리 — 목록의 유일한 비-리뷰 항목이 field-map.qmd였는데 그 파일은
# 2026-07-24에 프롤로그로 흡수·삭제됐다. 존재하는 파일만 순회하는 구조라 오류로도 안 뜨고
# 검사만 조용히 꺼져 있었다. 지도를 물려받은 프롤로그로 교체한다(상태 줄 실재 확인).
# (구 목록의 "index.qmd"도 2026-07-17에 삭제된 논문 목록 페이지를 가리키던 죽은 항목.)
STATUS_REQUIRED = (
    ["experiments/2026-06-29-prologue.qmd"]
    + [str(p.relative_to(ROOT)) for p in (ROOT / "paper-reviews").glob("*.qmd")
       if p.name not in NOT_PAPER_REVIEW]
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SEP_ROW_RE = re.compile(r"^\|?[\s:\-|]+\|?$")
ANCHOR_RE = re.compile(r"\{#([A-Za-z0-9_-]+)\}")

errors, warnings, notes = [], [], []


def strip_code_fences(lines):
    """코드 펜스(```) 안 여부를 라인별 bool 리스트로 반환."""
    in_fence, flags = False, []
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            flags.append(True)
        else:
            flags.append(in_fence)
    return flags


def check_tables(path, lines, fenced):
    block, start = [], None
    def flush():
        nonlocal block, start
        if block:
            if len(block) < 2 or not SEP_ROW_RE.match(block[1].strip()):
                errors.append(f"{path}:{start} 깨진 표 블록(헤더 구분선 없음, {len(block)}줄) — 앞 표와 빈 줄로 분리됐는지 확인")
            block, start = [], None
    for i, line in enumerate(lines, 1):
        if not fenced[i - 1] and line.strip().startswith("|") and line.strip() != "|":
            if not block:
                start = i
            block.append(line)
        else:
            flush()
    flush()


def anchor_targets(path):
    """대상 파일의 명시적 {#id} + 헤딩 근사 슬러그 집합."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    ids = set(ANCHOR_RE.findall(text))
    for h in re.findall(r"^#+\s+(.+)$", text, re.M):
        h = re.sub(r"[*_`\[\]()]", "", h)
        slug = re.sub(r"[^\w\s가-힣·-]", "", h.lower()).strip()
        ids.add(re.sub(r"[\s·]+", "-", slug))
    return ids


def check_links(path, text):
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            frag, file_part = target[1:], str(path)
            resolved = path
        else:
            file_part, _, frag = target.partition("#")
            resolved = (path.parent / file_part).resolve()
            if resolved.suffix not in (".qmd", ".md"):
                continue
            if not resolved.exists():
                errors.append(f"{path} 깨진 링크: ({target}) — 대상 파일 없음")
                continue
        if frag and frag not in anchor_targets(resolved):
            warnings.append(f"{path} 앵커 미확인: ({target}) — 대상에 {{#{frag}}} 없음(헤딩 자동 앵커면 오탐일 수 있음)")


def check_jargon(path, lines, fenced):
    for i, line in enumerate(lines, 1):
        if fenced[i - 1]:
            continue
        for term in JARGON_ERROR:
            if term in line:
                errors.append(f"{path}:{i} 내부 용어 '{term}' — 방문자 표면에서는 풀어쓸 것")
        for pat, label in JARGON_ERROR_RE:
            if pat.search(line):
                errors.append(f"{path}:{i} 내부 용어 '{label}' — 방문자 표면에서는 풀어쓸 것")
        for term in JARGON_WARN:
            if term in line:
                warnings.append(f"{path}:{i} 운영 용어 '{term}' — 일지 밖 사용이 맞는지 확인")


def check_status_line(path, lines):
    rel = str(path.relative_to(ROOT))
    if rel in STATUS_REQUIRED:
        head = "\n".join(lines[:20])
        if "> 상태" not in head:
            warnings.append(f"{rel} 가든 문서인데 상단 '> 상태:' 줄이 없음")


def table_rows(text, score_header):
    """파이프 표에서 {첫 셀: 점수 셀} 추출. 헤더에서 score_header 열 위치를 찾는다."""
    rows, score_idx = {}, None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if score_header in cells:
            score_idx = cells.index(score_header)
            continue
        if score_idx is not None and cells and not set(cells[0]) <= set(":- "):
            if len(cells) > score_idx:
                rows[cells[0]] = cells[score_idx]
    return rows


# 문체 반복 상한(2026-07-18 전수 탐지에서 확정한 쿼터 — 초과는 경고, 판정은 사람이).
# 원칙(2026-07-22 확정): 형태만으로 문제인 패턴만 기계가 센다. "아니라" 쿼터는 제거 —
# 극적 대조(voice 금지)와 사실 서술(정당)을 문자열로 못 가르고, 오탐이 정당한 문장을
# 고치게 만들었다(anisotropy 항목 실측). 그 판정은 의미 층(자체 스캔·voice-check·통독) 몫.
# 2026-07-27: "연결어미쉼표" 쿼터 제거. 근거로 적혀 있던 "AI 탐지 단일 최강 지표 4.84배"의
# 출처가 어디에도 없었고(07-26 전수 추적 실패), 근거 없는 쿼터가 문장 구조를 건드리는 수정을
# 유발했다(3급은 "고쳐서 문장이 나빠지면 안 고친다"가 원칙). 근거를 확보하면 되살린다.
STYLE_QUOTA = {"대시": 12, "볼드쌍": 10, "이모지": 0}
CONJ_COMMA_RE = re.compile(r"(?:고|며|지만|는데|면서|므로),\s")
# 2026-07-26 신설: CLAUDE.md 규칙 등급이 이모지를 3급으로 내리며 "site_lint.py 쿼터로 관리"라고
# 적었는데 lint에 검사가 없어 어느 층도 안 보고 있었다. 규칙이 겨냥한 것은 성숙도 스탬프(🌱🌿🌳)
# 류의 그림 이모지이므로 그 범위만 센다 — ✕·○·△·⚠ 같은 기호는 판정 표기라 제외(프롤로그
# 8편 표에서 오탐 실측).
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF]")
# 불릿 라벨 볼드(`- **라벨**: 설명`, `- **라벨** — 설명`) — 역할 볼드(voice 규칙 ③)라 산문 볼드와 구분
LABEL_BOLD_RE = re.compile(r"^[-*+]\s+\*\*[^*]+\*\*")


def check_style(path, lines, fenced):
    """산문 줄만 세어 문체 반복(대시·볼드·연결어미 쉼표)이 쿼터를 넘으면 경고.

    인용 블록(>)·표(|)·헤딩(#)·코드 펜스는 제외 — 원문 인용과 데이터는 문체 대상이 아니다.
    불릿 라벨 구분자 등 정당한 대시가 섞여 세밀하진 않으므로 상한을 넉넉히 잡았다.
    """
    counts = {"대시": 0, "볼드쌍": 0, "이모지": 0}
    for line, in_fence in zip(lines, fenced):
        s = line.strip()
        # 이모지는 인용·표·헤딩에서도 금지라 skip 앞에서 센다(코드 펜스만 제외)
        if not in_fence:
            counts["이모지"] += len(EMOJI_RE.findall(line))
        if in_fence or s.startswith((">", "|", "#")) or not s:
            continue
        # 대시는 산문만 센다 — 불릿의 라벨 구분자(`- **라벨** — 설명`)와 서지 줄은 관례상 예외
        if not s.startswith(("-", "*", "+")):
            counts["대시"] += line.count("—")
        # 볼드는 줄 맨 앞 불릿 라벨 1개를 빼고 센다(2026-07-22) — 불릿-라벨 구조 문서가
        # 역할 준수와 무관하게 걸리던 오탐 제거(self-report 27쌍 실측)
        counts["볼드쌍"] += LABEL_BOLD_RE.sub("", s).count("**") // 2
    over = {k: v for k, v in counts.items() if v > STYLE_QUOTA[k]}
    if over:
        detail = "·".join(f"{k} {v}(상한 {STYLE_QUOTA[k]})" for k, v in over.items())
        warnings.append(f"{path}: 문체 쿼터 초과 — {detail}")


def check_kaggle_sync():
    """foundations 대회 표 ↔ kaggle README 점수 동기 (진실원 = kaggle README).

    2026-07-07 실측: S6E7 점수 0.86217이 foundations 표에 누락돼 있던 드리프트를 이 대조로 발견.
    kaggle repo가 없는 환경(예: 클론만 받은 외부)에서는 조용히 건너뛴다.
    """
    kaggle_readme = ROOT.parent / "kaggle" / "README.md"
    foundations = ROOT / "foundations" / "index.qmd"
    if not kaggle_readme.exists() or not foundations.exists():
        return
    f_rows = table_rows(foundations.read_text(encoding="utf-8"), "최고 점수")
    k_rows = table_rows(kaggle_readme.read_text(encoding="utf-8"), "최고 점수")
    # 표에 있는 대회만 점수를 대조한다. 행의 존재 자체는 요구하지 않는다 —
    # 2026-07-18 선호 결정으로 미발행 대회 행(재정비 중 류)을 표에서 내렸다.
    # 발행된 행의 점수 어긋남(07-07 S6E7 사례)은 여전히 오류로 잡힌다.
    for name, f_score in f_rows.items():
        if name in k_rows and k_rows[name] != f_score:
            errors.append(f"foundations/index.qmd '{name}' 점수 '{f_score}' ≠ kaggle README '{k_rows[name]}' (진실원=kaggle README)")


# 글자수 문턱은 2026-07-18에 폐지했다. 같은 날 실측으로 해가 확인됐다 —
# 430자를 맞추려다 cross-entropy의 출처("정보이론에서 왔다"), 정렬이 다양성을
# 줄이는 메커니즘("cross-entropy와 방향이 반대라"), 온도 항목의 오해 교정
# 대비("창의성이 아니라")가 지워졌고, 회귀분석 항목은 종결어미가 잘려 나갔다.
# 규칙이 지키려던 것(용어집은 사전이지 리뷰가 아니다)은 아래 '문단 2개' 규칙이
# 직접 강제한다. 길이는 판정하지 않고 아래 report_glossary_lengths가 보여주기만 한다.
GLOSSARY_REPORT_TOP = 5  # 참고 출력할 최장 항목 수
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def visible_len(text):
    """마크다운 링크의 URL을 뺀 길이 — 독자가 실제로 읽는 분량.

    2026-07-18 교체 이유: 원문 글자수를 세면 URL이 22~132자를 차지해
    인용을 성실히 단 항목일수록 장황 판정을 받았다(cross-entropy는 측정값의 27%가 URL).
    규칙 의도가 '읽기에 장황한가'이므로 표시 텍스트만 센다.
    """
    return len(MD_LINK_RE.sub(r"\1", text))


def check_glossary():
    """용어집 구조 규칙(2026-07-12 개편) — 골격·중복·장황을 기계로 감시.

    - #### 헤딩엔 {#앵커} 필수, 파일 내 앵커 중복 금지(07-10 창발 중복 실측 클래스)
    - 항목 본문 = 문단 2개(한 줄 정의 + 설명 문단 1개) — 초과는 경고
    - 길이는 판정하지 않고 최장 항목만 참고 출력 (2026-07-18 문턱 폐지)
    """
    glossary = ROOT / "glossary.qmd"
    if not glossary.exists():
        return
    lines = glossary.read_text(encoding="utf-8").splitlines()
    seen, entries, current = {}, [], None
    for i, line in enumerate(lines, 1):
        if line.startswith("#### "):
            m = ANCHOR_RE.search(line)
            if not m:
                errors.append(f"glossary.qmd:{i} 항목 헤딩에 {{#앵커}} 없음")
            else:
                anchor = m.group(1)
                if anchor in seen:
                    errors.append(f"glossary.qmd:{i} 앵커 중복 {{#{anchor}}} — {seen[anchor]}줄과 충돌")
                seen[anchor] = i
            current = (i, [])
            entries.append(current)
        elif line.startswith(("## ", "### ")):
            current = None
        elif current is not None:
            current[1].append(line)
    lengths = []
    for i, body in entries:
        paras = [p for p in "\n".join(body).split("\n\n") if p.strip()]
        if len(paras) > 2:
            warnings.append(f"glossary.qmd:{i} 항목 문단 {len(paras)}개 — 골격은 '한 줄 정의 + 설명 문단 1개'")
        lengths.append((sum(visible_len(p) for p in paras), i))

    # 판정이 아니라 참고 — 비대해지면 눈에 띄되 문장을 깎으라는 압박은 주지 않는다.
    for n, i in sorted(lengths, reverse=True)[:GLOSSARY_REPORT_TOP]:
        notes.append(f"glossary.qmd:{i} {n}자")


def main():
    for path in PUBLIC_FILES:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        fenced = strip_code_fences(lines)
        check_tables(path.relative_to(ROOT), lines, fenced)
        check_links(path, text)
        check_jargon(path.relative_to(ROOT), lines, fenced)
        check_status_line(path, lines)
        check_style(path.relative_to(ROOT), lines, fenced)

    check_kaggle_sync()
    check_glossary()

    for e in errors:
        print(f"[오류] {e}")
    for w in warnings:
        print(f"[경고] {w}")
    if notes:
        print("\n참고 — 용어집 최장 항목(판정 아님):")
        for n in notes:
            print(f"  {n}")
    print(f"\n검사 파일 {len(PUBLIC_FILES)}개 · 오류 {len(errors)} · 경고 {len(warnings)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
