# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "numpy"]
# ///
"""트랜스포머 공부글(1706.03762) 그림 2장.

  images/attention-pattern.svg  — 무대 문장 전체 점수판 + `its` 줄만 뽑은 비율
  images/attention-masked.svg   — 같은 점수판에서 뒤쪽을 가린 모습(decoder masking)

무대 문장 = 논문 부록 Figure 4의 예문 앞부분:
  "The Law will never be perfect, but its application should be just"

⚠ 숫자는 전부 설명용 모식도다. 논문 Figure는 색 농도로만 그려져 있어 실제 attention
   값을 읽을 수 없다. 여기 값은 글 본문이 이미 서술한 것(its가 Law로 가장 크게,
   application으로 그 다음)만 그림으로 옮긴 것이고 모델의 측정치가 아니다.
   논문 Figure를 복사하지 않고 이해한 구조를 다시 그린 것(CLAUDE.md 차트 규약).
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import figstyle
from figstyle import TEAL, INK, MUTE, FAINT

figstyle.apply()

TOKENS = ["The", "Law", "will", "never", "be", "perfect", ",",
          "but", "its", "application", "should", "be", "just"]
N = len(TOKENS)
ITS = TOKENS.index("its")

# `its` 줄의 비율 — 합 1.0. Law가 최대, application이 그 다음(본문 서술과 일치).
ITS_ROW = np.array([0.02, 0.45, 0.02, 0.02, 0.03, 0.05, 0.02,
                    0.04, 0.08, 0.22, 0.02, 0.02, 0.01])

# 옅은 흰색 → 청록. 값이 클수록 진하다.
CMAP = LinearSegmentedColormap.from_list("teal", ["#ffffff", TEAL])


def base_grid():
    """전체 점수판 모식도. 대각선(자기 자신)과 인접 단어를 조금 높게 깔고
    `its` 줄만 본문이 서술한 값으로 덮는다. seed 고정 — 다시 돌려도 같은 그림."""
    rng = np.random.default_rng(20170612)
    g = rng.uniform(0.01, 0.09, size=(N, N))
    for i in range(N):
        g[i, i] += 0.18                      # 자기 자신
        if i > 0:
            g[i, i - 1] += 0.12              # 바로 앞 단어
    g[ITS] = ITS_ROW
    return g / g.sum(axis=1, keepdims=True)  # 줄마다 합 1


def draw(ax, grid, title, mask_upper=False):
    m = grid.copy()
    if mask_upper:
        tri = np.triu(np.ones_like(m, dtype=bool), k=1)
        m[tri] = np.nan
        m = np.where(np.isnan(m), np.nan, m)
        m = m / np.nansum(m, axis=1, keepdims=True)
    im = ax.imshow(m, cmap=CMAP, vmin=0, vmax=0.35, aspect="equal")
    ax.set_xticks(range(N))
    ax.set_yticks(range(N))
    ax.set_xticklabels(TOKENS, rotation=90, fontsize=8.5)
    ax.set_yticklabels(TOKENS, fontsize=8.5)
    ax.set_xlabel("비교당하는 쪽 (key)", fontsize=9.5, labelpad=6)
    ax.set_ylabel("묻는 쪽 (query)", fontsize=9.5, labelpad=6)
    ax.set_title(title, fontsize=11, color=INK, pad=10)
    for s in ax.spines.values():
        s.set_color(FAINT)
    if mask_upper:                            # 가려진 영역에 사선 표시
        for i in range(N):
            for j in range(i + 1, N):
                ax.plot([j - 0.5, j + 0.5], [i - 0.5, i + 0.5],
                        color=FAINT, lw=0.5, zorder=3)
    return im


# ── 그림 1: 전체 점수판 + `its` 줄 확대 ──
grid = base_grid()
fig = plt.figure(figsize=(7.2, 9.4))
gs = fig.add_gridspec(2, 1, height_ratios=[3.1, 1], hspace=0.72)

ax1 = fig.add_subplot(gs[0])
draw(ax1, grid, "모든 단어 쌍의 점수 — 한 줄의 합이 1이 되도록 맞춘 것")
ax1.add_patch(plt.Rectangle((-0.5, ITS - 0.5), N, 1, fill=False,
                            edgecolor=INK, lw=1.6, zorder=4))

ax2 = fig.add_subplot(gs[1])
ax2.bar(range(N), ITS_ROW, color=TEAL, width=0.62, zorder=3)
ax2.set_xticks(range(N))
ax2.set_xticklabels(TOKENS, rotation=90, fontsize=8.5)
ax2.set_ylim(0, 0.52)
ax2.set_ylabel("섞이는 비율", fontsize=9.5)
ax2.set_title("its 줄만 뽑으면 — Law가 가장 크고 application이 그 다음",
              fontsize=11, color=INK, pad=10)
ax2.spines[["top", "right"]].set_visible(False)
for i, v in enumerate(ITS_ROW):
    if v >= 0.2:
        ax2.text(i, v + 0.015, f"{v:.2f}", ha="center", fontsize=9, color=INK)

figstyle.save(fig, "attention-pattern")

# ── 그림 2: 뒤쪽을 가린 점수판 ──
fig, ax = plt.subplots(figsize=(6.4, 6.4))
draw(ax, grid, "각 자리가 자기 뒤쪽을 못 보게 막은 점수판", mask_upper=True)
ax.text(N - 0.2, 0.6, "사선 = 가려진 자리\n(비율 0)", fontsize=9.5,
        color=MUTE, ha="right", va="top")
figstyle.save(fig, "attention-masked")
