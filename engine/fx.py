"""画面効果：雨、波紋、しずく、光のにじみ（ボケ）、仕上げ（周辺減光・粒子）。

どの効果も「時刻 t を渡すと、その瞬間の姿を描く」作りにしてある。
乱数は seed で固定するので、何度書き出しても同じ映像になる。
"""

import math

import cairo
import numpy as np

from .config import W, H
from .draw import TAU, rgb, radial, clamp, ellipse


class Rain:
    """降る雨。奥・中・手前の層を分けて重ねると奥行きが出る。"""

    def __init__(self, seed, count, area=(0, 0, W, H), speed=(1500, 2100), length=(30, 60),
                 width=1.2, angle=0.13, alpha=0.35, color="#c9d6ff"):
        rng = np.random.default_rng(seed)
        self.area = area
        x0, y0, x1, y1 = area
        self.span = (y1 - y0) + 200
        self.n = count
        self.x = rng.uniform(x0 - 200, x1 + 200, count)
        self.y = rng.uniform(0, self.span, count)
        self.v = rng.uniform(*speed, count)
        self.len = rng.uniform(*length, count)
        self.a = rng.uniform(0.45, 1.0, count)
        self.width = width
        self.angle = angle
        self.alpha = alpha
        self.color = color

    def draw(self, ctx, t, light=None, alpha=1.0, gust=0.0):
        """light を渡すと、その模様（グラデーション）で雨粒を塗る。街灯の近くだけ明るい雨になる。"""
        x0, y0, _, _ = self.area
        tan = math.tan(self.angle + gust)
        ys = (self.y + self.v * t) % self.span - 100 + y0
        xs = self.x + (ys - y0) * tan
        dx = self.len * tan / math.hypot(1, tan) * 1.0
        dy = self.len / math.hypot(1, tan)
        ctx.save()
        ctx.set_line_width(self.width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        # 明るさの違う3束に分けて描く（1本ずつ色を変えるより速い）
        for k, lo, hi in ((0, 0.0, 0.6), (1, 0.6, 0.85), (2, 0.85, 1.01)):
            mask = (self.a >= lo) & (self.a < hi)
            if not mask.any():
                continue
            for x, y, ddx, ddy in zip(xs[mask], ys[mask], dx[mask], dy[mask]):
                ctx.move_to(x, y)
                ctx.line_to(x - ddx, y - ddy)
            a = self.alpha * alpha * (0.5 + 0.25 * k)
            r, g, b = rgb(self.color)
            if light is not None:
                # 光の当たるところは明るく、それ以外はうっすら
                ctx.set_source(light)
                ctx.stroke_preserve()
                ctx.set_source_rgba(r, g, b, a * 0.35)
            else:
                ctx.set_source_rgba(r, g, b, a)
            ctx.stroke()
        ctx.restore()


class Ripples:
    """水たまりに落ちる雨の波紋。area の中にランダムに現れては広がって消える。"""

    def __init__(self, seed, rate, area, size=(10, 28), life=0.7, squash=0.28,
                 color="#dfe7ff", alpha=0.35, perspective=None):
        self.rng_seed = seed
        self.rate = rate
        self.area = area
        self.size = size
        self.life = life
        self.squash = squash
        self.color = color
        self.alpha = alpha
        # perspective(y) → 大きさの倍率。奥ほど小さくしたいときに使う
        self.perspective = perspective

    def draw(self, ctx, t):
        x0, y0, x1, y1 = self.area
        first = int((t - self.life) * self.rate) - 1
        last = int(t * self.rate) + 1
        r, g, b = rgb(self.color)
        ctx.save()
        ctx.set_line_width(1.4)
        for k in range(max(first, -10_000), last + 1):
            born = k / self.rate
            age = (t - born) / self.life
            if not 0 <= age < 1:
                continue
            h = (k * 2654435761 + self.rng_seed * 97) & 0xFFFFFFFF
            u = (h & 0xFFFF) / 0xFFFF
            v = (h >> 16) / 0xFFFF
            x = x0 + (x1 - x0) * u
            y = y0 + (y1 - y0) * v
            s = self.size[0] + (self.size[1] - self.size[0]) * ((h >> 7) % 97) / 96
            if self.perspective:
                s *= self.perspective(y)
            rad = s * (0.2 + age)
            a = self.alpha * (1 - age) ** 1.5
            ctx.set_source_rgba(r, g, b, a)
            ellipse(ctx, x, y, rad, rad * self.squash)
            ctx.stroke()
            if age < 0.5:
                ctx.set_source_rgba(r, g, b, a * 0.6)
                ellipse(ctx, x, y, rad * 0.5, rad * 0.5 * self.squash)
                ctx.stroke()
        ctx.restore()


class Drips:
    """傘のふちなどから落ちるしずく。points(t) が落ちはじめの位置のリストを返す。"""

    def __init__(self, seed, interval=0.55, fall=220, color="#e6eeff", alpha=0.7):
        self.seed = seed
        self.interval = interval
        self.fall = fall
        self.color = color
        self.alpha = alpha

    def draw(self, ctx, t, points, g=2200, size=3.0):
        r, gg, b = rgb(self.color)
        for i, (px, py) in enumerate(points):
            off = ((i * 7919 + self.seed * 31) % 100) / 100 * self.interval
            ph = (t + off) % self.interval
            fall_t = ph
            dy = 0.5 * g * fall_t ** 2
            if dy > self.fall:
                continue
            a = self.alpha * (1 - dy / self.fall)
            ctx.set_source_rgba(r, gg, b, a)
            ellipse(ctx, px, py + dy, size * 0.7, size * (1 + fall_t * 3))
            ctx.fill()


def bokeh(ctx, t, lights, drift=0.0):
    """光のにじみ。lights = [(x, y, 半径, 色, 不透明度), ...]。雨の夜のピンボケの街灯り。"""
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for i, (x, y, r, color, a) in enumerate(lights):
        flick = 0.85 + 0.15 * math.sin(t * (0.7 + (i % 5) * 0.23) + i)
        xx = x + drift * t
        ctx.set_source(radial(xx, y, r, [(0, color, a * 0.55 * flick), (0.72, color, a * 0.45 * flick),
                                          (0.9, color, a * 0.6 * flick), (1, color, 0)]))
        ctx.arc(xx, y, r, 0, TAU)
        ctx.fill()
    ctx.restore()


def scatter_lights(seed, n, area, radius, colors, alpha):
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = area
    out = []
    for _ in range(n):
        out.append((rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(*radius),
                    colors[rng.integers(len(colors))], rng.uniform(*alpha)))
    return out


def reflection(ctx, x, y, w, length, color, a, wobble=0.0, t=0.0):
    """濡れた地面に映る光の縦の帯。横は中央が明るく、縦は下へいくほど薄くなる。"""
    off = wobble * math.sin(t * 2.3 + x * 0.01)
    ww = w * 1.25
    r, gg, b = rgb(color)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    g = cairo.LinearGradient(x - ww / 2 + off, 0, x + ww / 2 + off, 0)
    g.add_color_stop_rgba(0, r, gg, b, 0)
    g.add_color_stop_rgba(0.5, r, gg, b, a)
    g.add_color_stop_rgba(1, r, gg, b, 0)
    m = cairo.LinearGradient(0, y, 0, y + length)
    m.add_color_stop_rgba(0, 0, 0, 0, 1)
    m.add_color_stop_rgba(0.25, 0, 0, 0, 0.6)
    m.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.rectangle(x - ww / 2 + off, y, ww, length)
    ctx.clip()
    ctx.set_source(g)
    ctx.mask(m)
    ctx.restore()


# ---------------------------------------------------------------- 仕上げ

class Finish:
    """全カット共通の仕上げ。周辺減光と、フィルムのような細かい粒子。"""

    def __init__(self, w=W, h=H, grain=5.0, vignette=0.42, seed=3):
        rng = np.random.default_rng(seed)
        self.w, self.h = w, h
        # 粒子は数枚を用意して順に使う（毎フレーム作ると遅い）
        self.tiles = [rng.normal(0, grain, (h, w, 1)).astype(np.int16) for _ in range(4)] if grain > 0 else []
        self.vignette = vignette

    def apply(self, surface, frame):
        if self.vignette <= 0 and not self.tiles:
            return
        ctx = cairo.Context(surface)
        sw, sh = surface.get_width(), surface.get_height()
        g = cairo.RadialGradient(sw / 2, sh / 2, sh * 0.35, sw / 2, sh / 2, sh * 0.95)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0.01, 0.01, 0.04, self.vignette)
        ctx.set_source(g)
        ctx.paint()
        surface.flush()
        if not self.tiles:
            return
        buf = np.ndarray((sh, surface.get_stride() // 4, 4), np.uint8, surface.get_data())[:, :sw]
        tile = self.tiles[frame % len(self.tiles)]
        if tile.shape[0] != sh or tile.shape[1] != sw:
            tile = tile[:sh, :sw]
        rgb_ = buf[..., :3].astype(np.int16) + tile
        np.clip(rgb_, 0, 255, out=rgb_)
        buf[..., :3] = rgb_.astype(np.uint8)
        surface.mark_dirty()
