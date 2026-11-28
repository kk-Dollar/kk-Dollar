"""Build assets/demo_carousel.svg: a Hotstar-style auto-sliding demo carousel.

Shows two thumbnails at a time and slides one card left every HOLD seconds,
looping forever. Thumbnails are embedded as base64 JPEGs because GitHub's
image proxy blocks external references inside SVGs.

Usage: python3 assets/make_carousel.py   (run from the repo root)
Add a project by appending its thumbnail to CARDS.
"""
import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
CARDS = [
    "thumbnails/bitbot2_opencv.jpg",
    "thumbnails/bitbot2_nav2.jpg",
    "thumbnails/humanoid_arm.jpg",
    "thumbnails/car_painting_cell.jpg",
    "thumbnails/aloha_act.jpg",
]
OUT = ROOT / "demo_carousel.svg"

CARD_W, CARD_H, GAP, PAD = 640, 360, 20, 10
HOLD, SLIDE = 3.2, 0.7          # seconds a pair stays put / seconds to slide
STEP = CARD_W + GAP
VIEW_W = 2 * CARD_W + GAP + 2 * PAD
DOTS_Y = CARD_H + 2 * PAD + 14
VIEW_H = DOTS_Y + 14


def embed(path):
    im = Image.open(ROOT / path).convert("RGB").resize((CARD_W, CARD_H), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def pct(t, total):
    return f"{100 * t / total:.3f}%"


def main():
    n = len(CARDS)
    total = n * (HOLD + SLIDE)
    imgs = [embed(p) for p in CARDS]
    strip = imgs + imgs[:2]  # repeat the first two so the loop wraps seamlessly

    # Strip keyframes: hold at -i*STEP, then ease to -(i+1)*STEP.
    frames = []
    for i in range(n):
        t0 = i * (HOLD + SLIDE)
        frames.append(f"{pct(t0, total)}{{transform:translateX({-i * STEP}px);animation-timing-function:linear}}")
        frames.append(f"{pct(t0 + HOLD, total)}{{transform:translateX({-i * STEP}px);animation-timing-function:cubic-bezier(.65,0,.35,1)}}")
    frames.append(f"100%{{transform:translateX({-n * STEP}px)}}")

    # One keyframe set per dot: lit while its card is the left-hand card.
    on, off = "{fill:#4FC3F7}", "{fill:#5b6472}"
    eps = 0.01
    dot_css = []
    for j in range(n):
        lit_from = j * (HOLD + SLIDE) - (SLIDE / 2 if j else 0)
        lit_to = (j + 1) * (HOLD + SLIDE) - SLIDE / 2
        if j == 0:
            kf = f"0%{on}{pct(lit_to, total)}{on}{pct(lit_to + eps, total)}{off}{pct(total - SLIDE / 2, total)}{off}{pct(total - SLIDE / 2 + eps, total)}{on}100%{on}"
        else:
            kf = f"0%{off}{pct(lit_from, total)}{off}{pct(lit_from + eps, total)}{on}{pct(lit_to, total)}{on}{pct(lit_to + eps, total)}{off}100%{off}"
        dot_css.append(f"@keyframes d{j}{{{kf}}}.d{j}{{animation:d{j} {total:.2f}s infinite}}")

    cards_svg = "\n".join(
        f'    <image x="{k * STEP}" y="0" width="{CARD_W}" height="{CARD_H}" '
        f'clip-path="url(#r{k})" xlink:href="data:image/jpeg;base64,{b64}"/>'
        for k, b64 in enumerate(strip)
    )
    clips = "\n".join(
        f'    <clipPath id="r{k}"><rect x="{k * STEP}" y="0" width="{CARD_W}" height="{CARD_H}" rx="14"/></clipPath>'
        for k in range(len(strip))
    )
    dots_x0 = (VIEW_W - (n - 1) * 22) / 2
    dots = "\n".join(
        f'  <circle class="d{j}" cx="{dots_x0 + j * 22:.1f}" cy="{DOTS_Y}" r="5" fill="#5b6472"/>'
        for j in range(n)
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {VIEW_W} {VIEW_H}" width="{VIEW_W}" height="{VIEW_H}">
  <style>
    @keyframes slide{{{"".join(frames)}}}
    .strip{{animation:slide {total:.2f}s infinite}}
    {"".join(dot_css)}
  </style>
  <defs>
{clips}
  </defs>
  <svg x="{PAD}" y="{PAD}" width="{2 * CARD_W + GAP}" height="{CARD_H}" overflow="hidden">
  <g class="strip">
{cards_svg}
  </g>
  </svg>
{dots}
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {n} cards, {total:.1f}s loop)")


if __name__ == "__main__":
    main()
