"""PL_c008: 引きの画。雨の街の中の、小さなからし色の点。

カメラはゆっくり空へ上がり、タイトルが浮かぶ。最後は暗くなって終わる。
"""

from engine import assets, text
from engine.config import H, W
from engine.draw import camera, ease_in_out, glow, lerp, seg, smooth, src, fade
from engine.fx import Rain, Ripples, reflection

DURATION = 7.5

loc = assets.location("station_rain")
ossan = assets.character("ossan")
android = assets.character("android")
umbrella = assets.prop("umbrella")

GROUND = 900
RAIN_FAR = Rain(81, 1100, area=(0, -700, W, H), speed=(800, 1100), length=(12, 22), width=0.8, alpha=0.30)
RAIN_MID = Rain(82, 360, area=(0, -700, W, H), speed=(1300, 1700), length=(28, 46), width=1.1, alpha=0.26)
RIPPLES = Ripples(83, rate=60, area=(0, GROUND + 10, W, H + 80), size=(6, 26),
                  perspective=lambda y: 0.4 + (y - GROUND) / 250)


def draw(ctx, t, env):
    tilt = ease_in_out(seg(t, 1.2, 5.6))
    cy = lerp(560, 190, tilt)
    with camera(ctx, 1.0, 960, cy):
        loc.sky(ctx, -1100, GROUND, haze=1.0)
        loc.skyline(ctx, t, GROUND - 60, 81, loc.C["far"], 300, 640, win=0.30, win_size=(5, 7))
        loc.skyline(ctx, t, GROUND - 20, 82, loc.C["mid"], 160, 380, win=0.40, wmin=120, wmax=280)
        loc.skyline(ctx, t, GROUND, 83, loc.C["near"], 90, 200, win=0.55, wmin=160, wmax=320,
                    win_size=(14, 18), lit=0.5, beacons=False)
        loc.ground(ctx, GROUND, 400, t=t, lights=[(300, loc.C["lamp"], 60, 0.18), (1250, loc.C["lamp"], 60, 0.18)])
        l1 = loc.streetlamp(ctx, t, 230, GROUND, 300, side=1)
        l2 = loc.streetlamp(ctx, t, 1180, GROUND, 300, side=1)

        # 小さな二人
        x = lerp(760, 900, t / DURATION)
        s = 110
        hold = (x + 6, GROUND - 0.67 * s)
        android.side(ctx, x + 14, GROUND, s * android.HEIGHT, walk=t * 0.95, walk_amt=0.8,
                     tint=loc.NIGHT, t=t)
        ossan.side(ctx, x - 12, GROUND, s, walk=t * 0.82, walk_amt=0.8, arm="hold", target=hold,
                   tint=loc.NIGHT)
        umbrella.draw(ctx, *hold, 0.40 * s, angle=0.08, tint=("#1a2445", 0.05), t=t, shine=0.5)
        glow(ctx, x, GROUND - 0.9 * s, 60, umbrella.C["canopy"], 0.10)
        reflection(ctx, x, GROUND + 4, 40, 90, umbrella.C["canopy"], 0.2, wobble=4, t=t)

        RIPPLES.draw(ctx, t)
        RAIN_FAR.draw(ctx, t)
        RAIN_MID.draw(ctx, t, light=l2)

    # タイトル
    ta = smooth(seg(t, 3.6, 5.0)) * (1 - smooth(seg(t, 6.6, 7.3)))
    if ta > 0:
        title = text.render(env.text("title"), 76 if env.lang == "ja" else 70, color=(240, 236, 226),
                            lang=env.lang, serif=True, weight=500, tracking=10 if env.lang == "ja" else 2,
                            shadow=14)
        title.paint(ctx, W / 2, H * 0.42, alpha=ta)
        sub = text.render(env.text("subtitle"), 30, color=(200, 196, 190), lang=env.lang, serif=True,
                          tracking=6, shadow=8)
        sub.paint(ctx, W / 2, H * 0.42 + 90, alpha=ta * 0.9)
    fade(ctx, smooth(seg(t, 6.2, 7.4)))
