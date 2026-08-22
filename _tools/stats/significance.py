"""유의성 실측 — wang 논문의 24번 비교 구조를 그대로 흉내낸다.

핵심 설정: **두 집단 사이에 진짜 차이는 0이다.** 같은 곳에서 두 번 뽑았을 뿐이다.
그런데도 "유의한 차이"가 몇 번이나 나오는지를 센다.
"""
import random, math

random.seed(7)


def welch_p(a, b):
    """두 집단의 평균 차이에 대한 p값 (Welch's t-test, n=100이라 정규 근사)."""
    n1, n2 = len(a), len(b)
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    t = (m1 - m2) / math.sqrt(v1 / n1 + v2 / n2)
    return math.erfc(abs(t) / math.sqrt(2))       # 양측 p값


def draw(n=100, shift=0.0):
    """응답 100개를 뽑는다. shift=0이면 두 집단이 완전히 같은 곳에서 나온다."""
    return [random.gauss(shift, 1.0) for _ in range(n)]


print("=" * 66)
print("실험 1 — 진짜 차이가 0인 두 집단을 10,000번 비교하면?")
print("=" * 66)
hits = sum(welch_p(draw(), draw()) < 0.05 for _ in range(10000))
print(f"  '유의한 차이 있음'(p<0.05) 판정: 10,000번 중 {hits}번  ({hits/100:.1f}%)")
print("  → 차이가 0인데도 20번에 1번꼴로 '차이 있다'가 나온다. 이게 0.05의 뜻이다.\n")

print("=" * 66)
print("실험 2 — wang의 구조: 정체성 하나당 24번 비교 (지표 6 × 모델 4)")
print("=" * 66)
SETS = 1000
counts = []
for _ in range(SETS):
    counts.append(sum(welch_p(draw(), draw()) < 0.05 for _ in range(24)))
print(f"  진짜 차이가 0인데도 24번 중 '유의' 나온 횟수 — 1,000세트 실측")
print(f"    평균 {sum(counts)/SETS:.2f}번 · 최대 {max(counts)}번")
print(f"    한 번이라도 유의가 나온 세트: {sum(c >= 1 for c in counts)/10:.1f}%")
for k in (3, 5, 10, 16, 18, 23):
    c = sum(x >= k for x in counts)
    print(f"    {k:2d}번 이상 유의가 나온 세트: {c:4d} / {SETS}")

print()
print("=" * 66)
print("실험 3 — 다중비교 보정(Bonferroni)을 걸면?")
print("=" * 66)
print("  24번 비교하니 기준을 0.05 대신 0.05/24 = 0.0021로 낮춘다.")
strict = []
for _ in range(SETS):
    strict.append(sum(welch_p(draw(), draw()) < 0.05 / 24 for _ in range(24)))
print(f"    차이 0일 때 유의 횟수: 평균 {sum(strict)/SETS:.3f}번 (보정 전 {sum(counts)/SETS:.2f}번)")

print()
print("  그럼 진짜 효과가 있을 때 이 보정이 결과를 죽이나?")
for shift, label in [(0.20, "아주 약한 효과"), (0.45, "중간 효과"), (0.80, "강한 효과")]:
    raw = sum(welch_p(draw(), draw(shift=shift)) < 0.05 for _ in range(24))
    bon = sum(welch_p(draw(), draw(shift=shift)) < 0.05 / 24 for _ in range(24))
    print(f"    {label}(차이 {shift}): 보정 전 {raw:2d}/24 → 보정 후 {bon:2d}/24")
print()
print("=" * 66)
