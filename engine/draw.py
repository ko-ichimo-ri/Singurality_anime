"""描画の基本部品：色、形、グラデーション、カメラ、時間のカーブ。"""

import math
from contextlib import contextmanager

import cairo

from .config import W, H

TAU = math.tau


# ---------------------------------------------------------------- 色

def rgb(color):
    """'#rrggbb' または (r, g, b) を 0〜1 の (r, g, b) にする。"""
    if isinstance(color, str):
        c = color.lstrip("#")
        return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(color)


def mix(c1, c2, t):
    a, b = rgb(c1), rgb(c2)
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def shade(color, tint=None):
    """夜の光などで色を寄せる。tint = (色, 割合)。"""
    if tint is None:
        return rgb(color)
    return mix(color, tint[0], tint[1])


def src(ctx, color, a=1.0, tint=None):
    r, g, b = shade(color, tint)
    ctx.set_source_rgba(r, g, b, a)


# ---------------------------------------------------------------- 時間のカーブ

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, t0, t1):
    """t が t0→t1 の間で 0→1 に進む。"""
    if t1 == t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def overshoot(x, k=1.6):
    x = clamp(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


# ---------------------------------------------------------------- 形

def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -TAU / 4, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, TAU / 4)
    ctx.arc(x + r, y + h - r, r, TAU / 4, TAU / 2)
    ctx.arc(x + r, y + r, r, TAU / 2, TAU * 3 / 4)
    ctx.close_path()


def capsule(ctx, x0, y0, x1, y1, w0, w1=None):
    """(x0,y0)→(x1,y1) の、両端が丸い棒（太さ w0→w1）のパス。"""
    if w1 is None:
        w1 = w0
    a = math.atan2(y1 - y0, x1 - x0)
    ctx.new_sub_path()
    ctx.arc(x1, y1, w1 / 2, a - TAU / 4, a + TAU / 4)
    ctx.arc(x0, y0, w0 / 2, a + TAU / 4, a + TAU * 3 / 4)
    ctx.close_path()


def limb_end(x, y, angle, length):
    """角度 0 で真下、正の角度で +x 側へ振れる。"""
    return x + length * math.sin(angle), y + length * math.cos(angle)


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


# ---------------------------------------------------------------- グラデーション

def linear(x0, y0, x1, y1, stops):
    """stops = [(位置, 色, 不透明度), ...]"""
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, color, a in stops:
        r, gg, b = rgb(color)
        g.add_color_stop_rgba(off, r, gg, b, a)
    return g


def radial(x, y, r, stops, r0=0.0):
    g = cairo.RadialGradient(x, y, r0, x, y, r)
    for off, color, a in stops:
        r_, g_, b_ = rgb(color)
        g.add_color_stop_rgba(off, r_, g_, b_, a)
    return g


def vgrad(ctx, x, y, w, h, stops):
    ctx.rectangle(x, y, w, h)
    ctx.set_source(linear(0, y, 0, y + h, stops))
    ctx.fill()


def glow(ctx, x, y, r, color, a=1.0, core=0.0):
    """やわらかい光の玉。core は芯の大きさ（0〜1）。"""
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(radial(x, y, r, [(0, color, a), (max(core, 0.001), color, a * 0.85), (1, color, 0)]))
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- カメラ

@contextmanager
def camera(ctx, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0):
    """画面の中心に (cx, cy) が来るように拡大して映す。"""
    ctx.save()
    ctx.translate(W / 2, H / 2)
    ctx.scale(zoom, zoom)
    ctx.rotate(rot)
    ctx.translate(-cx, -cy)
    try:
        yield
    finally:
        ctx.restore()


@contextmanager
def place(ctx, x, y, s=1.0, flip=False, rot=0.0):
    """足もとを (x, y) に置き、高さ 1 を s ピクセルとして描く。"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(-s if flip else s, s)
    try:
        yield
    finally:
        ctx.restore()


def fade(ctx, a, color="#000000"):
    if a <= 0:
        return
    src(ctx, color, clamp(a))
    ctx.paint()
