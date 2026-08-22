"""효과크기 실측 — p값이 답하지 못하는 것.

질문 1: 표본을 늘리면 p값은 낮아질 수밖에 없나?
"""
import random, math

random.seed(11)


def welch_p(a, b):
    """두 집단의 평균 차이에 대한 p값 (n이 크므로 정규 근사)."""
    n1, n2 = len(a), len(b)
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    t = (m1 - m2) / math.sqrt(v1 / n1 + v2 / n2)
    return math.erfc(abs(t) / math.sqrt(2))


def draw(n, shift=0.0):
    return [random.gauss(shift, 1.0) for _ in range(n)]


print("=" * 70)
print("질문 — 참가자를 늘리면 '유의하다'가 더 자주 나오나?")
print("=" * 70)
print("  (각 칸 = 그 조건으로 여러 번 실험했을 때 '유의' 판정이 나온 비율)\n")

SIZES = [(100, 300), (1_000, 300), (10_000, 200), (100_000, 100)]

for shift, label in [(0.05, "진짜 차이가 티끌만큼 있다 (0.05)"),
                     (0.00, "진짜 차이가 정말 없다   (0)   ")]:
    cells = []
    for n, reps in SIZES:
        hits = sum(welch_p(draw(n), draw(n, shift=shift)) < 0.05 for _ in range(reps))
        cells.append(f"n={n:>7,} → {hits/reps*100:5.1f}%")
    print(f"  {label}")
    print("    " + "  |  ".join(cells) + "\n")


print("=" * 70)
print("질문 2 — 같은 3cm 차이인데 집단의 퍼짐만 다르면?")
print("=" * 70)
print("  재는 법: 두 집단에서 한 명씩 무작위로 뽑아 키를 견준다.")
print("  위 집단 쪽이 더 큰 경우가 몇 %인가? (50% = 전혀 구별 안 됨)\n")

TRIALS = 200_000

for spread, label in [(6, "A연구 — 성인 남성끼리   (키가 좁게 몰려 있음)"),
                      (25, "B연구 — 유치원생~성인  (키가 넓게 퍼져 있음)")]:
    wins = 0
    for _ in range(TRIALS):
        if random.gauss(3.0, spread) > random.gauss(0.0, spread):
            wins += 1
    print(f"  {label}")
    print(f"    평균 차이 3cm · 퍼짐 {spread}cm  →  더 큰 쪽으로 뽑힐 확률 {wins/TRIALS*100:.1f}%\n")


print("=" * 70)
print("질문 3 — 다중비교 보정은 무엇을 죽이고 무엇을 살리나")
print("=" * 70)
print("  wang과 같은 구조: 응답 100개씩, 정체성 하나당 24번 비교.")
print("  보정 전 기준 p<0.05  vs  보정 후 기준 p<0.05/24 (=0.0021)")
print("  같은 데이터에 두 기준을 각각 적용해 '유의' 개수를 센다.\n")

SETS = 300

for d, label in [(0.0, "효과 없음  (0)  "),
                 (0.2, "작은 효과  (0.2)"),
                 (0.5, "중간 효과  (0.5)"),
                 (0.8, "큰 효과    (0.8)")]:
    raw_total = bon_total = 0
    for _ in range(SETS):
        ps = [welch_p(draw(100), draw(100, shift=d)) for _ in range(24)]
        raw_total += sum(p < 0.05 for p in ps)
        bon_total += sum(p < 0.05 / 24 for p in ps)
    print(f"  {label}  →  보정 전 {raw_total/SETS:5.1f}/24   보정 후 {bon_total/SETS:5.1f}/24")
print()
