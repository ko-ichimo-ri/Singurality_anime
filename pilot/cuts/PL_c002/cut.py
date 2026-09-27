"""PL_c002: 改札を出るおっさん。うつむいて、ポケットに手を入れたまま歩く。

出口の手前で足を止め、外の雨に顔を上げる。傘は持っていない。
カメラは横から、おっさんに合わせてゆっくり右へ流れる。
"""

import cairo

from engine import assets
from engine.config import H, W
from engine.draw import ease_in_out, ease_out, lerp, linear, seg, smooth, src, ellipse
from engine.fx import Rain, bokeh, scatter_lights

DURATION = 4.5

loc = assets.location("station_rain")
ossan = assets.character("ossan")

FLOOR = 960
EXIT_X = 1560          # 出口（外への開口部）の左端。背景と一緒に流れる
SCROLL = 330
RAIN = Rain(21, 260, area=(0, 0, 900, H), speed=(1300, 1700), length=(30, 50), width=1.2, alpha=0.4)
LIGHTS = scatter_lights(22, 14, (0, 250, 700, 760), (18, 60), ["#ffcf7f", "#9fc3ff", "#ff5a4f", "#ffd48a"], (0.25, 0.6))


def draw(ctx, t, env):
    go = 1 - smooth(seg(t, 2.4, 3.3))              # 歩く量（止まるときに 0 へ）
    scroll = SCROLL * ease_in_out(seg(t, 0, 3.4))
    phase = t * 0.82 if t < 3.3 else 3.3 * 0.82
    loc.gates(ctx, t, FLOOR, scroll)

    # 出口の向こう：夜と雨
    ex = EXIT_X - scroll
    ctx.save()
    ctx.rectangle(ex, 60, W - ex + 10, FLOOR - 60)
    ctx.clip()
    ctx.set_source(linear(0, 60, 0, FLOOR, [(0, "#0a0f1e", 1), (1, "#1b2138", 1)]))
    ctx.paint()
    ctx.translate(ex, 0)
    bokeh(ctx, t, LIGHTS)
    RAIN.draw(ctx, t, alpha=1.0)
    ctx.restore()
    # 出口の枠
    src(ctx, "#2a2f3c")
    ctx.rectangle(ex - 22, 0, 26, FLOOR)
    ctx.fill()
    ctx.rectangle(ex - 22, 50, W, 14)
    ctx.fill()
    # 床に映る外の暗さ
    ctx.set_source(linear(ex, 0, ex + 300, 0, [(0, "#1b2138", 0.0), (1, "#1b2138", 0.55)]))
    ctx.rectangle(ex, FLOOR, W, H - FLOOR)
    ctx.fill()

    # おっさん
    x = lerp(470, 920, ease_out(seg(t, 0, 3.3) * 0.95 + 0.05 * seg(t, 0, 3.3)))
    s = 780
    head = lerp(0.24, -0.04, smooth(seg(t, 3.2, 4.1)))
    blink = 1.0 if 3.95 < t < 4.07 else 0.0
    src(ctx, "#000000", 0.18)
    ellipse(ctx, x + 10, FLOOR + 4, 120, 14)
    ctx.fill()
    ossan.side(ctx, x, FLOOR, s, walk=phase, walk_amt=go, hunch=lerp(0.09, 0.05, seg(t, 3.2, 4.1)),
               head=head, blink=blink, tint=env.char_tint(("#c7b8a0", 0.06)))

    # 手前を横切る柱（奥行きを出す）
    px = 180 - scroll * 1.8
    ctx.set_source(linear(px, 0, px + 120, 0, [(0, "#1d1f26", 1), (1, "#2d3039", 1)]))
    ctx.rectangle(px, 0, 120, H)
    ctx.fill()

    # 室内の明るさ
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    ctx.set_source(linear(0, 0, W, 0, [(0, "#fff4dc", 0.25), (0.7, "#fff4dc", 0.0), (1, "#1a2445", 0.3)]))
    ctx.paint()
    ctx.restore()
