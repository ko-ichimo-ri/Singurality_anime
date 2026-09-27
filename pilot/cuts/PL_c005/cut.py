"""PL_c005: 傘の柄の受け渡し（手元のアップ）。

高く掲げたアンドロイドの手の上から、おっさんの手が柄をにぎる。アンドロイドの手がほどけて、下りていく。
アンドロイドの手首には、首すじと同じ細い光の継ぎ目がある。
"""

import math

from engine import assets
from engine.config import H, W
from engine.draw import capsule, ease_in_out, ease_out, ellipse, glow, lerp, linear, rrect, seg, smooth, src
from engine.fx import Rain, bokeh, scatter_lights

DURATION = 4.5

android = assets.character("android")
ossan = assets.character("ossan")
umbrella = assets.prop("umbrella")

LIGHTS = scatter_lights(51, 26, (-100, 250, W + 100, H + 50), (60, 170),
                        ["#ffcf7f", "#9fc3ff", "#ff5a4f", "#ffd48a", "#c89cff"], (0.10, 0.28))
RAIN_BACK = Rain(52, 380, speed=(1000, 1400), length=(24, 44), width=1.2, alpha=0.28)
RAIN_FRONT = Rain(53, 40, speed=(2000, 2600), length=(160, 240), width=3.0, alpha=0.18)
SHAFT_X = 960


def fist(ctx, x, y, s, skin, skin_dk, tint, thumb_side=1):
    """柄を横からにぎる手。thumb_side で親指の向き（1 で右）。"""
    src(ctx, skin, 1, tint)
    rrect(ctx, x - 0.55 * s, y - 0.50 * s, 1.1 * s, 1.0 * s, 0.38 * s)
    ctx.fill()
    src(ctx, skin_dk, 0.8, tint)
    ctx.set_line_width(0.035 * s)
    for k in range(1, 4):
        yy = y - 0.5 * s + k * 0.25 * s
        ctx.move_to(x - 0.50 * s * thumb_side, yy)
        ctx.line_to(x + 0.05 * s * thumb_side, yy)
        ctx.stroke()
    src(ctx, skin, 1, tint)
    ellipse(ctx, x + 0.35 * s * thumb_side, y - 0.42 * s, 0.30 * s, 0.20 * s)
    ctx.fill()
    src(ctx, skin_dk, 0.6, tint)
    ellipse(ctx, x + 0.45 * s * thumb_side, y - 0.45 * s, 0.12 * s, 0.09 * s)
    ctx.fill()


def open_hand(ctx, x, y, s, skin, skin_dk, tint, spread):
    """指をほどいた手。"""
    src(ctx, skin, 1, tint)
    rrect(ctx, x - 0.50 * s, y - 0.35 * s, 1.0 * s, 0.9 * s, 0.35 * s)
    ctx.fill()
    for k in range(4):
        a = -0.5 + k * 0.28 + spread * (k - 1.5) * 0.12
        x0 = x - 0.36 * s + k * 0.24 * s
        x1 = x0 + math.sin(a) * 0.55 * s
        y1 = y - 0.35 * s - math.cos(a) * 0.55 * s
        capsule(ctx, x0, y - 0.25 * s, x1, y1, 0.22 * s, 0.19 * s)
        ctx.fill()
    capsule(ctx, x + 0.45 * s, y + 0.1 * s, x + 0.80 * s, y - 0.30 * s, 0.26 * s, 0.2 * s)
    ctx.fill()


def draw(ctx, t, env):
    ctx.set_source(linear(0, 0, W, H, [(0, "#1d2238", 1), (1, "#0a0e1c", 1)]))
    ctx.paint()
    bokeh(ctx, t, LIGHTS, drift=6)
    RAIN_BACK.draw(ctx, t)

    lift = -46 * ease_in_out(seg(t, 3.2, 4.5))
    anchor_y = 830 + lift
    tint_a = ("#2b2f52", 0.10)
    tint_o = ("#c9b9a0", 0.06)
    umbrella.draw(ctx, SHAFT_X, anchor_y, 1020, under=1.0, shine=0.4, tint=("#2b2f52", 0.15), t=t)

    # アンドロイドの腕（右下から）
    release = ease_in_out(seg(t, 2.3, 3.4))
    ay = 760 + lift * (1 - release)
    ax_hand = lerp(SHAFT_X + 18, SHAFT_X + 330, release)
    ay_hand = lerp(ay, 1010, release)
    wrist = (ax_hand + 70, ay_hand + 70)
    src(ctx, android.C["coat_lt"], 1, tint_a)
    capsule(ctx, W + 200, H + 260, wrist[0] + 60, wrist[1] + 60, 260, 170)
    ctx.fill()
    src(ctx, android.C["coat_dk"], 1, tint_a)
    capsule(ctx, wrist[0] + 90, wrist[1] + 90, wrist[0] + 40, wrist[1] + 40, 175, 168)
    ctx.fill()
    src(ctx, android.C["skin"], 1, tint_a)
    capsule(ctx, wrist[0] + 40, wrist[1] + 40, ax_hand + 20, ay_hand + 20, 110, 100)
    ctx.fill()
    # 手首の光の継ぎ目
    pulse = 0.55 + 0.3 * math.sin(t * 2.1)
    src(ctx, android.C["light"], pulse)
    ctx.set_line_width(4)
    ctx.move_to(wrist[0] + 2, wrist[1] + 78)
    ctx.line_to(wrist[0] + 78, wrist[1] + 2)
    ctx.stroke()
    glow(ctx, wrist[0] + 40, wrist[1] + 40, 60, android.C["light"], 0.12 * pulse)
    if release < 0.35:
        fist(ctx, SHAFT_X + 12, ay, 150, android.C["skin"], android.C["skin_dk"], tint_a, thumb_side=-1)
    else:
        open_hand(ctx, ax_hand, ay_hand, 150, android.C["skin"], android.C["skin_dk"], tint_a, release)

    # おっさんの手（左から伸びてきて、上をにぎる）
    reach = ease_out(seg(t, 0.5, 1.7))
    ox_hand = lerp(-260, SHAFT_X - 12, reach)
    oy_hand = lerp(760, 575, reach) + lift * smooth(seg(t, 2.0, 3.0))
    grip = seg(t, 1.55, 1.8) >= 1
    src(ctx, ossan.C["coat_lt"], 1, tint_o)
    capsule(ctx, -400, H + 300, ox_hand - 150, oy_hand + 110, 330, 220)
    ctx.fill()
    src(ctx, ossan.C["shirt"], 1, tint_o)
    capsule(ctx, ox_hand - 150, oy_hand + 110, ox_hand - 110, oy_hand + 80, 150, 140)
    ctx.fill()
    src(ctx, ossan.C["skin"], 1, tint_o)
    capsule(ctx, ox_hand - 120, oy_hand + 85, ox_hand - 20, oy_hand + 20, 125, 115)
    ctx.fill()
    if grip:
        fist(ctx, ox_hand, oy_hand, 175, ossan.C["skin"], ossan.C["skin_dk"], tint_o, thumb_side=1)
    else:
        open_hand(ctx, ox_hand, oy_hand, 175, ossan.C["skin"], ossan.C["skin_dk"], tint_o, 0.3)

    RAIN_FRONT.draw(ctx, t)
    # 左からの駅の明かり
    ctx.set_source(linear(0, 0, W, 0, [(0, "#fff0d0", 0.10), (0.5, "#fff0d0", 0.0)]))
    ctx.paint()
