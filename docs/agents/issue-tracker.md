# Issue tracker: GitHub

이 레포의 이슈·스펙은 `qoal1201/qoal1201.github.io` 의 GitHub 이슈로 산다.
모든 조작은 `gh` CLI — 클론 안에서 실행하면 `git remote -v` 로 레포를 알아서 찾는다.

> 2026-08-20 선택. 로컬 마크다운이 아닌 이유: 뿌리(`qoal1201/brain`)가 레포 간 왕래를
> **GitHub 크로스 레포 이슈 참조**로 확정했는데(`qoal1201/brain#4`), 이 레포만 그 배선에서
> 빠져 있었다 — 채택 시점 실측으로 **이 레포 이슈는 open 0 · closed 0** 이었다.

## ★ 이 레포는 공개다 — 이슈도 공개된다

`qoal1201/qoal1201.github.io` 는 public 이므로 **이슈 제목·본문·라벨이 전부 공개**된다.
그래서 무엇을 이슈로 올리고 무엇을 안 올리는지가 갈린다:

| 무엇 | 어디 |
|---|---|
| 공부·실험·발행 작업 티켓 | **GitHub 이슈** |
| 개인 맥락 (취업·사업·전략) | **이슈로 안 올린다** — 루트 `AGENTS.md` 규칙 그대로 |
| 이 레포에서 닫히는 결정 | **`docs/adr/`** — 다시 열 조건을 반드시 적는다 |
| 발동 조건이 붙은 규칙 (*"X 하면 Y 한다"*) | **에이전트 기억** — 비공개 · 레포별 · 자동 회수 |
| 박선호가 골라야 움직이는 것 | **조율 레포 이슈** (아래 참조) |

**2026-08-22 확정 — 「다음에 뭘 하나」의 진실원은 하나다.** 전에는 git 이 추적하지 않는
`BACKLOG.local.md` 가 그 자리였고 이슈와 갈렸다. 그 파일은 없앴다.

판정선은 **「박선호가 골라야 움직이나」** 다. 그렇다면 조율 레포로 올린다 — 결재 대기를
두 곳에 나누면 그가 두 곳을 봐야 하고, 그러면 「사람을 한 번만 세운다」가 무너진다.
아니라면 이 레포에 남는다. **공개 가부는 「어디에 두나」의 기준이지 「누가 결정을 기다리나」의
기준이 아니다.**

## 레포를 건너뛰는 것은 여기 안 산다

이 레포 밖에 걸리는 결정은 뿌리 이슈에 산다. 참조는 맨 텍스트로 qoal1201/brain#N 처럼 쓴다.

⚠ **백틱으로 감싸면 GitHub 이 교차참조로 안 읽어 백링크가 안 생긴다** (2026-08-16 실측).
사실은 그 레포가 진실원이고 결정은 뿌리가 갖는다.

## 관례

- **이슈 만들기**: `gh issue create --title "..." --body "..."` (여러 줄 본문은 heredoc)
- **이슈 읽기**: `gh issue view <번호> --comments`
- **목록**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`
- **코멘트**: `gh issue comment <번호> --body "..."`
- **라벨**: `gh issue edit <번호> --add-label "..."` / `--remove-label "..."`
- **닫기**: `gh issue close <번호> --comment "..."`

## Pull requests as a triage surface

**PRs as a request surface: no.** _(이 레포가 외부 PR 을 기능 요청으로 다루면 `yes` 로 바꾼다. `/triage` 가 이 플래그를 읽는다.)_

GitHub 은 이슈와 PR 이 번호 공간을 공유하므로 맨 `#42` 는 둘 중 하나일 수 있다 —
`gh pr view 42` 로 확인하고 안 되면 `gh issue view 42` 로 떨어진다.

## 스킬이 "이슈 트래커에 발행하라" 고 하면

GitHub 이슈를 만든다.

## 스킬이 "관련 티켓을 가져오라" 고 하면

`gh issue view <번호> --comments` 를 돌린다.

## Wayfinding operations

`/wayfinder` 가 쓴다. **지도**는 이슈 하나이고 **자식** 이슈가 티켓이다.

- **지도**: `wayfinder:map` 라벨이 붙은 이슈 하나. Notes / Decisions-so-far / Fog 를 본문에 든다
- **자식 티켓**: 지도에 sub-issue 로 연결. 안 되면 지도 본문 task list + 자식 본문 맨 위에 `Part of #<지도>`. 라벨 = `wayfinder:<종류>` (`research`/`prototype`/`grilling`/`task`)
- **블로킹**: GitHub 네이티브 issue dependencies. `gh api --method POST repos/<owner>/<repo>/issues/<자식>/dependencies/blocked_by -F issue_id=<블로커의 DB id>` — DB id 는 `gh api repos/<owner>/<repo>/issues/<n> --jq .id` (번호나 node_id 아님). 안 되면 자식 본문 맨 위 `Blocked by: #<n>` 줄로 대체
- **프론티어 질의**: 지도의 열린 자식 중 열린 블로커·담당자 없는 것, 지도 순서로 첫 번째
- **잡기**: `gh issue edit <n> --add-assignee @me` — 세션의 첫 쓰기
- **해소**: `gh issue comment <n>` → `gh issue close <n>` → 지도 Decisions-so-far 에 포인터 추가

⚠ 실측 2026-08-20: 이 레포엔 `wayfinder:*` 라벨이 아직 없다. 첫 지도를 깔 때 만든다.
