"""PL_c004: ひさしの端で、二人が向き合う（横から）。

アンドロイドが近づき、背伸びをして、傘を高く掲げる。おっさんの頭の上まで届かせようとして、少しふらつく。
おっさんは、見上げる。
"""

import math

from engine import assets
from engine.config import H, W
from engine.draw import ease_in_out, ease_out, ellipse, glow, lerp, linear, seg, smooth, src
from engine.fx import Drips, Rain, Ripples, bokeh, scatter_lights

DURATION = 4.5

loc = assets.location("station_rain")
ossan = assets.character("ossan")
android = assets.character("android")
umbrella = assets.prop("umbrella")

GROUND = 1010
EAVE = 860          # ひさしの右端（ここより右は雨）
LIGHTS = scatter_lights(41, 22, (EAVE, 120, W + 60, 820), (30, 90),
                        ["#ffcf7f", "#9fc3ff", "#ff5a4f", "#ffd48a"], (0.12, 0.32))
RAIN = Rain(42, 420, area=(EAVE, 0, W, H), speed=(1300, 1800), length=(30, 56), width=1.3, alpha=0.36)
RIPPLES = Ripples(43, rate=26, area=(EAVE + 20, GROUND, W, H), size=(14, 40))
EAVE_DRIPS = Drips(44, interval=0.5, fall=1000, alpha=0.6)


def draw(ctx, t, env):
    # 背景：左は駅の明るい壁、右は夜の街
    ctx.set_source(linear(0, 0, W, 0, [(0, "#d9d2c3", 1), (0.28, "#a9a39a", 1), (0.42, "#2a3046", 1), (1, "#0d1224", 1)]))
    ctx.paint()
    src(ctx, "#f5efdf", 0.9)
    ctx.rectangle(40, 120, 250, GROUND - 120)
    ctx.fill()
    glow(ctx, 170, 500, 520, "#fff3d6", 0.25)
    ctx.save()
    ctx.rectangle(EAVE, 0, W, H)
    ctx.clip()
    bokeh(ctx, t, LIGHTS)
    ctx.restore()
    # 地面
    ctx.set_source(linear(0, GROUND, 0, H, [(0, "#2c3148", 1), (1, "#0c1020", 1)]))
    ctx.rectangle(0, GROUND, W, H - GROUND)
    ctx.fill()
    ctx.set_source(linear(0, 0, W, 0, [(0, "#fff0d0", 0.25), (0.4, "#fff0d0", 0.0)]))
    ctx.rectangle(0, GROUND, W, H - GROUND)
    ctx.fill()

    ctx.save()
    ctx.rectangle(EAVE, 0, W, H)
    ctx.clip()
    RAIN.draw(ctx, t + 10)
    ctx.restore()

    # アンドロイドが近づき、背伸びして傘を上げる
    s_o = 600
    s_a = 600 * android.HEIGHT
    ox = 700
    walk_in = seg(t, 0.0, 1.3)
    axx = lerp(1250, 1010, ease_out(walk_in))
    go = 1 - smooth(seg(t, 0.9, 1.35))
    raise_ = ease_in_out(seg(t, 1.3, 2.7))
    tip = smooth(seg(t, 1.4, 2.4))
    wob = math.sin(t * 7.0) * 10 * smooth(seg(t, 2.6, 3.0))
    # 傘をつかむ手の位置：はじめは自分の肩の前、最後は二人のあいだの高いところ
    hx = lerp(axx - 0.08 * s_a, 870, raise_) + wob
    hy = lerp(GROUND - 0.74 * s_a, GROUND - 1.04 * s_o, raise_) + wob * 0.3
    ang = lerp(0.02, -0.16, raise_) + wob * 0.002

    # 影
    src(ctx, "#000000", 0.25)
    ellipse(ctx, ox + 10, GROUND + 4, 110, 12)
    ctx.fill()
    ellipse(ctx, axx - 10, GROUND + 4, 90, 11)
    ctx.fill()

    look_up = smooth(seg(t, 1.8, 2.8))
    ossan.side(ctx, ox, GROUND, s_o, hunch=lerp(0.06, 0.02, look_up), head=lerp(0.12, -0.28, look_up),
               blink=1.0 if 3.3 < t < 3.42 else 0.0, tint=("#c9b9a0", 0.08))
    pts = android.side(ctx, axx, GROUND, s_a, walk=t * 1.1, walk_amt=go, tiptoe=tip, flip=True,
                       head=lerp(0.0, -0.30, raise_), arm="hold", target=(hx, hy), smile=0.5,
                       lean=-0.05 * tip, tint=("#2b2f52", 0.12 * (1 - raise_)), t=t)
    u = umbrella.draw(ctx, *pts["hand"], 0.46 * s_o, angle=ang, t=t)

    # ひさし
    ctx.set_source(linear(0, 0, 0, 50, [(0, "#0b0e18", 1), (1, "#151a28", 1)]))
    ctx.rectangle(-10, 0, EAVE + 10, 46)
    ctx.fill()
    src(ctx, "#fff4dc", 0.9)
    ctx.rectangle(0, 46, EAVE - 20, 5)
    ctx.fill()
    EAVE_DRIPS.draw(ctx, t, [(EAVE - 6 - k * 70, 50) for k in range(4)] + [(EAVE - 3, 50)], size=4)
    RIPPLES.draw(ctx, t)
