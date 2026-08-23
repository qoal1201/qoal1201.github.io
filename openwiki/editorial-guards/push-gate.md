---
type: Operations Guide
title: 푸시 게이트
description: 검사 둘이 스크립트가 아니라 집행이 되는 유일한 자리, 그리고 그 자리가 조용히 꺼지는 세 경로.
tags: [git-hooks, 게이트, 검사]
sources:
  - id: openwiki-source-baf30c604828cfde90a8ab63
    resource: repo://.githooks/pre-push
  - id: openwiki-source-130d0b3286cb5b6fb515aab0
    resource: repo://docs/adr/0002-knowledge-bundle-scope-and-gate.md
generated: {by: "claude-code", at: "2026-08-23T16:52:46.407Z"}
verified:
  - by: openwiki/0.3.3
    at: 2026-08-23T16:52:46.407Z
---

# 무엇이 여기서 결정되나

`_tools/site_lint.py` 와 `tests/check_knowledge_bundle.py` 는 그 자체로는 그냥
실행하면 결과를 찍는 스크립트다. **둘을 집행으로 바꾸는 자리는 `.githooks/pre-push`
하나뿐이다.** 훅은 `git rev-parse --show-toplevel` 로 레포 루트를 잡아 그리로 이동한
뒤 두 검사를 차례로 돌리고, 어느 하나라도 0 이 아닌 코드로 끝나면 push 를 중단한다.

그래서 "검사가 있다" 와 "검사가 돈다" 를 가르는 것은 검사 파일이 아니라 이 훅이고,
아래 두 절이 그 둘이 갈라지는 지점을 다룬다.

# 무엇을 막고 무엇을 통과시키나

**오류는 막고 경고는 통과시킨다.** 이건 느슨함이 아니라 편집 규칙과의 정합이다.
이 레포의 3급 표현 규칙은 *"고쳐서 문장이 나빠지면 안 고친다"* 인데, 문체 쿼터가
push 를 막으면 그 규칙과 정면으로 부딪힌다 — 막힌 사람은 문장을 나쁘게 고쳐서라도
통과시키게 된다. 훅 주석이 그 판단을 직접 적어두고 있다.

`site_lint.py` 쪽에서 실제로 막히는 것은 깨진 표 블록, 죽은 내부 링크, 방문자
표면에 노출된 내부 용어, `foundations/` 점수와 이웃 레포 README 의 불일치,
용어집 앵커 누락·중복이다. 통과하는 것은 상태 줄 누락, 문체 쿼터 초과, 앵커
미확인, 용어집 문단 골격이다. 검사별 상세는
[사이트 린트](site-lint.md)가 갖는다.

지식 번들 검사는 [번들 적합성 검사기](../knowledge-bundle/conformance-checker.md)가
다룬다. 그 검사가 발행 워크플로가 아니라 여기 걸려 있는 이유는 **`knowledge/` 가
발행되지 않기 때문이다.** 개념 카드 하나가 깨졌다고 사이트 배포가 멈추면 결합이
틀린 것이고, 그 판단은 [ADR 0002](../governance/decision-records.md) 가 기록한다.

# 이 게이트가 꺼지는 세 경로

★ **훅은 세 자리에서 열린 채로 실패한다(fail open).**

| 조건 | 훅의 행동 |
|---|---|
| `_tools/site_lint.py` 가 없다 | 메시지를 찍고 **`exit 0`** — push 통과 |
| `python3` 을 못 찾는다 | 메시지를 찍고 **`exit 0`** — push 통과 |
| `tests/check_knowledge_bundle.py` 가 없다 | **메시지도 없이** 그 블록을 건너뛴다 |

셋째가 앞의 둘과 다르다. 번들 검사는 존재 확인(`if [ -f … ]`) 안에 들어 있어서
**파일이 없으면 아무 말도 없이 통째로 빠진다.** 앞의 둘은 최소한 건너뛴다고 찍는다.

인터프리터 탐색은 `command -v python3` → `/opt/homebrew/bin/python3` →
`/usr/bin/python3` 순서로 내려가고, 셋 다 실패하면 검사 없이 통과한다. 즉
**전제 조건이 빠지면 게이트는 빨개지는 대신 사라진다.** 통과한 push 가 검사를
통과한 것인지 검사를 건너뛴 것인지는 훅의 출력을 봐야 알 수 있다.

★ **더 넓은 구멍은 스위치다.** 훅 파일은 git 이 추적하지만 그것을 켜는
`core.hooksPath` 설정은 추적되지 않는다. 훅이 스스로 그 사실을 적어두고 있다 —
새 클론은 다음을 한 번 실행할 때까지 **아무 검사 없이 push 한다.**

```bash
git config core.hooksPath .githooks
```

파일은 살아남고 스위치는 안 살아남는다. "추적했으니 산다" 로 읽으면 틀린다.

의도적으로 건너뛰려면 `git push --no-verify` 다. 이건 구멍이 아니라 설계된 문이고,
위 셋과 다른 점은 **건너뛴다는 것을 누르는 사람이 안다**는 것이다.

⚠ **검사기가 여전히 빨개지는지 보는 자기검사는 아무것도 자동으로 부르지 않는다.**
훅에 안 넣은 것은 의도다 — push 가 나르는 것은 내용이지 **검사기의 정확성**이 아니다.
CI 에 거는 것은 조건부 미래로 기록돼 있지 지금 도는 동작이 아니다. 그래서 검사기가
언제부터 무음이 됐는지는 **사람이 손으로 돌려야** 알 수 있다.

# 확인

지금 이 클론에서 게이트가 켜져 있는지:

```bash
git config --get core.hooksPath
```

`.githooks` 가 나와야 한다. 아무것도 안 나오면 훅은 파일로만 존재하고 돌지 않는다.

두 검사를 훅 없이 직접 돌려보는 것:

```bash
python3 _tools/site_lint.py && python3 tests/check_knowledge_bundle.py
```
