# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "numpy"]
# ///
"""밑돌 글(before-attention) 그림 1장.

  images/relu-kink.svg  — 한 층(직선)으로는 못 맞추는 요금표를 ReLU 하나가 맞추는 장면

본문이 이미 숫자로 서술한 것을 그림으로 옮긴 것이고 새 주장을 담지 않는다.
요금표는 본문의 장거리 할인 예시와 같다(10km까지 1km당 1,000원, 이후 800원).

  한 층      요금 = 3,000 + 1,000×거리                       → 20km에서 23,000원(빗나감)
  두 층+ReLU 요금 = 3,000 + 1,000×거리 − 200×ReLU(거리−10)   → 세 점 모두 통과

세 점은 본문 표의 실제 기록이고 계산값은 스크립트가 직접 구한다(손으로 적지 않는다).
"""
import numpy as np
import matplotlib.pyplot as plt

import figstyle
from figstyle import TEAL, RED, INK, MUTE

figstyle.apply()

# 본문과 같은 요금표
records = [(5, 8_000), (10, 13_000), (20, 21_000)]

x = np.linspace(0, 22, 501)
linear = 3_000 + 1_000 * x                                  # 한 층 — 직선 하나
relu = 3_000 + 1_000 * x - 200 * np.maximum(0, x - 10)      # 두 층 + ReLU

# 그림이 본문 수치와 어긋나지 않는지 스크립트 안에서 확인
for d, fare in records:
    got = 3_000 + 1_000 * d - 200 * max(0, d - 10)
    assert got == fare, f"{d}km 계산 {got} != 본문 {fare}"

fig, ax = plt.subplots(figsize=(6.6, 4.1))

# 10km 이후 두 답이 갈라지는 폭을 면으로 — 꺾임 자체는 20% 차이라 선만으론 잘 안 보인다
ax.fill_between(x, relu, linear, where=(x >= 10), color=RED, alpha=0.13, lw=0)

ax.plot(x, linear, color=MUTE, lw=1.8, ls="--",
        label="한 층 — 직선 하나뿐이라 못 맞춘다")
ax.plot(x, relu, color=TEAL, lw=2.4,
        label="두 층 + ReLU — 10km에서 꺾인다")

ax.scatter([d for d, _ in records], [f for _, f in records],
           color=RED, s=52, zorder=5, label="실제 요금 기록")

# 꺾인점 표시
ax.axvline(10, color=INK, lw=0.8, ls=":", alpha=0.45)
ax.annotate("꺾인점 — 여기서 ReLU가 켜지고\n1km당 1,000원이 800원으로 바뀐다",
            xy=(10, 13_000), xytext=(3.1, 17_600),
            fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="->", color=INK, lw=0.9,
                            connectionstyle="arc3,rad=-0.2"))

# 한 층이 빗나가는 폭
ax.annotate("", xy=(20, 23_000), xytext=(20, 21_000),
            arrowprops=dict(arrowstyle="<->", color=RED, lw=1.2))
ax.text(19.4, 24_500, "한 층은 여기서\n2,000원 빗나간다",
        fontsize=9, color=RED, ha="center")

ax.set_xlabel("거리 (km)")
ax.set_ylabel("요금 (원)")
ax.set_xlim(0, 22)
ax.set_ylim(0, 28_500)
ax.set_xticks([0, 5, 10, 15, 20])
ax.set_yticks([0, 5_000, 10_000, 15_000, 20_000, 25_000])
ax.set_yticklabels(["0", "5,000", "10,000", "15,000", "20,000", "25,000"])
ax.grid(True, alpha=0.18, lw=0.6)
ax.legend(loc="upper left", frameon=False, fontsize=9)

figstyle.save(fig, "relu-kink")
