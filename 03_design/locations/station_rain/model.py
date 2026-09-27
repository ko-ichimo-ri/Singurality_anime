"""雨の夜の駅前（東京23区のどこか）と、そこから続く通り。

カットのスクリプトは、ここの部品を組み合わせて背景を作る。
色は夜の青を基調にし、駅の照明と窓の明かりだけをあたたかい色にする。
"""

import math

import cairo
import numpy as np

from engine import text
from engine.config import W, H
from engine.draw import TAU, glow, linear, radial, rrect, src, vgrad
from engine.fx import reflection

NAME = "雨の駅前"
NAME_EN = "Station front in the rain"

C = {
    "sky_top": "#060913",
    "sky_mid": "#111830",
    "haze": "#2c2a44",
    "far": "#0f1428",
    "mid": "#141a31",
    "near": "#1a2139",
    "wall": "#1c2236",
    "wall_dk": "#12172a",
    "glass": "#f3ead6",
    "glass_cool": "#cfe0ff",
    "canopy": "#0d111e",
    "sign": "#eef4ff",
    "ground": "#0a0e19",
    "ground_lt": "#1a2238",
    "win_warm": "#ffcf7f",
    "win_cool": "#9fc3ff",
    "lamp": "#ffd48a",
    "red": "#ff5a4f",
    "green": "#6cf0b0",
    "teal": "#72e3d4",
}

NIGHT = ("#1a2445", 0.30)   # キャラクターを夜の色に寄せる（shade の tint）
NIGHT_WARM = ("#3a2c3a", 0.18)  # 駅の明かりの下


# ---------------------------------------------------------------- 空と街並み

def sky(ctx, y0=0, y1=H, haze=0.8):
    vgrad(ctx, 0, y0, W, y1 - y0, [(0, C["sky_top"], 1), (0.7, C["sky_mid"], 1), (1, C["haze"], 1)])
    # 雲に街の明かりが映ったような、地平線近くのにじみ
    ctx.set_source(linear(0, y1 - (y1 - y0) * 0.45, 0, y1, [(0, "#3b2c46", 0), (1, "#4a3550", 0.35 * haze)]))
    ctx.rectangle(0, y0, W, y1 - y0)
    ctx.fill()


def skyline(ctx, t, base_y, seed, color, hmin, hmax, win=0.35, x0=-200, x1=W + 200,
            wmin=70, wmax=210, win_size=(7, 10), lit=0.35, beacons=True):
    """ビルのシルエットと窓の明かり。seed を変えると別の街並みになる。"""
    rng = np.random.default_rng(seed)
    x = x0
    src(ctx, color)
    boxes = []
    while x < x1:
        w = rng.uniform(wmin, wmax)
        h = rng.uniform(hmin, hmax)
        boxes.append((x, base_y - h, w, h))
        x += w + rng.uniform(-10, 18)
    for bx, by, bw, bh in boxes:
        ctx.rectangle(bx, by, bw, bh + 2)
    ctx.fill()
    if win <= 0:
        return
    ww, wh = win_size
    for i, (bx, by, bw, bh) in enumerate(boxes):
        r2 = np.random.default_rng(seed * 1000 + i)
        cols = int((bw - 16) // (ww * 2.2))
        rows = int((bh - 20) // (wh * 2.1))
        warm = r2.random() < 0.6
        for cx in range(cols):
            for cy in range(rows):
                if r2.random() > lit:
                    continue
                wx = bx + 10 + cx * ww * 2.2
                wy = by + 12 + cy * wh * 2.1
                flick = 1.0
                if r2.random() < 0.02:
                    flick = 0.4 + 0.6 * (math.sin(t * 3 + i + cx) > 0)
                src(ctx, C["win_warm"] if (warm or r2.random() < 0.2) else C["win_cool"],
                    win * r2.uniform(0.35, 1.0) * flick)
                ctx.rectangle(wx, wy, ww, wh)
                ctx.fill()
        if beacons and bh > hmax * 0.8 and r2.random() < 0.5:
            on = (math.sin(t * 2.2 + i * 1.3) > 0.2)
            if on:
                glow(ctx, bx + bw / 2, by - 4, 16, C["red"], 0.55, core=0.15)


# ---------------------------------------------------------------- 地面

def ground(ctx, y, h=None, lights=(), t=0.0):
    """濡れたアスファルト。lights = [(x, 色, 幅, 強さ)] の光が縦に映り込む。"""
    h = h if h is not None else H - y
    vgrad(ctx, 0, y, W, h, [(0, C["ground_lt"], 1), (0.25, C["ground"], 1), (1, "#06080f", 1)])
    for lx, col, lw, a in lights:
        reflection(ctx, lx, y, lw, h * 0.95, col, a, wobble=lw * 0.08, t=t)


# ---------------------------------------------------------------- 駅舎

def station(ctx, t, cx, ground_y, scale=1.0, sign=True):
    """駅舎の正面。cx が入口の中心。scale 1 で幅およそ 1160 ピクセル。"""
    s = scale
    ctx.save()
    ctx.translate(cx, ground_y)
    ctx.scale(s, s)
    # 建物
    src(ctx, C["wall"])
    ctx.rectangle(-580, -360, 1160, 360)
    ctx.fill()
    src(ctx, C["wall_dk"])
    ctx.rectangle(-580, -360, 1160, 26)
    ctx.fill()
    # 二階の細長い窓
    for i in range(14):
        x = -540 + i * 78
        if -250 < x < 200:
            continue
        src(ctx, C["win_cool"] if i % 3 else C["win_warm"], 0.20 + 0.1 * (i % 2))
        ctx.rectangle(x, -300, 44, 70)
        ctx.fill()
    # 入口のガラス（中の明かり）
    ctx.set_source(linear(0, -200, 0, 0, [(0, C["glass_cool"], 1), (1, C["glass"], 1)]))
    ctx.rectangle(-210, -200, 420, 200)
    ctx.fill()
    # ガラスの向こうの柱と改札の影
    src(ctx, "#8e8a86", 0.45)
    for x in (-150, -50, 50, 150):
        ctx.rectangle(x - 6, -200, 12, 200)
        ctx.fill()
    src(ctx, "#5a5a66", 0.55)
    for i in range(7):
        rrect(ctx, -170 + i * 52, -62, 22, 62, 4)
        ctx.fill()
    # 入口の窓枠
    src(ctx, C["wall_dk"])
    for x in (-210, -70, 70, 206):
        ctx.rectangle(x, -200, 5, 200)
        ctx.fill()
    # ひさし
    src(ctx, C["canopy"])
    ctx.rectangle(-380, -238, 760, 34)
    ctx.fill()
    ctx.set_source(linear(0, -206, 0, -196, [(0, C["glass"], 0.9), (1, C["glass"], 0)]))
    ctx.rectangle(-360, -206, 720, 10)
    ctx.fill()
    # 看板
    if sign:
        src(ctx, C["sign"], 0.95)
        rrect(ctx, -170, -330, 340, 66, 6)
        ctx.fill()
        label = text.render("北口   North Exit", 34, color=(25, 32, 58), shadow=0, weight=600)
        label.paint(ctx, 0, -297)
    ctx.restore()
    # 入口からこぼれる光
    glow(ctx, cx, ground_y - 100 * s, 520 * s, C["glass"], 0.22, core=0.1)
    if sign:
        glow(ctx, cx, ground_y - 297 * s, 260 * s, C["sign"], 0.10)


def streetlamp(ctx, t, x, ground_y, h=420, side=1):
    """街灯。光の輪と、光に照らされる雨の範囲を返す（雨を明るく描くための模様）。"""
    top = ground_y - h
    src(ctx, "#0b0e16")
    ctx.rectangle(x - 5, top, 10, h)
    ctx.fill()
    ctx.set_line_width(8)
    ctx.move_to(x, top + 4)
    ctx.curve_to(x, top - 30, x + side * 30, top - 40, x + side * 70, top - 34)
    ctx.stroke()
    lx, ly = x + side * 76, top - 26
    src(ctx, "#1a1d26")
    rrect(ctx, lx - 26, ly - 12, 52, 16, 5)
    ctx.fill()
    src(ctx, "#fff2d0")
    ctx.rectangle(lx - 20, ly + 2, 40, 4)
    ctx.fill()
    glow(ctx, lx, ly + 6, 120, C["lamp"], 0.35, core=0.05)
    # 光の円錐
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.move_to(lx - 18, ly + 6)
    ctx.line_to(lx + 18, ly + 6)
    ctx.line_to(lx + 170, ground_y)
    ctx.line_to(lx - 170, ground_y)
    ctx.close_path()
    ctx.set_source(linear(0, ly, 0, ground_y, [(0, C["lamp"], 0.16), (1, C["lamp"], 0.0)]))
    ctx.fill()
    ctx.restore()
    return radial(lx, ly + 150, 330, [(0, "#fff0c8", 0.9), (0.6, "#ffe2a8", 0.35), (1, "#ffe2a8", 0.0)])


# ---------------------------------------------------------------- 改札（駅の中）

def gates(ctx, t, floor_y, scroll=0.0):
    """改札のある駅の出口。明るい屋内から、右奥の雨の外へ抜けていく。"""
    # 天井と壁
    vgrad(ctx, 0, 0, W, floor_y, [(0, "#c9ccd6", 1), (0.35, "#e4e3dd", 1), (1, "#d6d2c8", 1)])
    # 天井の照明
    for i in range(7):
        x = -80 + i * 300 - scroll
        src(ctx, "#fbfaf4")
        rrect(ctx, x, 40, 200, 14, 7)
        ctx.fill()
        glow(ctx, x + 100, 50, 180, "#fffbea", 0.18)
    # 奥の壁の案内表示
    src(ctx, "#27324f")
    rrect(ctx, 210 - scroll * 0.6, 150, 420, 70, 6)
    ctx.fill()
    label = text.render("出口   Exit  →", 30, color=(240, 236, 220), shadow=0, weight=600)
    label.paint(ctx, 420 - scroll * 0.6, 185)
    # 床
    vgrad(ctx, 0, floor_y, W, H - floor_y, [(0, "#a7a49c", 1), (1, "#6f6d69", 1)])
    # 改札機の列
    for i in range(6):
        x = 60 + i * 300 - scroll
        gh = 400
        src(ctx, "#3a3f4d")
        rrect(ctx, x, floor_y - gh, 110, gh, 12)
        ctx.fill()
        src(ctx, "#596070")
        rrect(ctx, x + 10, floor_y - gh, 90, 40, 8)
        ctx.fill()
        on = C["teal"] if (i + int(t * 1.2)) % 5 else "#ff7a6a"
        glow(ctx, x + 55, floor_y - gh + 20, 40, on, 0.5, core=0.2)
        src(ctx, "#8a8f9c", 0.55)
        rrect(ctx, x + 110, floor_y - gh * 0.62, 150, 14, 7)
        ctx.fill()
        # 床に映る改札
        ctx.set_source(linear(0, floor_y, 0, floor_y + 120, [(0, "#3a3f4d", 0.35), (1, "#3a3f4d", 0)]))
        ctx.rectangle(x, floor_y, 110, 120)
        ctx.fill()


# ---------------------------------------------------------------- 奥へ続く通り

class Street:
    """後ろから見た、奥へまっすぐ続く通り。実際の寸法（メートル）で街を置き、画面に投影する。

    カメラは道の中央、高さ cam_h メートル。vx, vy は消失点（地平線の高さ）。
    travel を増やすと、カメラが奥へ進む。
    """

    ROAD = 5.5       # 道の中央から建物の壁まで（メートル）
    LAMP_X = 4.6
    NEAR = 0.6

    def __init__(self, seed=5, vx=960, vy=480, f=900, cam_h=1.6, length=160):
        self.vx, self.vy, self.f, self.cam_h = vx, vy, f, cam_h
        rng = np.random.default_rng(seed)
        self.buildings = []
        for side in (-1, 1):
            d = -10.0
            while d < length:
                ln = rng.uniform(6, 15)
                self.buildings.append({
                    "side": side, "d0": d, "d1": d + ln - rng.uniform(0, 0.6),
                    "h": rng.uniform(7, 22),
                    "col": [C["mid"], C["near"], "#171d33", "#1e2540"][rng.integers(4)],
                    "shop": [C["win_warm"], C["win_cool"], "#ffe2b0", C["win_warm"], None][rng.integers(5)],
                    "sign": [None, C["red"], C["teal"], "#c89cff", C["win_warm"], None][rng.integers(6)],
                    "seed": int(rng.integers(1 << 30)),
                })
                d += ln
        self.length = length

    def proj(self, x, y, d):
        d = max(d, self.NEAR)
        return self.vx + self.f * x / d, self.vy + self.f * (self.cam_h - y) / d

    def scale_at(self, d):
        """奥行き d の位置で、1メートルが何ピクセルか。"""
        return self.f / max(d, self.NEAR)

    def _quad(self, ctx, pts):
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.close_path()

    def _facade(self, ctx, side, d0, d1, y0, y1, x=None):
        x = side * self.ROAD if x is None else x
        return [self.proj(x, y0, d0), self.proj(x, y1, d0), self.proj(x, y1, d1), self.proj(x, y0, d1)]

    def draw(self, ctx, t, travel=0.0):
        """返り値：雨を明るく描くための光の模様。"""
        sky(ctx, 0, self.vy + 60)
        skyline(ctx, t, self.vy + 8, 21, C["far"], 30, 140, win=0.25, x0=self.vx - 520, x1=self.vx + 520,
                wmin=30, wmax=90, win_size=(3, 4), lit=0.3, beacons=False)
        # 道と歩道
        far = self.length
        road = [self.proj(-self.ROAD, 0, self.NEAR), self.proj(self.ROAD, 0, self.NEAR),
                self.proj(self.ROAD, 0, far), self.proj(-self.ROAD, 0, far)]
        self._quad(ctx, road)
        ctx.set_source(linear(0, self.vy, 0, H, [(0, C["ground_lt"], 1), (0.25, C["ground"], 1), (1, "#05070d", 1)]))
        ctx.fill()
        for side in (-1, 1):
            src(ctx, "#8f9ab5", 0.10)
            curb = [self.proj(side * 3.6, 0, self.NEAR), self.proj(side * 3.7, 0, self.NEAR),
                    self.proj(side * 3.7, 0, far), self.proj(side * 3.6, 0, far)]
            self._quad(ctx, curb)
            ctx.fill()
        # 中央の白線（カメラが進むと手前へ流れる）
        src(ctx, "#cdd3e0", 0.16)
        off = travel % 6.0
        for k in range(30):
            d0 = k * 6.0 - off + 1.0
            if d0 + 3 < self.NEAR:
                continue
            q = [self.proj(-0.07, 0, max(d0, self.NEAR)), self.proj(0.07, 0, max(d0, self.NEAR)),
                 self.proj(0.07, 0, d0 + 3), self.proj(-0.07, 0, d0 + 3)]
            self._quad(ctx, q)
            ctx.fill()
        # 建物（奥から手前へ）
        items = []
        for b in self.buildings:
            d0, d1 = b["d0"] - travel, b["d1"] - travel
            if d1 < self.NEAR or d0 > far:
                continue
            items.append((d0, b))
        for d0, b in sorted(items, key=lambda it: -it[0]):
            self._building(ctx, t, b, travel)
        # 街灯
        lights = []
        off = travel % 18.0
        for k in range(10):
            d = k * 18.0 - off + 4.0
            if d < 1.2:
                continue
            for side in (-1, 1):
                bx, by = self.proj(side * self.LAMP_X, 0, d)
                tx, ty = self.proj(side * self.LAMP_X, 6.2, d)
                hx, hy = self.proj(side * (self.LAMP_X - 1.0), 6.0, d)
                sc = self.scale_at(d)
                src(ctx, "#080a12")
                ctx.set_line_width(max(0.16 * sc, 1))
                ctx.move_to(bx, by)
                ctx.line_to(tx, ty)
                ctx.line_to(hx, hy)
                ctx.stroke()
                glow(ctx, hx, hy + 0.1 * sc, min(1.6 * sc, 420), C["lamp"], 0.45)
                reflection(ctx, hx, by, 0.9 * sc, min(3.5 * sc, 700), C["lamp"], 0.10, wobble=0.1 * sc, t=t)
                lights.append((hx, hy, sc))
        return radial(self.vx, self.vy + 120, 900, [(0, "#ffe7b8", 0.5), (1, "#ffe7b8", 0.0)])

    def _building(self, ctx, t, b, travel):
        side = b["side"]
        d0, d1 = max(b["d0"] - travel, self.NEAR), b["d1"] - travel
        # 壁
        self._quad(ctx, self._facade(ctx, side, d0, d1, 0, b["h"]))
        src(ctx, b["col"])
        ctx.fill()
        # 手前の側面（道に面した角）
        rng = np.random.default_rng(b["seed"])
        # 1階の店
        if b["shop"]:
            self._quad(ctx, self._facade(ctx, side, d0 + 0.6, d1 - 0.6, 0.2, 3.0, x=side * (self.ROAD - 0.02)))
            # 手前の店ほど暗くする（近すぎる明かりで画面がうるさくならないように）
            near = min(1.0, max(0.0, (d0 - 2.0) / 10.0))
            src(ctx, b["shop"], 0.12 + 0.33 * near)
            ctx.fill()
            self._quad(ctx, self._facade(ctx, side, d0 + 0.6, d1 - 0.6, 2.7, 3.0, x=side * (self.ROAD - 0.03)))
            src(ctx, "#0b0e18", 0.8)
            ctx.fill()
        # 上の階の窓
        floors = int((b["h"] - 4) // 3)
        cols = int((d1 - d0) // 2.4)
        for fl in range(floors):
            y0 = 4.2 + fl * 3
            for c in range(cols):
                if rng.random() > 0.4:
                    continue
                wd0 = d0 + 0.6 + c * 2.4
                col = C["win_warm"] if rng.random() < 0.6 else C["win_cool"]
                self._quad(ctx, self._facade(ctx, side, wd0, wd0 + 1.2, y0, y0 + 1.5, x=side * (self.ROAD - 0.02)))
                src(ctx, col, rng.uniform(0.25, 0.6))
                ctx.fill()
        # 看板
        if b["sign"]:
            sx, sy = self.proj(side * (self.ROAD - 0.5), 4.2, d0 + 1.2)
            sc = self.scale_at(d0 + 1.2)
            self._quad(ctx, [self.proj(side * (self.ROAD - 0.05), 3.4, d0 + 1.0),
                             self.proj(side * (self.ROAD - 0.05), 5.4, d0 + 1.0),
                             self.proj(side * (self.ROAD - 0.9), 5.4, d0 + 1.0),
                             self.proj(side * (self.ROAD - 0.9), 3.4, d0 + 1.0)])
            src(ctx, b["sign"], 0.75)
            ctx.fill()
            glow(ctx, sx, sy, min(2.2 * sc, 500), b["sign"], 0.22)
