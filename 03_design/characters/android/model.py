"""女性型アンドロイドのデザイン。

おっさんより頭ひとつ小さい（身長はおっさんの 0.88 倍）。クリーム色のAラインのコートに、濃い紫がかった黒のボブヘア。
見た目は人間そっくりだが、首すじの細い光の線と、瞳の奥の小さな光だけが機械であることを示す。
描き方は side（横）/ back（後ろ）/ front（正面）。足もとを (x, y)、身長を s ピクセルとして描く。
"""

import math

from engine.draw import TAU, capsule, ellipse, glow, ik, limb_end, linear, place, rrect, src
from engine.rig import Anchor, limb, walk_back, walk_side

NAME = "アンドロイド"
NAME_EN = "Android"
HEIGHT = 0.88  # おっさんを 1 としたときの身長

C = {
    "skin": "#f2d9c7",
    "skin_dk": "#d9b7a3",
    "blush": "#eea79c",
    "hair": "#2d2433",
    "hair_lt": "#4a3b55",
    "coat": "#e8e0d1",
    "coat_dk": "#c9bfad",
    "coat_lt": "#f4eee4",
    "skirt": "#5f5470",
    "tights": "#3a3343",
    "shoe": "#5b3c2d",
    "eye": "#2a2130",
    "light": "#72e3d4",
}


# ================================================================ 横

def _leg_side(ctx, leg, tint, far, tiptoe):
    hip, knee, ankle = leg
    limb(ctx, [hip, knee, ankle], [0.056, 0.048, 0.040], "#2e2836" if far else C["tights"], tint)
    ctx.save()
    ctx.translate(*ankle)
    ctx.rotate(0.95 * tiptoe)
    src(ctx, C["shoe"], 1, tint)
    rrect(ctx, -0.022, -0.020, 0.092, 0.030, 0.014)
    ctx.fill()
    ctx.restore()


def _coat_side(ctx, sway, tint):
    src(ctx, C["skirt"], 1, tint)
    ctx.move_to(-0.080, -0.46)
    ctx.line_to(0.085, -0.46)
    ctx.line_to(0.100 + sway, -0.345)
    ctx.line_to(-0.100 + sway, -0.345)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(-0.048, -0.812)
    ctx.curve_to(-0.074, -0.80, -0.078, -0.72, -0.072, -0.64)
    ctx.curve_to(-0.068, -0.56, -0.100, -0.47, -0.118 + sway, -0.395)
    ctx.line_to(0.110 + sway, -0.388)
    ctx.curve_to(0.090, -0.47, 0.066, -0.55, 0.066, -0.64)
    ctx.curve_to(0.068, -0.73, 0.056, -0.795, 0.028, -0.812)
    ctx.curve_to(0.0, -0.824, -0.028, -0.824, -0.048, -0.812)
    ctx.close_path()
    src(ctx, C["coat"], 1, tint)
    ctx.fill_preserve()
    ctx.set_source(linear(-0.12, 0, 0.11, 0, [(0, C["coat_dk"], 0.9), (0.5, C["coat_dk"], 0.0), (1, C["coat_dk"], 0.15)]))
    ctx.fill()
    # 腰のベルト
    src(ctx, C["coat_dk"], 1, tint)
    rrect(ctx, -0.070, -0.600, 0.138, 0.016, 0.006)
    ctx.fill()
    # 丸い襟
    src(ctx, C["coat_lt"], 1, tint)
    ellipse(ctx, 0.020, -0.800, 0.040, 0.020)
    ctx.fill()


def _head_side(ctx, tint, blink, smile):
    src(ctx, C["skin"], 1, tint)
    ellipse(ctx, 0.018, -0.905, 0.064, 0.070)
    ctx.fill()
    ellipse(ctx, 0.038, -0.868, 0.030, 0.022)
    ctx.fill()
    # 小さな鼻
    ctx.move_to(0.076, -0.910)
    ctx.curve_to(0.088, -0.894, 0.086, -0.888, 0.074, -0.884)
    ctx.close_path()
    ctx.fill()
    # 頬
    src(ctx, C["blush"], 0.28 + 0.25 * smile, tint)
    ellipse(ctx, 0.050, -0.884, 0.016, 0.009)
    ctx.fill()
    # 目（まつげと、瞳の奥の小さな光）
    open_ = max(1 - blink, 0.08)
    src(ctx, C["eye"], 1, tint)
    ellipse(ctx, 0.060, -0.908, 0.0075, 0.0095 * open_)
    ctx.fill()
    ctx.set_line_width(0.0035)
    ctx.move_to(0.050, -0.917 + 0.006 * blink)
    ctx.curve_to(0.058, -0.921 + 0.006 * blink, 0.066, -0.919 + 0.006 * blink, 0.071, -0.913 + 0.004 * blink)
    ctx.stroke()
    if open_ > 0.4:
        src(ctx, C["light"], 0.9, tint)
        ellipse(ctx, 0.062, -0.905, 0.0022, 0.0022)
        ctx.fill()
    # 口
    src(ctx, "#b8746c", 1, tint)
    ctx.set_line_width(0.0032)
    ctx.move_to(0.060, -0.870 - 0.002 * smile)
    ctx.curve_to(0.066, -0.866 + 0.002 * smile, 0.070, -0.867, 0.074, -0.871 - 0.002 * smile)
    ctx.stroke()
    # ボブの髪（前髪をそろえ、あごの高さで切りそろえる）
    src(ctx, C["hair"], 1, tint)
    ctx.move_to(0.074, -0.935)
    ctx.curve_to(0.080, -0.975, 0.030, -0.998, -0.012, -0.992)
    ctx.curve_to(-0.060, -0.985, -0.078, -0.940, -0.074, -0.895)
    ctx.curve_to(-0.072, -0.865, -0.064, -0.850, -0.050, -0.846)
    ctx.line_to(0.004, -0.846)
    ctx.curve_to(0.010, -0.866, 0.008, -0.905, 0.018, -0.926)
    ctx.curve_to(0.034, -0.940, 0.060, -0.930, 0.074, -0.935)
    ctx.close_path()
    ctx.fill()
    src(ctx, C["hair_lt"], 0.7, tint)
    ctx.set_line_width(0.005)
    ctx.move_to(-0.030, -0.975)
    ctx.curve_to(-0.056, -0.950, -0.060, -0.900, -0.052, -0.865)
    ctx.stroke()


def _neck_light(ctx, x0, y0, x1, y1, tint, t=0.0):
    a = 0.55 + 0.25 * math.sin(t * 2.1)
    src(ctx, C["light"], a, tint)
    ctx.set_line_width(0.0035)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def side(ctx, x, y, s, walk=None, walk_amt=1.0, tiptoe=0.0, lean=0.0, head=0.0, arm="down",
         target=None, tint=None, flip=False, blink=0.0, smile=0.3, t=0.0):
    """横向き（+x を向く。flip=True で左向き）。

    tiptoe: つま先立ち（0〜1）、lean: 体の傾き、head: 顔の上下（正で下、負で上を見る）
    arm: "down"（下ろす）/ "hold"（target の位置を手でつかむ）
    """
    ph = walk if walk is not None else 0.0
    amt = walk_amt if walk is not None else 0.0
    legs, dy = walk_side(ph, amt, -0.48, 0.235, 0.24, swing=0.28)
    lift = 0.034 * tiptoe
    for leg in legs:
        for i, (px, py) in enumerate(leg):
            leg[i] = (px, py - lift)
    hip = (0.0, -0.48 + dy - lift)
    pts = {}
    anchor = Anchor(ctx)
    with place(ctx, x, y, s, flip):
        _leg_side(ctx, legs[0], tint, True, tiptoe)
        _leg_side(ctx, legs[1], tint, False, tiptoe)
        ctx.save()
        ctx.translate(*hip)
        ctx.rotate(lean)
        ctx.translate(-hip[0], 0.48)
        sway = 0.012 * math.sin(TAU * ph) * amt
        src(ctx, C["skin_dk"], 1, tint)
        capsule(ctx, 0.002, -0.80, 0.010, -0.862, 0.036)
        ctx.fill()
        _neck_light(ctx, -0.004, -0.842, 0.020, -0.838, tint, t)
        _coat_side(ctx, sway, tint)
        shoulder = (-0.004, -0.772)
        if arm == "hold" and target is not None:
            tx = ((target[0] - x) / s) * (-1 if flip else 1)
            ty = (target[1] - y) / s
            cx, cy = tx - hip[0], ty - hip[1]
            c, sn = math.cos(-lean), math.sin(-lean)
            lx, ly = cx * c - cy * sn + hip[0], cx * sn + cy * c - 0.48
            elbow, hand = ik(*shoulder, lx, ly, 0.175, 0.165, bend=1)
        else:
            sw = -0.25 * math.sin(TAU * ph) * amt
            elbow = limb_end(*shoulder, sw, 0.175)
            hand = limb_end(*elbow, sw + 0.12, 0.165)
        limb(ctx, [shoulder, elbow, hand], [0.052, 0.046, 0.040], C["coat_lt"], tint)
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, hand[0], hand[1], 0.021, 0.024)
        ctx.fill()
        pts["hand"] = anchor.point(ctx, *hand)
        neck = (0.008, -0.842)
        ctx.translate(*neck)
        ctx.rotate(head)
        ctx.translate(-neck[0], -neck[1])
        _head_side(ctx, tint, blink, smile)
        pts["head_top"] = anchor.point(ctx, 0.01, -0.99)
        ctx.restore()
    return pts


# ================================================================ 後ろ

def back(ctx, x, y, s, walk=None, walk_amt=1.0, lean=0.0, head_tilt=0.0, hold=None, tint=None, t=0.0):
    """後ろ姿。lean で体ごと傾ける（負で画面の左へ寄りかかる）。"""
    ph = walk if walk is not None else 0.0
    amt = walk_amt if walk is not None else 0.0
    legs, sway, bob = walk_back(ph, amt, -0.47, 0.036, 0.47)
    pts = {}
    anchor = Anchor(ctx)
    with place(ctx, x, y, s):
        ctx.rotate(lean)
        for hip, knee, ankle, lift in legs:
            limb(ctx, [hip, knee, ankle], [0.058, 0.050, 0.042], C["tights"], tint)
            src(ctx, C["shoe"], 1, tint)
            ellipse(ctx, ankle[0], ankle[1] - 0.004, 0.028, 0.016 + lift * 0.1)
            ctx.fill()
        ctx.translate(sway, bob)
        src(ctx, C["skirt"], 1, tint)
        ctx.move_to(-0.105, -0.44)
        ctx.line_to(0.105, -0.44)
        ctx.line_to(0.118, -0.345)
        ctx.line_to(-0.118, -0.345)
        ctx.close_path()
        ctx.fill()
        ctx.move_to(-0.080, -0.806)
        ctx.curve_to(-0.100, -0.80, -0.104, -0.77, -0.100, -0.72)
        ctx.curve_to(-0.094, -0.60, -0.120, -0.48, -0.134, -0.392)
        ctx.curve_to(-0.05, -0.384, 0.05, -0.384, 0.134, -0.392)
        ctx.curve_to(0.120, -0.48, 0.094, -0.60, 0.100, -0.72)
        ctx.curve_to(0.104, -0.77, 0.100, -0.80, 0.080, -0.806)
        ctx.curve_to(0.04, -0.818, -0.04, -0.818, -0.080, -0.806)
        ctx.close_path()
        src(ctx, C["coat"], 1, tint)
        ctx.fill_preserve()
        ctx.set_source(linear(-0.13, 0, 0.13, 0, [(0, C["coat_dk"], 0.8), (0.35, C["coat_dk"], 0.0),
                                                   (0.7, C["coat_dk"], 0.0), (1, C["coat_dk"], 0.6)]))
        ctx.fill()
        src(ctx, C["coat_dk"], 1, tint)
        rrect(ctx, -0.060, -0.605, 0.120, 0.016, 0.006)
        ctx.fill()
        ctx.set_line_width(0.0035)
        ctx.move_to(0, -0.59)
        ctx.line_to(0, -0.388)
        ctx.stroke()
        # 腕
        for sgn in (-1, 1):
            sh = (sgn * 0.090, -0.768)
            if sgn == 1 and hold is not None:
                tx, ty = (hold[0] - x) / s, (hold[1] - y) / s
                c, sn = math.cos(-lean), math.sin(-lean)
                tx, ty = tx * c - ty * sn - sway, tx * sn + ty * c - bob
                el, ha = ik(*sh, tx, ty, 0.175, 0.165, bend=-1)
            elif sgn == -1 and hold == "arm":
                el, ha = (-0.110, -0.640), (-0.080, -0.560)
            else:
                sw = 0.08 * math.sin(TAU * ph) * amt * sgn
                el, ha = (sgn * 0.108, -0.635 + sw * 0.2), (sgn * 0.104, -0.525 + sw * 0.25)
            limb(ctx, [sh, el, ha], [0.052, 0.046, 0.040], C["coat_lt"], tint)
            src(ctx, C["skin"], 1, tint)
            ellipse(ctx, ha[0], ha[1] + 0.008, 0.019, 0.022)
            ctx.fill()
            pts["hand_l" if sgn < 0 else "hand_r"] = anchor.point(ctx, *ha)
        # 頭
        ctx.translate(0, -0.84)
        ctx.rotate(head_tilt)
        ctx.translate(0, 0.84)
        src(ctx, C["skin_dk"], 1, tint)
        capsule(ctx, 0, -0.80, 0, -0.86, 0.036)
        ctx.fill()
        _neck_light(ctx, -0.014, -0.832, 0.014, -0.832, tint, t)
        src(ctx, C["hair"], 1, tint)
        ctx.move_to(-0.072, -0.900)
        ctx.curve_to(-0.078, -0.995, 0.078, -0.995, 0.072, -0.900)
        ctx.curve_to(0.070, -0.870, 0.066, -0.852, 0.058, -0.846)
        ctx.line_to(-0.058, -0.846)
        ctx.curve_to(-0.066, -0.852, -0.070, -0.870, -0.072, -0.900)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["hair_lt"], 0.6, tint)
        ctx.set_line_width(0.005)
        for dx in (-0.030, 0.026):
            ctx.move_to(dx * 0.6, -0.975)
            ctx.curve_to(dx * 1.1, -0.93, dx * 1.25, -0.89, dx * 1.3, -0.852)
            ctx.stroke()
        pts["head_top"] = anchor.point(ctx, 0, -0.99)
    return pts


# ================================================================ 正面

def front(ctx, x, y, s, hold=None, wave=0.0, blink=0.0, smile=0.35, look=0.0, head_tilt=0.0,
          tint=None, t=0.0):
    """正面。hold に画面の座標を渡すと、右手（画面の左）でそこをつかむ。wave で左手を小さく振る。"""
    pts = {}
    anchor = Anchor(ctx)
    with place(ctx, x, y, s):
        for sgn in (-1, 1):
            limb(ctx, [(sgn * 0.036, -0.47), (sgn * 0.038, -0.24), (sgn * 0.036, -0.02)],
                 [0.058, 0.048, 0.040], C["tights"], tint)
            src(ctx, C["shoe"], 1, tint)
            ellipse(ctx, sgn * 0.040, -0.012, 0.030, 0.016)
            ctx.fill()
        src(ctx, C["skirt"], 1, tint)
        ctx.move_to(-0.105, -0.44)
        ctx.line_to(0.105, -0.44)
        ctx.line_to(0.118, -0.345)
        ctx.line_to(-0.118, -0.345)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["skin_dk"], 1, tint)
        capsule(ctx, 0, -0.80, 0, -0.862, 0.036)
        ctx.fill()
        _neck_light(ctx, -0.016, -0.838, 0.016, -0.838, tint, t)
        ctx.move_to(-0.080, -0.806)
        ctx.curve_to(-0.100, -0.80, -0.104, -0.77, -0.100, -0.72)
        ctx.curve_to(-0.094, -0.60, -0.120, -0.48, -0.134, -0.392)
        ctx.curve_to(-0.05, -0.384, 0.05, -0.384, 0.134, -0.392)
        ctx.curve_to(0.120, -0.48, 0.094, -0.60, 0.100, -0.72)
        ctx.curve_to(0.104, -0.77, 0.100, -0.80, 0.080, -0.806)
        ctx.curve_to(0.04, -0.818, -0.04, -0.818, -0.080, -0.806)
        ctx.close_path()
        src(ctx, C["coat"], 1, tint)
        ctx.fill_preserve()
        ctx.set_source(linear(-0.13, 0, 0.13, 0, [(0, C["coat_dk"], 0.5), (0.3, C["coat_dk"], 0.0),
                                                   (0.8, C["coat_dk"], 0.0), (1, C["coat_dk"], 0.5)]))
        ctx.fill()
        src(ctx, C["coat_lt"], 1, tint)
        for sgn in (-1, 1):
            ellipse(ctx, sgn * 0.030, -0.800, 0.034, 0.018)
            ctx.fill()
        src(ctx, C["coat_dk"], 1, tint)
        rrect(ctx, -0.098, -0.605, 0.196, 0.016, 0.006)
        ctx.fill()
        ctx.set_line_width(0.0035)
        ctx.move_to(0, -0.79)
        ctx.line_to(0, -0.388)
        ctx.stroke()
        src(ctx, "#8a7560", 1, tint)
        for yy in (-0.74, -0.67, -0.54, -0.47):
            ellipse(ctx, 0.016, yy, 0.006, 0.006)
            ctx.fill()
        # 腕
        rs, ls = (-0.090, -0.768), (0.090, -0.768)
        if hold is not None:
            tx, ty = (hold[0] - x) / s, (hold[1] - y) / s
            re, rh = ik(*rs, tx, ty, 0.175, 0.165, bend=1)
        else:
            re, rh = (-0.108, -0.635), (-0.104, -0.525)
        limb(ctx, [rs, re, rh], [0.052, 0.046, 0.040], C["coat_lt"], tint)
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, rh[0], rh[1], 0.019, 0.022)
        ctx.fill()
        pts["hand_r"] = anchor.point(ctx, *rh)
        if wave > 0:
            w = wave
            le = (0.118 + 0.02 * w, -0.66 + 0.02 * w)
            lh = (0.100 + 0.05 * w + 0.012 * math.sin(t * 9) * w, -0.60 - 0.10 * w)
        else:
            le, lh = (0.108, -0.635), (0.104, -0.525)
        limb(ctx, [ls, le, lh], [0.052, 0.046, 0.040], C["coat_lt"], tint)
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, lh[0], lh[1], 0.019, 0.022)
        ctx.fill()
        # 頭
        ctx.translate(0, -0.845)
        ctx.rotate(head_tilt)
        ctx.translate(0, 0.845)
        src(ctx, C["hair"], 1, tint)
        ctx.move_to(-0.074, -0.900)
        ctx.curve_to(-0.080, -0.990, 0.080, -0.990, 0.074, -0.900)
        ctx.curve_to(0.074, -0.870, 0.070, -0.850, 0.064, -0.842)
        ctx.line_to(-0.064, -0.842)
        ctx.curve_to(-0.070, -0.850, -0.074, -0.870, -0.074, -0.900)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["skin"], 1, tint)
        ctx.move_to(-0.056, -0.925)
        ctx.curve_to(-0.058, -0.875, -0.030, -0.845, 0.0, -0.843)
        ctx.curve_to(0.030, -0.845, 0.058, -0.875, 0.056, -0.925)
        ctx.close_path()
        ctx.fill()
        # 前髪
        src(ctx, C["hair"], 1, tint)
        ctx.move_to(-0.066, -0.915)
        ctx.curve_to(-0.070, -0.975, 0.070, -0.975, 0.066, -0.915)
        ctx.curve_to(0.040, -0.922, 0.020, -0.918, 0.0, -0.925)
        ctx.curve_to(-0.020, -0.918, -0.040, -0.922, -0.066, -0.915)
        ctx.close_path()
        ctx.fill()
        # 頬
        src(ctx, C["blush"], 0.25 + 0.3 * smile, tint)
        for sgn in (-1, 1):
            ellipse(ctx, sgn * 0.034, -0.878, 0.014, 0.008)
            ctx.fill()
        # 目
        open_ = max(1 - blink, 0.08)
        for sgn in (-1, 1):
            ex, ey = sgn * 0.024 + look * 0.005, -0.900
            if smile > 0.75 and blink < 0.5:
                # にっこりしたときは目を細める
                src(ctx, C["eye"], 1, tint)
                ctx.set_line_width(0.004)
                ctx.move_to(ex - 0.010, ey + 0.002)
                ctx.curve_to(ex - 0.004, ey - 0.008, ex + 0.004, ey - 0.008, ex + 0.010, ey + 0.002)
                ctx.stroke()
                continue
            src(ctx, C["eye"], 1, tint)
            ellipse(ctx, ex, ey, 0.0095, 0.0125 * open_)
            ctx.fill()
            if open_ > 0.4:
                src(ctx, C["light"], 0.85, tint)
                ctx.set_line_width(0.0022)
                ctx.arc(ex, ey + 0.002, 0.0055, 0.3, math.pi - 0.3)
                ctx.stroke()
                src(ctx, "#ffffff", 0.9, tint)
                ellipse(ctx, ex - 0.003, ey - 0.004, 0.0028, 0.0028)
                ctx.fill()
            src(ctx, C["eye"], 1, tint)
            ctx.set_line_width(0.0035)
            ctx.move_to(ex - 0.012, ey - 0.010 * open_ - 0.001)
            ctx.curve_to(ex - 0.004, ey - 0.016 * open_, ex + 0.006, ey - 0.015 * open_, ex + 0.013, ey - 0.008 * open_)
            ctx.stroke()
        # 眉・鼻・口
        src(ctx, C["hair"], 0.8, tint)
        ctx.set_line_width(0.003)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.014, -0.924)
            ctx.line_to(sgn * 0.034, -0.926)
            ctx.stroke()
        src(ctx, C["skin_dk"], 1, tint)
        ctx.set_line_width(0.003)
        ctx.move_to(0.001, -0.884)
        ctx.line_to(-0.002, -0.876)
        ctx.stroke()
        src(ctx, "#b8746c", 1, tint)
        ctx.set_line_width(0.0034)
        w = 0.010 + 0.004 * smile
        ctx.move_to(-w, -0.862 - 0.003 * smile)
        ctx.curve_to(-w * 0.4, -0.857 + 0.002 * smile, w * 0.4, -0.857 + 0.002 * smile, w, -0.862 - 0.003 * smile)
        ctx.stroke()
        pts["head_top"] = anchor.point(ctx, 0, -0.99)
    return pts


SHEET_VIEWS = [
    ("正面 front", lambda c, x, y, s: front(c, x, y, s)),
    ("笑顔 smile", lambda c, x, y, s: front(c, x, y, s, smile=1.0, wave=1.0)),
    ("横 side", lambda c, x, y, s: side(c, x, y, s)),
    ("背伸び tiptoe", lambda c, x, y, s: side(c, x, y, s, tiptoe=1.0, head=-0.35, arm="hold",
                                              target=(x + 0.05 * s, y - 1.22 * s))),
    ("後ろ back", lambda c, x, y, s: back(c, x, y, s)),
]
