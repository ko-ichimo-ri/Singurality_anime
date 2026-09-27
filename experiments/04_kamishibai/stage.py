"""紙芝居版の舞台と絵。

パイロット版の各カットから「決めの一瞬」を1枚ずつ取り出し、水彩の絵にして、木の舞台で見せる。
カットの終わりに絵を右へ引き抜くと、次の絵が現れる。最後はタイトルの紙が出てくる。
"""

import cairo
import numpy as np

from engine import assets, text
from engine.config import H, W
from engine.draw import TAU, ease_in, ease_in_out, glow, lerp, linear, rrect, seg, smooth, src, fade
from engine.styles import watercolor

PW, PH = 1400, 788            # 絵の大きさ
PX, PY = (W - PW) / 2, 92     # 絵の左上
PULL = 0.8                    # 絵を引き抜くのにかける秒数

# カットごとの「決めの一瞬」（パイロット版のカットの中の秒数）
KEYS = {
    "PL_c001": 3.8, "PL_c002": 4.2, "PL_c003": 3.9, "PL_c004": 3.6,
    "PL_c005": 2.2, "PL_c006": 1.4, "PL_c007": 4.6, "PL_c008": 1.2,
}
ORDER = list(KEYS)

_pictures = {}


class _Env:
    """パイロット版のカットを1枚だけ描くときに渡す、最小限の情報。"""

    def __init__(self, lang, texts):
        self.lang, self.texts, self.T = lang, texts, 0.0

    def text(self, key):
        return self.texts.get(key, {}).get(self.lang, "")

    def char_tint(self, tint=None):
        return tint

    def prop_tint(self, tint=None):
        return tint


def _to_surface(arr):
    h, w = arr.shape[:2]
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = bytearray(stride * h)
    np.ndarray((h, stride // 4, 4), np.uint8, buf)[:, :w] = arr
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)
    surf._buf = buf
    return surf


def _watercolor(surf):
    surf.flush()
    arr = np.ndarray((H, surf.get_stride() // 4, 4), np.uint8, surf.get_data())[:, :W]
    watercolor.post(arr, 0)
    surf.mark_dirty()
    return surf


def picture(cut_id, env):
    """1枚の絵（1920×1080 の cairo の画面）。一度描いたら使い回す。"""
    key = (cut_id, env.lang)
    if key in _pictures:
        return _pictures[key]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    if cut_id == "title":
        _title_card(ctx, env)
    else:
        base = assets.load(f"pilot/cuts/{cut_id}/cut.py")
        base.draw(ctx, KEYS[cut_id], _Env(env.lang, env.texts))
    _pictures[key] = _watercolor(surf)
    return _pictures[key]


def _title_card(ctx, env):
    src(ctx, "#f1ebdd")
    ctx.paint()
    umbrella = assets.prop("umbrella")
    umbrella.draw(ctx, W / 2, 640, 120, angle=0.08)
    title = text.render(env.text("title"), 92 if env.lang == "ja" else 84, color=(52, 46, 52), lang=env.lang,
                        serif=True, weight=500, tracking=12 if env.lang == "ja" else 2, shadow=0)
    title.paint(ctx, W / 2, 800)
    sub = text.render(env.text("subtitle"), 38, color=(120, 110, 110), lang=env.lang, serif=True,
                      tracking=8, shadow=0)
    sub.paint(ctx, W / 2, 900)


# ---------------------------------------------------------------- 舞台

def room(ctx):
    """部屋と、紙芝居の木の舞台（絵のまわり）。"""
    ctx.set_source(linear(0, 0, 0, H, [(0, "#1c1512", 1), (1, "#2a1f19", 1)]))
    ctx.paint()
    glow(ctx, W / 2, 80, 1100, "#ffd9a0", 0.22)
    # 台
    ctx.set_source(linear(0, 930, 0, H, [(0, "#5a3c28", 1), (1, "#3a261a", 1)]))
    ctx.rectangle(0, 930, W, H - 930)
    ctx.fill()
    # 舞台の枠
    fx, fy, fw, fh = PX - 58, PY - 58, PW + 116, PH + 104
    src(ctx, "#6b4527")
    rrect(ctx, fx, fy, fw, fh, 10)
    ctx.fill()
    ctx.set_source(linear(fx, 0, fx + fw, 0, [(0, "#8a5c35", 0.6), (0.5, "#8a5c35", 0.0), (1, "#3d2715", 0.5)]))
    rrect(ctx, fx, fy, fw, fh, 10)
    ctx.fill()
    # 木目
    src(ctx, "#4d311c", 0.35)
    ctx.set_line_width(2)
    for k in range(9):
        y = fy + 8 + k * (fh - 16) / 8
        ctx.move_to(fx + 6, y)
        ctx.curve_to(fx + fw * 0.3, y + 6, fx + fw * 0.7, y - 6, fx + fw - 6, y + 2)
        ctx.stroke()
    # 開いた扉（左右）
    for side in (-1, 1):
        x0 = fx if side < 0 else fx + fw
        x1 = x0 + side * 150
        src(ctx, "#5e3c22")
        ctx.move_to(x0, fy - 10)
        ctx.line_to(x1, fy + 40)
        ctx.line_to(x1, fy + fh - 40)
        ctx.line_to(x0, fy + fh + 10)
        ctx.close_path()
        ctx.fill()
        src(ctx, "#3d2715", 0.6)
        ctx.set_line_width(3)
        ctx.move_to(x0 + side * 8, fy)
        ctx.line_to(x0 + side * 8, fy + fh)
        ctx.stroke()
    # 絵の入る窓（奥の暗さ）
    src(ctx, "#140e0a")
    ctx.rectangle(PX - 6, PY - 6, PW + 12, PH + 12)
    ctx.fill()


def frame_lip(ctx):
    """絵の手前にかぶさる枠の縁（絵が枠の中に差し込まれているように見せる）。"""
    src(ctx, "#6b4527")
    ctx.rectangle(PX - 58, PY - 58, PW + 116, 52)
    ctx.fill()
    ctx.set_source(linear(0, PY - 8, 0, PY + 18, [(0, "#000000", 0.45), (1, "#000000", 0.0)]))
    ctx.rectangle(PX, PY - 6, PW, 24)
    ctx.fill()


def card(ctx, surf, x, zoom=1.0, focus=(0.5, 0.5)):
    """絵を1枚、窓の中に描く。x は右へずらす量（引き抜き）。"""
    ctx.save()
    ctx.rectangle(PX + x, PY, PW, PH)
    ctx.clip()
    ctx.translate(PX + x + PW * focus[0], PY + PH * focus[1])
    ctx.scale(PW / W * zoom, PH / H * zoom)
    ctx.translate(-W * focus[0], -H * focus[1])
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
    if x > 0:
        # 引き抜かれる紙の左端の影
        ctx.set_source(linear(PX + x - 30, 0, PX + x, 0, [(0, "#000000", 0.0), (1, "#000000", 0.45)]))
        ctx.rectangle(PX + x - 30, PY, 30, PH)
        ctx.fill()


def make(cut_id, duration):
    """パイロット版のカットと同じ長さの、紙芝居のカットを作る。draw と overlay を返す。"""
    i = ORDER.index(cut_id)
    nxt = ORDER[i + 1] if i + 1 < len(ORDER) else "title"
    last = nxt == "title"
    pull_at = 3.3 if last else duration - PULL

    def draw(ctx, t, env):
        room(ctx)
        # 引き抜いたあとに現れる次の絵（最後はタイトルの紙）
        if t > pull_at:
            card(ctx, picture(nxt, env), 0, zoom=1.0)
        pull = ease_in(seg(t, pull_at, pull_at + PULL)) * (PW + 160)
        if pull < PW + 150:
            zoom = lerp(1.0, 1.06, ease_in_out(seg(t, 0, pull_at)))
            card(ctx, picture(cut_id, env), pull, zoom=zoom)
        frame_lip(ctx)
        if last:
            fade(ctx, smooth(seg(t, duration - 1.3, duration)))
        elif i == 0:
            fade(ctx, 1 - smooth(seg(t, 0, 1.2)))

    return duration, draw
