"""PL_c006: 後ろから。一本の傘に入って、夜の通りを歩き出す二人。

カメラはその場に残り、二人は少しずつ遠ざかる。
傘はおっさんが持ち、アンドロイドの側へ少し傾けている（おっさんの左肩は濡れる）。
歩幅の違う二人の足取りが、少しずつずれている。
"""

from engine import assets
from engine.config import H, W
from engine.draw import ease_in_out, ellipse, lerp, seg, smooth, src
from engine.fx import Rain, Ripples, reflection

DURATION = 6.0

loc = assets.location("station_rain")
ossan = assets.character("ossan")
android = assets.character("android")
umbrella = assets.prop("umbrella")

STREET = loc.Street(seed=6, vy=470, f=900, cam_h=1.6)
RAIN_FAR = Rain(61, 700, speed=(900, 1200), length=(14, 26), width=0.9, alpha=0.28)
RAIN_MID = Rain(62, 300, speed=(1400, 1800), length=(34, 56), width=1.3, alpha=0.30)
RAIN_NEAR = Rain(63, 50, speed=(2300, 2900), length=(120, 180), width=2.6, alpha=0.18)
RIPPLES = Ripples(64, rate=55, area=(200, 640, 1720, H + 40), size=(8, 36),
                  perspective=lambda y: 0.3 + (y - 600) / 420)


def draw(ctx, t, env):
    light = STREET.draw(ctx, t, travel=0.0)
    RIPPLES.draw(ctx, t)
    RAIN_FAR.draw(ctx, t)

    # 二人の位置（メートル）：カメラから d メートル先。歩くにつれて遠ざかる
    d = 3.0 + 0.62 * t
    px_m = STREET.scale_at(d)
    s_o = 1.70 * px_m
    s_a = 1.70 * android.HEIGHT * px_m
    ox, feet_y = STREET.proj(-0.27, 0, d)
    axx, _ = STREET.proj(0.30, 0, d)
    cx = (ox + axx) / 2
    scale = s_o / 560

    # 地面に映る傘の色
    reflection(ctx, cx, feet_y + 6, 260 * scale, 260 * scale, umbrella.C["canopy"], 0.16, wobble=10 * scale, t=t)
    src(ctx, "#000000", 0.3)
    ellipse(ctx, cx, feet_y + 2, 150 * scale, 14 * scale)
    ctx.fill()

    hold = (cx + 4 * scale, feet_y - 0.74 * s_o)
    android.back(ctx, axx, feet_y, s_a, walk=t * 0.95 + 0.3, walk_amt=0.9, tint=env.char_tint(loc.NIGHT), t=t)
    ossan.back(ctx, ox, feet_y, s_o, walk=t * 0.82, walk_amt=0.9, hold=hold, tint=env.char_tint(loc.NIGHT))
    umbrella.draw(ctx, *hold, 0.36 * s_o, angle=0.12, tint=env.prop_tint(("#1a2445", 0.12)), t=t)

    RAIN_MID.draw(ctx, t, light=light)
    RAIN_NEAR.draw(ctx, t)
    if t < 0.3:
        src(ctx, "#000000", 1 - smooth(t / 0.3))
        ctx.paint()
