"""アンドロイドが持ってくる傘。

雨の夜の青い画面の中で、唯一のあたたかい色（からし色）。二人の距離をつなぐ小道具なので、どのカットでも目立たせる。
手でにぎる位置 (hx, hy) を基準に描く。angle は軸の傾き（0 でまっすぐ上、正で +x 側へ倒れる）。
"""

import math

from engine.draw import TAU, linear, src, ellipse
from engine.rig import Anchor

NAME = "傘"
NAME_EN = "Umbrella"
HEIGHT = 0.9

C = {
    "canopy": "#d6a03f",
    "canopy_lt": "#efc56c",
    "canopy_dk": "#a8762a",
    "under": "#7d5520",
    "shaft": "#3b3b42",
    "handle": "#6e4a31",
}

RIBS = 8


def draw(ctx, hx, hy, r, angle=0.0, tint=None, t=0.0, shine=1.0, under=0.0):
    """r は開いた傘の半径（ピクセル）。under は下からのぞく角度（0〜1、下から見上げると内側が見える）。

    返り値：rim（縁の先端の位置のリスト。しずくを落とすのに使う）、top（てっぺん）
    """
    anchor = Anchor(ctx)
    L = 1.05 * r        # 手からてっぺんまで
    h = 0.40 * r        # 傘の高さ
    rim_y = -L + h
    pts = {}
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(angle)
    # 軸と持ち手
    src(ctx, C["shaft"], 1, tint)
    ctx.set_line_width(max(r * 0.022, 1.2))
    ctx.move_to(0, 0.04 * r)
    ctx.line_to(0, -L)
    ctx.stroke()
    src(ctx, C["handle"], 1, tint)
    ctx.set_line_width(max(r * 0.05, 2))
    ctx.move_to(0, -0.02 * r)
    ctx.line_to(0, 0.12 * r)
    ctx.curve_to(0, 0.22 * r, -0.13 * r, 0.22 * r, -0.13 * r, 0.14 * r)
    ctx.stroke()
    # 縁の先端
    tips = []
    for i in range(RIBS + 1):
        u = i / RIBS
        x = -r + 2 * r * u
        y = rim_y + 0.035 * r * math.sin(math.pi * u)
        tips.append((x, y))
    # 下からのぞいたときの内側
    if under > 0:
        src(ctx, C["under"], 1, tint)
        ctx.move_to(*tips[0])
        for i in range(RIBS):
            (x0, y0), (x1, y1) = tips[i], tips[i + 1]
            ctx.curve_to(x0 + (x1 - x0) * 0.3, y0 - 0.075 * r, x0 + (x1 - x0) * 0.7, y1 - 0.075 * r, x1, y1)
        ctx.curve_to(r * 0.6, rim_y + 0.25 * r * under, -r * 0.6, rim_y + 0.25 * r * under, *tips[0])
        ctx.fill()
    # 傘の布
    ctx.move_to(*tips[0])
    ctx.curve_to(-r * 0.98, rim_y - h * 0.85, -r * 0.50, -L, 0, -L)
    ctx.curve_to(r * 0.50, -L, r * 0.98, rim_y - h * 0.85, *tips[-1])
    for i in range(RIBS, 0, -1):
        (x0, y0), (x1, y1) = tips[i], tips[i - 1]
        ctx.curve_to(x0 + (x1 - x0) * 0.3, y0 - 0.075 * r, x0 + (x1 - x0) * 0.7, y1 - 0.075 * r, x1, y1)
    ctx.close_path()
    src(ctx, C["canopy"], 1, tint)
    ctx.fill_preserve()
    ctx.set_source(linear(-r, -L, r, rim_y, [(0, C["canopy_lt"], 0.9), (0.45, C["canopy_lt"], 0.0),
                                             (0.75, C["canopy_dk"], 0.35), (1, C["canopy_dk"], 0.9)], tint=tint))
    ctx.fill()
    # 骨
    src(ctx, C["canopy_dk"], 0.55, tint)
    ctx.set_line_width(max(r * 0.008, 0.8))
    for x, y in tips[1:-1]:
        ctx.move_to(0, -L)
        ctx.curve_to(x * 0.55, -L + 0.02 * r, x * 0.92, y - h * 0.45, x, y)
        ctx.stroke()
    # 縁の影
    src(ctx, C["under"], 0.55, tint)
    ctx.set_line_width(max(r * 0.02, 1))
    ctx.move_to(*tips[0])
    for i in range(RIBS):
        (x0, y0), (x1, y1) = tips[i], tips[i + 1]
        ctx.curve_to(x0 + (x1 - x0) * 0.3, y0 - 0.075 * r, x0 + (x1 - x0) * 0.7, y1 - 0.075 * r, x1, y1)
    ctx.stroke()
    # 濡れたつや
    if shine > 0:
        ctx.set_line_width(max(r * 0.018, 1))
        for k, (a0, a1) in enumerate(((0.18, 0.42), (0.52, 0.62))):
            src(ctx, "#fff6dc", (0.30 - 0.1 * k) * shine, tint)
            ctx.move_to(-r * (1 - a0) * 0.9, rim_y - h * (0.55 + a0 * 0.6))
            ctx.curve_to(-r * 0.6, -L + h * 0.18, -r * 0.3, -L + h * 0.02, -r * (1 - a1) * 0.5, -L + h * 0.02)
            ctx.stroke()
    # 石突き
    src(ctx, C["shaft"], 1, tint)
    ctx.set_line_width(max(r * 0.03, 1.5))
    ctx.move_to(0, -L)
    ctx.line_to(0, -L - 0.08 * r)
    ctx.stroke()
    pts["rim"] = [anchor.point(ctx, x, y) for x, y in tips]
    pts["top"] = anchor.point(ctx, 0, -L)
    ctx.restore()
    return pts


SHEET_VIEWS = [
    ("まっすぐ upright", lambda c, x, y, s: draw(c, x, y - s * 0.30, s * 0.42)),
    ("傾けて tilted", lambda c, x, y, s: draw(c, x, y - s * 0.30, s * 0.42, angle=0.35)),
    ("見上げ from below", lambda c, x, y, s: draw(c, x, y - s * 0.30, s * 0.42, under=1.0)),
]
