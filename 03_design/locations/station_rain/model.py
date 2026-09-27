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
        x = 120 + i * 230 - scroll
        src(ctx, "#3a3f4d")
        rrect(ctx, x, floor_y - 170, 70, 170, 8)
        ctx.fill()
        src(ctx, "#596070")
        rrect(ctx, x + 8, floor_y - 170, 54, 22, 5)
        ctx.fill()
        on = C["teal"] if (i + int(t * 1.2)) % 5 else "#ff7a6a"
        glow(ctx, x + 35, floor_y - 150, 26, on, 0.5, core=0.2)
        src(ctx, "#8a8f9c", 0.5)
        ctx.rectangle(x + 70, floor_y - 110, 90, 8)
        ctx.fill()
        # 床に映る改札
        ctx.set_source(linear(0, floor_y, 0, floor_y + 120, [(0, "#3a3f4d", 0.35), (1, "#3a3f4d", 0)]))
        ctx.rectangle(x, floor_y, 70, 120)
        ctx.fill()


# ---------------------------------------------------------------- 奥へ続く通り

def street(ctx, t, vp=(960, 520), ground_y=520, depth=0.0, lamps=True, blur=0.0):
    """後ろから見た、奥へまっすぐ続く通り。depth を増やすと奥へ進んだように見える。

    返り値：雨を明るく描くための光の模様（なければ None）
    """
    vx, vy = vp
    sky(ctx, 0, ground_y + 40)
    skyline(ctx, t, ground_y + 30, 21, C["far"], 60, 220, win=0.25, x0=vx - 700, x1=vx + 700,
            wmin=40, wmax=110, win_size=(4, 6), lit=0.3)
    # 左右の建物（遠近法の壁）
    for side in (-1, 1):
        ctx.move_to(vx + side * 90, vy - 150)
        ctx.line_to(vx + side * 1400, -600)
        ctx.line_to(vx + side * 1400, H + 400)
        ctx.line_to(vx + side * 90, vy + 18)
        ctx.close_path()
        ctx.set_source(linear(vx, 0, vx + side * 1100, 0, [(0, C["mid"], 1), (1, "#0b0f1d", 1)]))
        ctx.fill()
        # 窓と店の明かり：奥から手前へ流れる
        for k in range(22):
            u = ((k * 0.13 + depth * 0.08) % 1.0)
            z = 0.06 + u ** 2.2 * 1.2
            px = vx + side * (90 + (1400 - 90) * z)
            top = vy - 150 + (-600 - (vy - 150)) * z
            bot = vy + 18 + (H + 400 - (vy + 18)) * z
            hgt = bot - top
            wcol = C["win_warm"] if (k * 7) % 3 else C["win_cool"]
            a = 0.55 * min(1, z * 3) * (1 - blur * 0.3)
            ww = 20 + 160 * z
            # 店の明かり（1階）
            src(ctx, wcol, a * 0.8)
            ctx.rectangle(px - side * ww * 0.3 - ww / 2, bot - hgt * 0.25, ww, hgt * 0.12)
            ctx.fill()
            # 上の階の窓
            if (k * 5) % 4:
                src(ctx, wcol, a * 0.45)
                ctx.rectangle(px - ww / 2, top + hgt * 0.35, ww * 0.6, hgt * 0.05)
                ctx.fill()
            # 看板
            if k % 4 == 1:
                col = [C["red"], C["teal"], C["win_warm"], "#c89cff"][(k // 4) % 4]
                glow(ctx, px, top + hgt * 0.55, 40 + 90 * z, col, 0.35 * min(1, z * 3))
    # 道路
    ctx.move_to(vx - 90, vy + 18)
    ctx.line_to(vx + 90, vy + 18)
    ctx.line_to(vx + 1400, H + 400)
    ctx.line_to(vx - 1400, H + 400)
    ctx.close_path()
    ctx.set_source(linear(0, vy, 0, H, [(0, C["ground_lt"], 1), (0.3, C["ground"], 1), (1, "#05070d", 1)]))
    ctx.fill()
    # 白線（手前へ流れる）
    src(ctx, "#cdd3e0", 0.18)
    for k in range(12):
        u = ((k / 12 + depth * 0.1) % 1.0)
        z0, z1 = u ** 2.4, (u + 0.035) ** 2.4
        y0 = vy + 18 + (H + 400 - vy) * z0
        y1 = vy + 18 + (H + 400 - vy) * z1
        w0, w1 = 2 + 20 * z0, 2 + 20 * z1
        ctx.move_to(vx - w0, y0)
        ctx.line_to(vx + w0, y0)
        ctx.line_to(vx + w1, y1)
        ctx.line_to(vx - w1, y1)
        ctx.close_path()
        ctx.fill()
    light = None
    if lamps:
        for k in range(6):
            u = ((k / 6 + depth * 0.05) % 1.0)
            z = 0.05 + u ** 2 * 1.1
            for side in (-1, 1):
                px = vx + side * (130 + 900 * z)
                py = vy + 18 + (H + 400 - vy) * z * 0.62
                hh = 40 + 900 * z
                src(ctx, "#080a12")
                ctx.rectangle(px - 1 - 4 * z, py - hh, 2 + 8 * z, hh)
                ctx.fill()
                glow(ctx, px - side * 20 * z, py - hh, 30 + 160 * z, C["lamp"], 0.4)
                reflection(ctx, px - side * 20 * z, vy + 30 + (H - vy) * z * 0.9, 10 + 60 * z,
                           120 + 400 * z, C["lamp"], 0.12, wobble=8 * z, t=t)
        light = radial(vx, vy + 100, 900, [(0, "#ffe7b8", 0.5), (1, "#ffe7b8", 0.0)])
    return light
