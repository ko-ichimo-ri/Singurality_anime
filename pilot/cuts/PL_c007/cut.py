"""PL_c007: 後ろから、寄り。カメラは二人と一緒に進む。

「こんなに技術が進んでも、足元がびしょびしょになっちゃいますね」
言いながら、アンドロイドがおっさんへ肩を寄せる。足もとの水たまりが、歩くたびに跳ねる。
"""

import math

import cairo

from engine import assets
from engine.config import H, W
from engine.draw import ease_in_out, ellipse, lerp, linear, seg, smooth, src
from engine.fx import Rain, Ripples, bokeh, reflection, scatter_lights

DURATION = 7.5

loc = assets.location("station_rain")
ossan = assets.character("ossan")
android = assets.character("android")
umbrella = assets.prop("umbrella")

STREET = loc.Street(seed=7, vy=250, f=900, cam_h=1.5)
D = 1.75
LIGHTS = scatter_lights(71, 18, (0, 180, W, 700), (40, 110), ["#ffcf7f", "#9fc3ff", "#ff5a4f", "#ffd48a"], (0.10, 0.25))
RAIN_MID = Rain(72, 360, speed=(1300, 1700), length=(34, 60), width=1.4, alpha=0.30)
RAIN_NEAR = Rain(73, 50, speed=(2300, 2900), length=(140, 220), width=2.8, alpha=0.16)
RIPPLES = Ripples(74, rate=40, area=(0, 700, W, H + 40), size=(16, 60), perspective=lambda y: 0.3 + (y - 300) / 800)


def splash(ctx, x, y, age, s):
    """足もとで跳ねる水。age は着地してからの時間（秒）。"""
    if not 0 <= age < 0.35:
        return
    a = 0.55 * (1 - age / 0.35)
    src(ctx, "#dfe7ff", a)
    for i in range(6):
        ang = -math.pi / 2 + (i - 2.5) * 0.35
        d = 90 * s * age / 0.35
        px = x + math.cos(ang) * d
        py = y + math.sin(ang) * d + 220 * s * age * age / 0.35
        ellipse(ctx, px, py, 3.5 * s, 5 * s)
        ctx.fill()
    ctx.set_line_width(2)
    src(ctx, "#dfe7ff", a * 0.7)
    ellipse(ctx, x, y + 4, 40 * s * (0.4 + age * 2), 7 * s * (0.4 + age * 2))
    ctx.stroke()


def draw(ctx, t, env):
    light = STREET.draw(ctx, t, travel=t * 1.05)
    # ピンボケ（背景を少し沈めて光をにじませる）
    src(ctx, "#0a0e1c", 0.35)
    ctx.paint()
    bokeh(ctx, t, LIGHTS)
    RIPPLES.draw(ctx, t)

    lean = smooth(seg(t, 3.4, 4.6))
    px_m = STREET.scale_at(D)
    s_o = 1.70 * px_m
    s_a = 1.70 * android.HEIGHT * px_m
    ox, feet = STREET.proj(-0.27, 0, D)
    axx, _ = STREET.proj(lerp(0.33, 0.27, lean), 0, D)
    mid = (ox + axx) / 2
    ph_o = t * 0.82
    ph_a = t * 0.95 + 0.3

    reflection(ctx, mid, feet + 6, 420, 300, umbrella.C["canopy"], 0.16, wobble=16, t=t)
    src(ctx, "#000000", 0.3)
    ellipse(ctx, mid, feet + 4, 260, 20)
    ctx.fill()

    hold = (mid - 5, feet - 0.76 * s_o)
    android.back(ctx, axx, feet, s_a, walk=ph_a, walk_amt=0.85, lean=-0.07 * lean,
                 head_tilt=-0.16 * lean, tint=env.char_tint(loc.NIGHT), t=t)
    ossan.back(ctx, ox, feet, s_o, walk=ph_o, walk_amt=0.85, hold=hold, tint=env.char_tint(loc.NIGHT),
               head_tilt=0.04 * lean)
    umbrella.draw(ctx, *hold, 0.40 * s_o, angle=0.10 - 0.03 * lean, tint=env.prop_tint(("#1a2445", 0.12)), t=t)

    # 足もとの水はね（足が地面に着くたび）
    for x0, ph, sc in ((ox, ph_o, 1.0), (axx, ph_a, 0.85)):
        for leg in (0, 1):
            p = (ph + leg * 0.5) % 1.0
            age = (p - 0.5) / 0.82 if p >= 0.5 else (p + 0.5) / 0.82
            lx = x0 + (-1 if leg == 0 else 1) * 0.046 * s_o * sc
            splash(ctx, lx, feet - 4, age, sc)

    RAIN_MID.draw(ctx, t, light=light)
    RAIN_NEAR.draw(ctx, t)
    # 字幕が読みやすいように、下を少し暗く
    ctx.set_source(linear(0, H - 260, 0, H, [(0, "#000000", 0), (1, "#000000", 0.35)]))
    ctx.rectangle(0, H - 260, W, 260)
    ctx.fill()
