"""PL_c003: 雨の中、傘を差して待っているアンドロイド（おっさんの目線）。

はじめは少し横を見ている。気づいて、こちらを見て、目を細めて笑い、小さく手を振る。
背景は街の明かりのピンボケ。傘のふちから、しずくが落ちる。
"""

from engine import assets
from engine.config import H, W
from engine.draw import camera, ease_in_out, lerp, linear, seg, smooth, src
from engine.fx import Drips, Rain, bokeh, scatter_lights

DURATION = 5.0

loc = assets.location("station_rain")
android = assets.character("android")
umbrella = assets.prop("umbrella")

BACK_LIGHTS = scatter_lights(31, 30, (-100, 150, W + 100, 900), (30, 95),
                             ["#ffcf7f", "#9fc3ff", "#ff5a4f", "#ffd48a", "#6cf0b0", "#c89cff"], (0.10, 0.30))
RAIN_BACK = Rain(32, 500, speed=(1100, 1500), length=(20, 38), width=1.0, alpha=0.30)
RAIN_FRONT = Rain(33, 70, speed=(2100, 2700), length=(120, 180), width=2.6, alpha=0.2)
DRIPS = Drips(34, interval=0.62, fall=900, alpha=0.75)


def draw(ctx, t, env):
    zoom = lerp(1.0, 1.05, ease_in_out(t / DURATION))
    with camera(ctx, zoom, 960, 520):
        ctx.set_source(linear(0, 0, 0, H, [(0, "#070a15", 1), (0.6, "#141a31", 1), (1, "#1c2440", 1)]))
        ctx.paint()
        bokeh(ctx, t, BACK_LIGHTS, drift=-4)
        # 地面の照り返し（ボケ）
        ctx.set_source(linear(0, 780, 0, H, [(0, "#2a3150", 0.0), (1, "#2a3150", 0.6)]))
        ctx.rectangle(0, 780, W, H - 780)
        ctx.fill()
        RAIN_BACK.draw(ctx, t)

        s = 900
        ax, ay = 960, 1180
        look = lerp(-1.2, 0.0, smooth(seg(t, 1.0, 1.6)))
        tilt = lerp(0.06, 0.0, smooth(seg(t, 1.0, 1.7))) + 0.05 * smooth(seg(t, 2.4, 3.2))
        smile = lerp(0.2, 1.0, smooth(seg(t, 2.1, 2.8)))
        blink = 1.0 if 1.85 < t < 1.97 else 0.0
        wave = smooth(seg(t, 2.6, 3.1)) * (1 - smooth(seg(t, 4.3, 4.9)))
        tint = ("#2b2f52", 0.20)
        pts = android.front(ctx, ax, ay, s, hold=(ax - 0.085 * s, ay - 0.70 * s), wave=wave, blink=blink,
                            smile=smile, look=look, head_tilt=tilt, tint=tint, t=t)
        u = umbrella.draw(ctx, *pts["hand_r"], 0.50 * s, angle=0.0, tint=("#2b2f52", 0.12), t=t, under=0.35)
        DRIPS.draw(ctx, t, u["rim"][1:-1:2] + [u["rim"][0], u["rim"][-1]], size=5)
    RAIN_FRONT.draw(ctx, t)
    # 顔にあたる駅の明かり
    src(ctx, "#ffe9c4", 0.05)
    ctx.paint()
