"""設定画（sheet.png）を書き出す。

    .venv/Scripts/python -m engine.sheet characters/ossan characters/android props/umbrella

03_design/<種類>/<名前>/model.py を読み、そのモデルが持つ描き方（front / side / back など）を並べる。
モデルに sheet(ctx, w, h) があれば、それで描く。
"""

import sys

import cairo

from . import assets, text
from .config import ROOT
from .draw import rgb, src

SW, SH = 2400, 1350


def default_views(model):
    views = []
    if hasattr(model, "front"):
        views.append(("正面 front", lambda c, x, y, s: model.front(c, x, y, s)))
    if hasattr(model, "side"):
        views.append(("横 side", lambda c, x, y, s: model.side(c, x, y, s)))
        views.append(("歩き walk", lambda c, x, y, s: model.side(c, x, y, s, walk=0.25)))
    if hasattr(model, "back"):
        views.append(("後ろ back", lambda c, x, y, s: model.back(c, x, y, s)))
    return views


def render(kind_name):
    folder = ROOT / "03_design" / kind_name
    model = assets.load(folder / "model.py")
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
    ctx = cairo.Context(surf)
    src(ctx, "#ece8e1")
    ctx.paint()
    # 床の線
    src(ctx, "#cfc8bd")
    ctx.rectangle(0, SH - 230, SW, 2)
    ctx.fill()

    title = f"{getattr(model, 'NAME', kind_name)}  /  {getattr(model, 'NAME_EN', '')}"
    text.render(title, 56, color=(40, 38, 44), shadow=0, weight=600).paint(ctx, SW / 2, 70)

    if hasattr(model, "sheet"):
        model.sheet(ctx, SW, SH)
    else:
        views = getattr(model, "SHEET_VIEWS", None) or default_views(model)
        height = 880 * getattr(model, "HEIGHT", 1.0)
        n = len(views)
        for i, (label, fn) in enumerate(views):
            x = 80 + (SW - 480) * (i + 0.5) / n
            fn(ctx, x, SH - 230, height)
            text.render(label, 30, color=(90, 86, 96), shadow=0).paint(ctx, x, SH - 170)
    # 色見本
    colors = getattr(model, "C", {})
    x = SW - 300
    y = 170
    for name, col in colors.items():
        src(ctx, col)
        ctx.rectangle(x, y, 44, 30)
        ctx.fill()
        src(ctx, "#5a5660")
        ctx.select_font_face("Consolas")
        ctx.set_font_size(20)
        ctx.move_to(x + 56, y + 22)
        ctx.show_text(f"{name}  {col}")
        y += 40
    out = folder / "sheet.png"
    surf.write_to_png(str(out))
    return out


if __name__ == "__main__":
    for name in sys.argv[1:]:
        print(render(name))
