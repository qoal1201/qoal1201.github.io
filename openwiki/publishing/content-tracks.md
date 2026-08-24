---
type: Architecture Guide
title: 콘텐츠 갈래
description: 발행되는 네 표면과 그것들을 가르는 것 — 주제가 아니라 콘텐츠 모델이다.
tags: [발행, 템플릿, frontmatter]
sources:
  - id: openwiki-source-dbf2cf18086874042a43414d
    resource: repo://_templates/experiment.qmd
  - id: openwiki-source-cc865c3d0a2509ac4d8fb860
    resource: repo://_templates/paper-review.qmd
  - id: openwiki-source-bc60e82edfcbb78d15686df2
    resource: repo://_templates/reproduction-skeleton/README.qmd
  - id: openwiki-source-450f926f2517c086e4b25858
    resource: repo://_templates/reproduction-skeleton/requirements.txt
  - id: openwiki-source-39c3295efc089133e87a9c80
    resource: repo://CONTEXT.md
  - id: openwiki-source-3c3344b05d15d84c3572521c
    resource: repo://foundations/index.qmd
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: {by: "claude-code", at: "2026-08-23T16:52:46.407Z"}
---

# 갈래를 가르는 축은 주제가 아니다

| 갈래 | 콘텐츠 모델 | 무엇 |
|---|---|---|
| `paper-reviews/` | 가든 | 논문 하나 또는 기초 개념 하나를 이해시키는 글 |
| `experiments/` | 타임라인 | 실험 하나의 진행 기록 |
| `foundations/` | 랜딩은 가든, 대회 글은 타임라인 | 캐글 대회 하나 = 노트북 하나 |
| `glossary.qmd` | 가든 | [별도 페이지](glossary.md)가 갖는다 |

★ **가든과 타임라인의 차이가 편집 권한을 정한다.** 가든은 계속 자라고 다시 손질하며
**궤적은 문서가 아니라 git 이 보존한다.** 타임라인은 날짜 절이 쌓이고 **닫힌 뒤에는
고치지 않는다** — 서식 재배치와 제목의 상태 표시만 소급으로 허용된다.

그래서 "이 글을 고쳐도 되나" 의 답은 글의 나이가 아니라 갈래에서 나온다.

# 템플릿은 복사할 문자열이 아니다

`_templates/paper-review.qmd` 는 스스로를 **골격 가이드**라고 선언하고, 절 제목은 그
논문 내용으로 지으라고 한다. 그 안에 절 순서의 원리가 박혀 있다 —
**논문 목차가 아니라 이해의 순서.** 문제 → 핵심 아이디어 하나 → 전체 그림 → 그림의
칸 채우기 → 증거 → 지금 우리와의 관계.

논문 종류마다 골격이 갈린다는 것도 템플릿이 든다. 아키텍처 논문은 부품 조립이 축이고,
측정 논문은 조작화가 들어오고, 이론·포지션 논문은 부품이 없으니 억지 조립 절을 만들지
않는다.

`_templates/experiment.qmd` 는 훨씬 짧다 — 무엇을 측정하나 한 줄, 설계, `# YYYY-MM-DD`
날짜 절, 결과·배운 것.

# 날짜 계약

리뷰와 실험 글의 frontmatter 는 `date` 를 갖고, 그 아래 `date-modified` 가 **자동으로
붙거나 지워진다.** 손으로 관리하는 값이 아니다 — 규칙과 함정은
[날짜 파생](../editorial-guards/date-provenance.md)이 갖는다.

# foundations 는 다시 실행되지 않는다

노트북은 **저장된 실행 결과 그대로** 렌더된다. 빌드가 셀을 다시 돌리지 않는다.
이유는 성능이 아니라 데이터다 — **캐글 대회 CSV 는 재배포 규정상 레포에 없다.**
그래서 재실행할 입력 자체가 없다.

대회 표의 점수는 이 레포가 진실원이 아니다. 이웃 레포 README 가 갖고, 그 대조는
[레포 밖 경계](../governance/cross-repo-boundaries.md)가 다룬다.

# 재현 골격은 이 레포의 의존성이 아니다

⚠ `_templates/reproduction-skeleton/` 안에 `requirements.txt` 가 있다. **이것은 이
레포가 설치하는 목록이 아니라** 앞으로 만들 재현 조각이 복사해 갈 뼈대다.

**이 레포의 루트에는 의존성 매니페스트가 없다.** `package.json` · `pyproject.toml` ·
`requirements.txt` 어느 것도 없고, 검사 스크립트는 표준 라이브러리만 쓰며 그림
스크립트는 각자 PEP 723 헤더로 의존성을 든다. 레포를 매니페스트로 파악하려 하면
아무것도 안 나온다.

# 초안

논문 공부글 절반이 지금 `draft: true` 다. 어느 글이고 그것이 발행과 검사에 각각
무슨 뜻인지는 [사이트 빌드](site-build.md)의 초안 절이 갖는다.
