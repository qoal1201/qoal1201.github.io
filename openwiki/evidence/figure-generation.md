---
type: Reference
title: 그림 생성
description: 사이트의 모든 그림은 스크립트에서 나온다 — 공용 스타일, 실행 방법, 그리고 그 규약 밖에 있는 한 개.
tags: [matplotlib, svg, 그림]
sources:
  - id: openwiki-source-da6cd023562f21143ce4b486
    resource: repo://_tools/figures/figstyle.py
  - id: openwiki-source-347fbda46c07ac0e9c8946f6
    resource: repo://_tools/figures/schelling_figs.py
  - id: openwiki-source-9e494d04ca48fe0a6140cd54
    resource: repo://_tools/figures/transformer_figs.py
  - id: openwiki-source-171115258e1d145ceff5501d
    resource: repo://_tools/figures/wang_figs.py
  - id: openwiki-source-0e1f3b45819028e3584bc0dc
    resource: repo://_tools/make_field_map_charts.py
generated: {by: "claude-code", at: "2026-08-23T16:52:46.407Z"}
---

# 원칙

**논문 Figure 를 그대로 복사하지 않는다.** 이해한 구조를 다시 그린 재구성만 싣는다.
저작권 문제이기도 하고, 다시 그릴 수 있다는 것 자체가 이해의 증거이기도 하다.

그리고 **생성 스크립트를 레포에 보관한다.** 그림이 어디서 나왔는지 물으면 답이
파일로 있어야 한다.

# 공용 스타일

`_tools/figures/figstyle.py` 가 사이트 차트 규칙을 코드로 굳힌 것이다.

| | 값 | 뜻 |
|---|---|---|
| 청록 | `#0F87A8` | 강조 대상 — 이 연구, 측정의 주인공 |
| 적색 | `#C4443C` | 갭·경고·빈자리 |
| 나머지 | 회색 계열 | 배경 |

라벨은 전부 한국어이고 폰트는 사이트 본문과 같은 Pretendard 다.

★ **SVG 는 글자를 path 로 구워 저장한다**(`svg.fonttype: path`). 방문자 기기에 그
폰트가 없어도 같게 보이게 하려는 것 — 웹폰트 로딩에 그림의 정확성을 의존시키지 않는다.

⚠ **그런데 그 굽기가 반대편에서는 위험이 된다.** 폰트 지정에 **대체 목록이 없다.**
그리는 기계에 그 폰트가 없으면 matplotlib 은 조용히 다른 글꼴로 대체하고, **path 로
굽는 단계가 그 대체를 산출물에 영구히 박는다.** 커밋된 SVG 안에서는 더 이상 글자가
아니라 곡선이라 **방문자 쪽에서 고칠 방법이 없다.**

정리하면 이 레포는 폰트에 대해 **두 개의 다른 가정**을 하고 있다.

| 어디 | 언제 필요한가 | 없으면 |
|---|---|---|
| 그림 생성 | **그리는 기계**에서, 굽는 시점에 | 산출물에 영구히 박힌다 |
| 사이트 본문 | **방문자 브라우저**에서, 보는 시점에 | 웹폰트를 받아서 해결된다 |

앞쪽이 되돌릴 수 없는 쪽이다.

★ **저장은 흰 배경을 명시한다.** 투명하게 두면 다크 테마에서 잉크가 배경에 묻히므로,
흰 바탕을 깔아 **카드처럼 읽히게** 한다.

사용은 두 줄이다.

```python
import figstyle
figstyle.apply()
# ... 그린 다음
figstyle.save(fig, "이름")   # → images/이름.svg
```

# 실행

각 스크립트가 **자기 의존성을 PEP 723 헤더로 든다.**

```bash
uv run _tools/figures/wang_figs.py
```

프로젝트 환경이 필요 없다는 뜻이다. 이 레포에 루트 의존성 매니페스트가 없는 것과
같은 방향의 선택이다.

# 그림은 본문이 이미 말한 것만 그린다

스크립트 docstring 이 **어느 수치를 어디서 가져왔는지** 적는다. 그리고 수치가 없는
모식도는 **모식도라고 명시한다** — 예컨대 배치가 그림용 배열이지 논문의 실제 초기
배열이 아니라는 것, 점 위치가 데이터가 아니라는 것을 스크립트가 직접 밝힌다.

이 관례가 규칙을 실행 가능하게 만든다. 그림에 새 주장이 들어가면 그 주장의 출처를
docstring 에 못 적게 되므로, **적을 수 없으면 그리지 않는다.**

지금 있는 스크립트는 여섯이고 각각 한 편의 공부글에 붙는다 — 밑돌 글, 트랜스포머,
GA 리뷰, Schelling, self-report, wang.

# 규약 밖에 있는 하나

⚠ `_tools/make_field_map_charts.py` 는 `figures/` 관례를 안 따른다. 공용 스타일을
import 하지 않고 **팔레트와 폰트를 그 파일 안에서 다시 선언하며**, SVG 가 아니라
PNG 두 장을 뽑는다. 실행도 `uv run` 이 아니라 venv 파이썬을 직접 부른다.

그리고 **docstring 이 지금 없는 파일을 가리킨다** — 첫 줄이 `field-map.qmd` 차트
생성기라고 선언하는데 그 파일은 프롤로그에 흡수돼 사라졌다. 그림 자체는 살아 있고
프롤로그가 쓰고 있다. 데이터 출처도 그 죽은 파일의 절 번호로 적혀 있어, 지금 지도를
갱신하려면 그 서술이 어디로 옮겨갔는지를 먼저 찾아야 한다.
