---
type: Architecture Guide
title: 사이트 빌드
description: Quarto 프로젝트가 무엇을 렌더하고 무엇을 안 하나, 그리고 푸시 하나가 배포가 되기까지.
tags: [quarto, github-pages, 배포]
sources:
  - id: openwiki-source-1102dfe98fc8c998310bb47d
    resource: repo://_quarto.yml
  - id: openwiki-source-bfa3b84a318d5325e014eaad
    resource: repo://_tools/site_lint.py
  - id: openwiki-source-f2608d0d515da097485b6ec5
    resource: repo://.github/workflows/publish.yml
  - id: openwiki-source-85f817e5fee8ed575e45161c
    resource: repo://experiments/2026-06-29-prologue.qmd
  - id: openwiki-source-e847f70bab9d2c3888719b34
    resource: repo://foundations/_metadata.yml
  - id: openwiki-source-3c3344b05d15d84c3572521c
    resource: repo://foundations/index.qmd
  - id: openwiki-source-ce63e315e005b8d86575e057
    resource: repo://index.qmd
  - id: openwiki-source-75657e714e770cb814abf9a3
    resource: repo://paper-reviews/2304.03442-generative-agents.qmd
  - id: openwiki-source-078fe8e4e71b975dcb3af5f5
    resource: repo://paper-reviews/schelling-1971-segregation.qmd
  - id: openwiki-source-a4eddade3476647fc13eb107
    resource: repo://theme-dark.scss
  - id: openwiki-source-0d03ca4ee492648d4b88bae3
    resource: repo://theme-light.scss
generated: {by: "claude-code", at: "2026-08-23T16:52:46.407Z"}
verified:
  - by: openwiki/0.3.3
    at: 2026-08-23T16:52:46.407Z
---

# 렌더 대상은 명시 목록이다

`_quarto.yml` 의 `render` 는 트리 전체가 아니라 **다섯 항목**을 든다 — `index.qmd`,
`glossary.qmd`, 그리고 `experiments/` · `paper-reviews/` · `foundations/` 세 디렉터리.

여기서 나오는 규칙이 하나 있다. **루트에 새 페이지를 만들면 이 목록에 넣기 전까지
발행되지 않는다.** 반대로 세 디렉터리 안에 만든 파일은 자동으로 잡힌다.

⚠ [사이트 린트](../editorial-guards/site-lint.md)의 검사 대상은 이 목록을 **읽지 않고**
같은 구조를 glob 으로 재현한다. 지금은 우연히 일치하고, 렌더 목록이 바뀌면 둘이 갈린다.

# 초안 처리

`_quarto.yml` 에 `drafts` 나 `draft-mode` 키가 **없다.** 그래서 Quarto 기본 동작이
그대로 적용되는데, 실제로 초안 표시가 붙은 글이 적지 않다 — **논문 공부글 10편 중
5편이 frontmatter 에 `draft: true` 를 달고 있다**(`2502.15800-llm-traders`,
`2506.19806-simulations-boundary`, `2602.15785-validating-llm-simulations`,
`anderson-1972-more-is-different`, `schelling-1971-segregation`).

★ **그 기본 동작이 무엇인지는 실측했다.** `_site` 를 지우고 전체를 다시 렌더한 결과
(Quarto 1.9.38):

| | 결과 |
|---|---|
| 초안 5편이 `_site` 에 렌더되나 | **전부 렌더된다** — URL 이 살아 있다 |
| 홈 목록에 나오나 | **하나도 안 나온다** (비초안은 전부 나온다) |

즉 **`draft: true` 는 발행 여부가 아니라 발견 가능성을 정한다.** 초안 글도 배포되고
주소로 열리지만 **사이트의 유일한 목록에서 빠진다.** 지금 논문 공부글 절반이 그 상태다 —
직접 링크나 리다이렉트로만 닿는다.

⚠ **초안이어도 린트는 검사한다.** 린트의 파일 집합은 frontmatter 를 안 보기 때문에,
초안 글의 죽은 링크나 내부 용어 노출도 그대로 push 를 막고, **상태 줄 요구도 똑같이
적용된다**(초안도 `paper-reviews/*.qmd` glob 안에 있다).

그래서 결론이 하나 나온다 — **린트가 초록인 것은 그 글이 홈에서 닿는다는 뜻이 전혀
아니다.** 두 층은 서로를 안 본다.

⚠ **발행 상태를 정하는 표면이 셋인데 서로를 검사하지 않는다** — 글의 `draft` 플래그,
`_quarto.yml` 의 렌더 목록, `index.qmd` 의 목록 glob. **초안 플래그가 의도와 맞는지
확인하는 검사는 없다.** 한 줄을 지우거나 더하는 것으로 사이트의 유일한 목차가 조용히
바뀐다.

# 구 주소 계약

★ **legacy URL 열 개가 `aliases` 로 살아 있고, 네 페이지에 흩어져 있다.**

| 어디 | 몇 개 | 무엇을 흡수했나 |
|---|---|---|
| `index.qmd` | 3 | 논문 목록·실험 목록·열린 질문 페이지 |
| `experiments/2026-06-29-prologue.qmd` | 5 | 일지 2편·분야 지도·gap8 리뷰·읽기 목록 |
| `paper-reviews/2304.03442-generative-agents.qmd` | 1 | 클로니 대조 페이지 |
| `foundations/index.qmd` | 1 | 타이타닉 페이지 |

여기서 나오는 운영 규칙: **발행된 페이지를 지우거나 다른 글에 흡수시킬 때는 그 페이지의
`aliases` 를 흡수한 쪽으로 옮긴다.** 안 옮기면 밖에서 걸린 링크가 그날로 죽는다.

`실측`: 별칭은 **구 경로에 리다이렉트 파일로 생성된다.** 깨끗한 빌드에서도 사라진
페이지들의 주소에 산출물이 만들어진다 — 소스가 없어도 **살아남은 페이지가 그 별칭을
들고 있는 한** 주소가 계속 응답한다는 뜻이다.

⚠ 이 계약이 문서보다 오래 산다는 증거가 지금 레포에 있다. `README.md` 는 아직
`field-map.qmd` 를 최상위 파일로 소개하는데 그 파일은 프롤로그에 흡수돼 사라졌고,
**리다이렉트만 남아 주소를 지키고 있다.** `_tools/make_field_map_charts.py` 의 머리말도
같은 죽은 이름을 가리킨다.

# 푸시에서 배포까지

`.github/workflows/publish.yml` 이 `main` 푸시와 수동 실행에 반응한다. 빌드 잡이
`quarto render` 로 `_site` 를 만들어 Pages 아티팩트로 올리고, 배포 잡이 그것을 올린다.

권한은 `contents: read` · `pages: write` · `id-token: write` 로 좁혀져 있다. 동시성은
`pages` 그룹에 `cancel-in-progress: true` 라, **연달아 푸시하면 앞 배포가 취소되고
뒤 배포가 이긴다.** 큐에 쌓이지 않는다.

`_site` 는 `.gitignore` 안이다 — 배포되는 산출물이 레포에 들어오지 않는다.

# 홈은 생성된 목록이다

`index.qmd` 는 손으로 관리하는 목차가 아니라 `paper-reviews/*.qmd` 와
`experiments/2*.qmd` 를 날짜 역순으로 나열하는 **listing** 이다. 실험 글 glob 이 숫자로
시작하는 것만 잡아 `experiments/index` 류를 배제한다.

그래서 **홈의 순서는 frontmatter 날짜의 결과**이고, 순서를 바꾸려면 날짜를 바꿔야 한다.
그 날짜가 어떻게 정해지는지는 [날짜 파생](../editorial-guards/date-provenance.md)이 갖는다.

# 테마

라이트/다크 SCSS 한 쌍이 flatly·darkly 위에 얹힌다. 손댄 것은 셋뿐이다 — 본문 글자
크기 17px(한국어 가독), navbar 를 흰 배경 + 얇은 경계선으로, 링크 색을 사이트 차트
강조색과 같은 청록으로. **다크의 링크 색은 같은 청록을 어두운 배경용으로 밝힌 값**이라
두 테마가 같은 색을 쓴다.

`styles.css` 는 Pretendard 웹폰트와 행간, 그리고 좁은 화면에서 **넓은 표를 페이지가
아니라 표 안에서 가로 스크롤**시키는 규칙을 담는다. Quarto 가 표를 스크롤 컨테이너로
감싸지 않아 표가 본문 폭을 뚫으면 페이지 전체가 흔들리기 때문이다.

# 디렉터리 단위 설정

`foundations/_metadata.yml` 이 그 폴더에만 `code-fold: true` 를 건다. 전역이 아니다 —
노트북 코드는 접히고 공부글·실험 글의 코드는 그대로 보인다. 독자가 서사를 먼저 읽고
확인하고 싶을 때 펼치라는 배치다.

# 확인

```bash
quarto render
```

⚠ 파일을 여럿 지정해 렌더하면 한 HTML 로 합쳐진다. 전체를 돌리거나 한 파일씩 돌린다.
