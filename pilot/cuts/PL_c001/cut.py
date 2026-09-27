"""PL_c001: 雨の夜の駅前。引きの画で場所を見せ、ゆっくり寄っていく。

出口の外で、からし色の傘が小さく誰かを待っている。
"""

from engine import assets
from engine.config import H, W
from engine.draw import camera, ease_in_out, fade, lerp, smooth
from engine.fx import Rain, Ripples, reflection

DURATION = 5.0

loc = assets.location("station_rain")
android = assets.character("android")
umbrella = assets.prop("umbrella")

GROUND = 800
RAIN_FAR = Rain(11, 900, speed=(800, 1100), length=(12, 22), width=0.8, alpha=0.30)
RAIN_MID = Rain(12, 420, speed=(1300, 1700), length=(28, 46), width=1.1, alpha=0.32)
RAIN_NEAR = Rain(13, 60, speed=(2300, 2900), length=(110, 170), width=2.4, alpha=0.18)
RIPPLES = Ripples(14, rate=70, area=(0, GROUND + 10, W, H + 60), size=(6, 34),
                  perspective=lambda y: 0.3 + (y - GROUND) / 300)


def draw(ctx, t, env):
    zoom = lerp(1.0, 1.08, ease_in_out(t / DURATION))
    with camera(ctx, zoom, 1010, 610):
        loc.sky(ctx, 0, GROUND)
        loc.skyline(ctx, t, GROUND - 10, 11, loc.C["far"], 260, 560, win=0.28, win_size=(5, 7))
        loc.skyline(ctx, t, GROUND - 10, 12, loc.C["mid"], 120, 300, win=0.42, wmin=110, wmax=260)
        loc.ground(ctx, GROUND, H - GROUND + 200, t=t, lights=[
            (960, loc.C["glass"], 440, 0.20),
            (326, loc.C["lamp"], 90, 0.22),
            (1604, loc.C["lamp"], 90, 0.22),
        ])
        loc.station(ctx, t, 960, GROUND)
        lamp_l = loc.streetlamp(ctx, t, 250, GROUND, 440, side=1)
        lamp_r = loc.streetlamp(ctx, t, 1680, GROUND, 440, side=-1)

        # 出口の外で待つアンドロイド（まだ小さい）
        s = 170 * android.HEIGHT
        ax, ay = 1415, GROUND + 6
        pts = android.front(ctx, ax, ay, s, hold=(ax - 0.06 * s, ay - 0.70 * s), tint=loc.NIGHT, t=t)
        umbrella.draw(ctx, *pts["hand_r"], 0.52 * s, angle=0.04, tint=loc.NIGHT, t=t)
        reflection(ctx, ax, ay + 4, 70, 110, umbrella.C["canopy"], 0.18, wobble=6, t=t)

        RIPPLES.draw(ctx, t)
        RAIN_FAR.draw(ctx, t, alpha=0.9)
        RAIN_MID.draw(ctx, t, light=lamp_r)
        RAIN_MID.draw(ctx, t + 3.3, light=lamp_l, alpha=0.5)
    RAIN_NEAR.draw(ctx, t)
    fade(ctx, 1 - smooth(t / 1.6))
