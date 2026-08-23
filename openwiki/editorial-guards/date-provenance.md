---
type: Reference
title: 날짜 파생
description: 리뷰의 최종 갱신일을 손으로 관리하지 않고 git 이 아는 사실에서 뽑아내는 스크립트.
tags: [frontmatter, git, 발행]
sources:
  - id: openwiki-source-60a032f4951899a021c9850f
    resource: repo://_tools/sync_dates.py
  - id: openwiki-source-baf30c604828cfde90a8ab63
    resource: repo://.githooks/pre-push
  - id: openwiki-source-f2608d0d515da097485b6ec5
    resource: repo://.github/workflows/publish.yml
generated: {by: "claude-code", at: "2026-08-23T16:52:46.407Z"}
verified:
  - by: openwiki/0.3.3
    at: 2026-08-23T16:52:46.407Z
---

# 왜 파생시키나

리뷰는 발행 뒤에도 계속 자라는 문서다. 상단에 공개일만 찍혀 있으면 "그날 만들고
끝"으로 읽히므로 최종 갱신일을 함께 표시하는데, **그 값을 손으로 관리하면 반드시
어긋난다.** `_tools/sync_dates.py` 는 그래서 `date-modified` 를 쓰지 않고 **git 에서
계산한다.**

대상은 `paper-reviews/*.qmd` 와 `experiments/2*.qmd` 다. 실험 글의 glob 이 숫자로
시작하는 것만 잡는 것은 날짜 접두어를 가진 실험 글만 대상으로 삼기 위해서다.

# 판정 규칙

```
작업 트리에 내용 변경이 있다  →  date-modified = 오늘
그 외                        →  date-modified = 내용이 실제로 바뀐 마지막 커밋일
계산값 ≤ 공개일              →  date-modified 를 아예 지운다
```

마지막 줄이 규칙의 성격을 정한다 — **만들고 안 고친 글에는 갱신일이 붙지 않는다.**
갱신일은 "이 문서가 얼마나 자랐나" 를 나르는 정보이지 도장이 아니다.

# 두 개의 재귀 함정

이 스크립트의 어려움은 전부 **자기가 쓴 값을 자기가 다시 읽는다**는 데서 온다.

★ **함정 1 — 메타 줄만 바뀐 커밋을 내용 변경으로 세면 날짜가 영원히 밀린다.**
`diff_has_content` 는 diff 에서 `date:` 와 `date-modified:` 로 시작하는 줄을 빼고
남는 것이 있는지 본다. 이 제외가 없으면 스크립트가 어제 쓴 갱신일이 오늘 실행의
갱신 근거가 되고, 아무도 글을 안 고쳐도 날짜가 매일 하루씩 올라간다. 첫 실행에서
리뷰 일곱 편이 실제로 그렇게 밀릴 뻔했다고 코드가 기록한다.

★ **함정 2 — 생성 커밋을 갱신으로 세면 모든 글이 갱신된 것이 된다.**
`last_content_commit_date` 는 `--diff-filter=A` 로 생성 커밋을 먼저 찾아두고,
로그를 훑다가 그 커밋에 닿으면 멈춘다. 안 그러면 파일이 처음 만들어진 커밋이
"내용이 바뀐 커밋" 으로 잡혀 모든 글에 갱신일이 붙는다.

# git status 를 손으로 자르지 않는다

`dirty_paths` 는 `git status --porcelain` 이 아니라 `git diff --name-only HEAD` 를
쓴다. 이유가 주석에 실측으로 남아 있다 — 출력 전체에 `strip` 을 걸면 첫 줄의
상태 컬럼 앞 공백이 사라져 **첫 항목만 한 글자씩 밀렸고**, 그래서 바뀐 파일을
놓치고 "전부 최신" 이라고 답했다. `--name-only` 는 경로만 내보내므로 자를 것이 없다.

# 두 가지 모드

| 실행 | 파일 | 종료 코드 |
|---|---|---|
| `python3 _tools/sync_dates.py` | 고친다 | 항상 `0` |
| `python3 _tools/sync_dates.py --check` | 안 고친다 | 고칠 것이 있으면 `1` |

`--check` 가 게이트용이다. 다만 **[푸시 게이트](push-gate.md)도 발행 워크플로도 이
스크립트를 부르지 않는다** — 훅이 돌리는 것은 사이트 린트와 번들 검사 둘뿐이고, CI 는
렌더만 한다. 날짜 파생은 **커밋 직전 사람이 돌리는 절차**로 남아 있고, 안 돌리면
낡거나 지워진 갱신일이 **완전히 초록인 push 를 타고 그대로 배포된다.**

# ⚠ git 이 실패하면 날짜가 지워진다

`git()` 헬퍼는 `subprocess.run` 을 `check=True` 없이 부르고 **stderr 를 버린다.**
그래서 어떤 이유로든 git 호출이 실패하면 빈 문자열이 돌아온다.

그 빈 문자열이 흐르는 경로가 문제다:

```
git 실패 → last_content_commit_date 가 "" 반환
        → wanted = published
        → wanted <= published 이므로 wanted = None
        → date-modified 를 지운다
```

**오류로 멈추는 대신 대상 문서 전체에서 갱신일을 걷어낸다.** 얕은 클론, 레포 밖 실행,
읽을 수 없는 오브젝트가 전부 같은 결과를 낸다. 화면에는 `[갱신] … → 없음` 이 줄줄이
찍히는데, 그것이 "안 고친 글이라 갱신일이 없다" 인지 "git 이 죽었다" 인지 출력만으로는
구분되지 않는다.

# 무엇이 화면에 나오나

이 스크립트가 쓰는 값이 실제로 방문자에게 보이는지는 `styles.css` 에 걸려 있다.
날짜 블록이 한동안 숨겨져 있었고, 그 기간에 `date-modified` 는 HTML 안에만 있고
화면에는 없었다 — 그렇게 배포된 뒤 눈으로 보고 발견했다는 기록이 그 파일 주석에
남아 있다. 파생이 맞다고 표시가 맞는 것은 아니다.

# 확인

```bash
python3 _tools/sync_dates.py --check
```
