"""文字の描画。Pillow で文字を画像にし、cairo の画面に貼る。

日本語と英語を同じ仕組みで扱う。一度作った文字の画像は使い回す。
"""

from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import FONT_CANDIDATES, FONT_SERIF_CANDIDATES


def _find(candidates):
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError("フォントが見つかりません: " + ", ".join(map(str, candidates)))


@lru_cache(maxsize=None)
def font(size, serif=False, weight=None):
    f = ImageFont.truetype(_find(FONT_SERIF_CANDIDATES if serif else FONT_CANDIDATES), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except (OSError, AttributeError):
            pass  # 可変フォントでなければ太さは変えられない
    return f


def wrap(text, fnt, max_width, lang):
    """1行に収まらないときに折り返す。英語は単語ごと、日本語は文字ごと。"""
    if max_width is None:
        return text.split("\n")
    lines = []
    for para in text.split("\n"):
        units = para.split(" ") if lang == "en" else list(para)
        sep = " " if lang == "en" else ""
        cur = ""
        for u in units:
            trial = u if not cur else cur + sep + u
            if fnt.getlength(trial) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = u
        lines.append(cur)
    return lines


class TextImage:
    """cairo に貼れる文字の画像。surface の寿命のためにバッファも持っておく。"""

    def __init__(self, surface, buf, w, h):
        self.surface, self.buf, self.w, self.h = surface, buf, w, h

    def paint(self, ctx, x, y, alpha=1.0, anchor="center"):
        """anchor が center なら (x, y) が文字の中心、bottom なら下辺の中央。"""
        ox = x - self.w / 2
        oy = y - self.h / 2 if anchor == "center" else y - self.h
        ctx.save()
        ctx.set_source_surface(self.surface, ox, oy)
        ctx.paint_with_alpha(alpha)
        ctx.restore()


@lru_cache(maxsize=256)
def render(text, size, color=(255, 255, 255), lang="ja", serif=False, weight=None,
           max_width=None, line_gap=0.35, shadow=10, shadow_alpha=190, tracking=0):
    fnt = font(size, serif, weight)
    lines = wrap(text, fnt, max_width, lang)
    asc, desc = fnt.getmetrics()
    lh = asc + desc
    step = int(lh * (1 + line_gap))

    def line_w(s):
        return fnt.getlength(s) + tracking * max(len(s) - 1, 0)

    tw = int(max(line_w(s) for s in lines)) + 1
    th = step * (len(lines) - 1) + lh
    pad = shadow * 3 + 4
    w, h = tw + pad * 2, th + pad * 2

    def draw_lines(d, fill):
        for i, s in enumerate(lines):
            x = pad + (tw - line_w(s)) / 2
            y = pad + i * step
            if tracking:
                for ch in s:
                    d.text((x, y), ch, font=fnt, fill=fill)
                    x += fnt.getlength(ch) + tracking
            else:
                d.text((x, y), s, font=fnt, fill=fill)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_lines(ImageDraw.Draw(sh), (4, 6, 16, shadow_alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        # 影を少し濃くするために2回重ねる
        img = Image.alpha_composite(img, sh)
        img = Image.alpha_composite(img, sh)
    draw_lines(ImageDraw.Draw(img), tuple(color) + (255,))
    return to_cairo(img)


def to_cairo(img):
    a = np.asarray(img, dtype=np.uint16)
    alpha = a[..., 3:4]
    rgb_ = (a[..., :3] * alpha // 255).astype(np.uint8)
    bgra = np.concatenate([rgb_[..., ::-1], alpha.astype(np.uint8)], axis=2)
    h, w = bgra.shape[:2]
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = bytearray(stride * h)
    view = np.ndarray((h, stride // 4, 4), np.uint8, buf)
    view[:, :w] = bgra
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)
    return TextImage(surf, buf, w, h)
