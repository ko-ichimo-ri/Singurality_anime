"""おっさん（55歳）のデザイン。

少し猫背で、手はいつもコートのポケットの中。濃紺のオーバーコートに、くすんだ赤のマフラー、細い眼鏡。
描き方は side（横）/ back（後ろ）/ front（正面）の3つ。どれも足もとを (x, y)、身長を s ピクセルとして描く。
"""

import math

from engine.draw import TAU, capsule, ellipse, ik, limb_end, linear, place, rrect, src
from engine.rig import Anchor, limb, walk_back, walk_side

NAME = "おっさん"
NAME_EN = "Ossan"
HEIGHT = 1.0

C = {
    "skin": "#d7a687",
    "skin_dk": "#b3806a",
    "hair": "#97938d",
    "hair_dk": "#6f6b67",
    "coat": "#2e3442",
    "coat_dk": "#222630",
    "coat_lt": "#3a4152",
    "trousers": "#1f222a",
    "shoe": "#121215",
    "shirt": "#dcd8cf",
    "tie": "#3a2e37",
    "scarf": "#6a3c38",
    "scarf_dk": "#4f2c2a",
    "glasses": "#16161a",
    "eye": "#1b1819",
}


# ================================================================ 横

def _leg_side(ctx, leg, tint, far):
    hip, knee, ankle = leg
    limb(ctx, [hip, knee, ankle], [0.078, 0.064, 0.052], C["trousers"] if not far else "#17191f", tint)
    src(ctx, C["shoe"], 1, tint)
    rrect(ctx, ankle[0] - 0.028, ankle[1] - 0.024, 0.108, 0.036, 0.016)
    ctx.fill()


def _coat_side(ctx, hem_sway, tint):
    ctx.move_to(-0.056, -0.817)
    ctx.curve_to(-0.082, -0.80, -0.086, -0.70, -0.082, -0.60)
    ctx.curve_to(-0.079, -0.48, -0.090, -0.37, -0.094 + hem_sway, -0.295)
    ctx.line_to(0.090 + hem_sway, -0.287)
    ctx.curve_to(0.082, -0.40, 0.076, -0.55, 0.072, -0.66)
    ctx.curve_to(0.070, -0.745, 0.062, -0.795, 0.030, -0.817)
    ctx.curve_to(0.0, -0.832, -0.034, -0.832, -0.056, -0.817)
    ctx.close_path()
    src(ctx, C["coat"], 1, tint)
    ctx.fill_preserve()
    ctx.set_source(linear(-0.095, 0, 0.09, 0, [(0, C["coat_dk"], 0.85), (0.45, C["coat_dk"], 0.0), (1, C["coat_dk"], 0)], tint=tint))
    ctx.fill()
    # 前の合わせと、ポケット
    ctx.set_line_width(0.0045)
    src(ctx, C["coat_dk"], 1, tint)
    ctx.move_to(0.061, -0.74)
    ctx.curve_to(0.066, -0.55, 0.072, -0.40, 0.080 + hem_sway, -0.29)
    ctx.stroke()
    # 襟
    src(ctx, C["coat_lt"], 1, tint)
    ctx.move_to(0.028, -0.815)
    ctx.line_to(0.070, -0.71)
    ctx.line_to(0.050, -0.775)
    ctx.close_path()
    ctx.fill()
    # マフラー
    src(ctx, C["scarf"], 1, tint)
    rrect(ctx, -0.050, -0.842, 0.100, 0.040, 0.014)
    ctx.fill()
    src(ctx, C["scarf_dk"], 1, tint)
    capsule(ctx, 0.044, -0.812, 0.058, -0.690, 0.030, 0.026)
    ctx.fill()


def _head_side(ctx, tint, blink=0.0):
    # 頭とあご
    src(ctx, C["skin"], 1, tint)
    ellipse(ctx, 0.022, -0.905, 0.060, 0.068)
    ctx.fill()
    ellipse(ctx, 0.044, -0.866, 0.033, 0.022)
    ctx.fill()
    # 鼻
    ctx.move_to(0.076, -0.915)
    ctx.curve_to(0.090, -0.892, 0.092, -0.882, 0.074, -0.876)
    ctx.close_path()
    ctx.fill()
    # 耳
    src(ctx, C["skin_dk"], 1, tint)
    ellipse(ctx, -0.006, -0.900, 0.014, 0.021)
    ctx.fill()
    # 髪（前が少し薄い）
    src(ctx, C["hair"], 1, tint)
    ctx.move_to(0.046, -0.957)
    ctx.curve_to(0.030, -0.982, -0.020, -0.985, -0.040, -0.958)
    ctx.curve_to(-0.055, -0.935, -0.050, -0.885, -0.040, -0.862)
    ctx.line_to(-0.018, -0.866)
    ctx.curve_to(-0.022, -0.885, -0.020, -0.915, -0.010, -0.925)
    ctx.curve_to(0.004, -0.940, 0.028, -0.946, 0.046, -0.957)
    ctx.close_path()
    ctx.fill()
    src(ctx, C["hair_dk"], 0.8, tint)
    ctx.set_line_width(0.004)
    ctx.move_to(-0.030, -0.955)
    ctx.curve_to(-0.042, -0.935, -0.040, -0.90, -0.034, -0.875)
    ctx.stroke()
    # 眉・目・口
    ctx.set_line_width(0.0055)
    ctx.move_to(0.046, -0.931)
    ctx.line_to(0.068, -0.927)
    ctx.stroke()
    src(ctx, C["eye"], 1, tint)
    lid = 0.004 * (1 - blink)
    ellipse(ctx, 0.060, -0.911, 0.0055, max(lid, 0.0012))
    ctx.fill()
    src(ctx, C["skin_dk"], 1, tint)
    ctx.set_line_width(0.0035)
    ctx.move_to(0.062, -0.866)
    ctx.line_to(0.076, -0.868)
    ctx.stroke()
    ctx.move_to(0.058, -0.895)
    ctx.curve_to(0.062, -0.885, 0.066, -0.878, 0.070, -0.874)
    ctx.stroke()
    # 眼鏡
    src(ctx, C["glasses"], 1, tint)
    ctx.set_line_width(0.0038)
    rrect(ctx, 0.048, -0.922, 0.026, 0.021, 0.006)
    ctx.stroke()
    ctx.move_to(0.048, -0.915)
    ctx.line_to(-0.002, -0.910)
    ctx.stroke()


def side(ctx, x, y, s, walk=None, walk_amt=1.0, hunch=0.07, head=0.10, arm="pockets",
         target=None, tint=None, flip=False, blink=0.0):
    """横向き（+x を向く。flip=True で左向き）。

    walk: 歩きの位相（0〜1 を繰り返す）。None なら立ち止まる
    hunch: 背中の丸まり（ラジアン）、head: うつむき具合（ラジアン、正で下を向く）
    arm: "pockets"（ポケットに手）/ "down"（下ろす）/ "hold"（target の位置を手でつかむ）
    target: arm="hold" のときに手を置く位置（画面の座標）
    """
    ph = walk if walk is not None else 0.0
    amt = walk_amt if walk is not None else 0.0
    legs, dy = walk_side(ph, amt, -0.485, 0.24, 0.245)
    hip = (0.0, -0.485 + dy)
    pts = {}
    anchor = Anchor(ctx)
    with place(ctx, x, y, s, flip):
        _leg_side(ctx, legs[0], tint, far=True)
        _leg_side(ctx, legs[1], tint, far=False)
        ctx.save()
        ctx.translate(*hip)
        ctx.rotate(hunch)
        ctx.translate(-hip[0], 0.485)
        sway = 0.012 * math.sin(TAU * ph) * amt
        # 首はコートとマフラーの奥にあるので先に描く
        src(ctx, C["skin_dk"], 1, tint)
        capsule(ctx, 0.004, -0.80, 0.014 + head * 0.03, -0.86, 0.046)
        ctx.fill()
        _coat_side(ctx, sway, tint)
        shoulder = (-0.004, -0.772)
        if arm == "pockets":
            elbow, hand = (-0.030, -0.605), (0.036, -0.532)
            limb(ctx, [shoulder, elbow, hand], [0.066, 0.058, 0.050], C["coat_lt"], tint)
            src(ctx, C["coat_dk"], 1, tint)
            ctx.set_line_width(0.006)
            ctx.move_to(0.012, -0.548)
            ctx.line_to(0.070, -0.530)
            ctx.stroke()
        else:
            if arm == "hold" and target is not None:
                tx = ((target[0] - x) / s) * (-1 if flip else 1)
                ty = (target[1] - y) / s
                # 腰を中心に傾けた分を戻して、胴体の座標にする
                cx, cy = tx - hip[0], ty - hip[1]
                c, sn = math.cos(-hunch), math.sin(-hunch)
                lx, ly = cx * c - cy * sn + hip[0], cx * sn + cy * c - 0.485
                elbow, hand = ik(*shoulder, lx, ly, 0.19, 0.18, bend=1)
            else:
                sw = -0.28 * math.sin(TAU * ph) * amt
                elbow = limb_end(*shoulder, sw, 0.19)
                hand = limb_end(*elbow, sw + 0.18, 0.18)
            limb(ctx, [shoulder, elbow, hand], [0.066, 0.058, 0.050], C["coat_lt"], tint)
            src(ctx, C["skin"], 1, tint)
            ellipse(ctx, hand[0], hand[1], 0.026, 0.030)
            ctx.fill()
            pts["hand"] = anchor.point(ctx, *hand)
        neck = (0.012, -0.83)
        ctx.translate(*neck)
        ctx.rotate(head)
        ctx.translate(-neck[0], -neck[1])
        _head_side(ctx, tint, blink)
        pts["head_top"] = anchor.point(ctx, 0.02, -0.975)
        ctx.restore()
    return pts


# ================================================================ 後ろ

def back(ctx, x, y, s, walk=None, walk_amt=1.0, hold=None, lean=0.0, head_tilt=0.0, tint=None):
    """後ろ姿。hold に画面の座標を渡すと、右手（画面の右）でそこをつかむ。"""
    ph = walk if walk is not None else 0.0
    amt = walk_amt if walk is not None else 0.0
    legs, sway, bob = walk_back(ph, amt, -0.48, 0.046, 0.48)
    pts = {}
    anchor = Anchor(ctx)
    with place(ctx, x, y, s):
        ctx.rotate(lean)
        for hip, knee, ankle, lift in legs:
            limb(ctx, [hip, knee, ankle], [0.080, 0.068, 0.056], C["trousers"], tint)
            src(ctx, C["shoe"], 1, tint)
            ellipse(ctx, ankle[0], ankle[1] - 0.004, 0.036, 0.018 + lift * 0.1)
            ctx.fill()
        ctx.translate(sway, bob)
        # コート
        ctx.move_to(-0.100, -0.812)
        ctx.curve_to(-0.125, -0.805, -0.128, -0.770, -0.124, -0.72)
        ctx.curve_to(-0.118, -0.58, -0.120, -0.42, -0.122, -0.296)
        ctx.curve_to(-0.04, -0.288, 0.04, -0.288, 0.122, -0.296)
        ctx.curve_to(0.120, -0.42, 0.118, -0.58, 0.124, -0.72)
        ctx.curve_to(0.128, -0.770, 0.125, -0.805, 0.100, -0.812)
        ctx.curve_to(0.05, -0.828, -0.05, -0.828, -0.100, -0.812)
        ctx.close_path()
        src(ctx, C["coat"], 1, tint)
        ctx.fill_preserve()
        ctx.set_source(linear(-0.13, 0, 0.13, 0, [(0, C["coat_dk"], 0.7), (0.3, C["coat_dk"], 0.0),
                                                   (0.75, C["coat_dk"], 0.0), (1, C["coat_dk"], 0.55)], tint=tint))
        ctx.fill()
        src(ctx, C["coat_dk"], 1, tint)
        ctx.set_line_width(0.004)
        ctx.move_to(0, -0.80)
        ctx.line_to(0, -0.40)
        ctx.stroke()
        ctx.move_to(0.004, -0.40)
        ctx.line_to(0.004, -0.292)
        ctx.stroke()
        rrect(ctx, -0.075, -0.525, 0.150, 0.022, 0.006)
        ctx.fill()
        # 立てた襟とマフラー
        src(ctx, C["scarf"], 1, tint)
        rrect(ctx, -0.055, -0.852, 0.110, 0.030, 0.012)
        ctx.fill()
        src(ctx, C["coat_lt"], 1, tint)
        rrect(ctx, -0.078, -0.832, 0.156, 0.036, 0.014)
        ctx.fill()
        # 腕
        ls = (-0.110, -0.770)
        rs = (0.110, -0.770)
        lsw = 0.10 * math.sin(TAU * ph) * amt
        le, lh = (-0.132, -0.625 + lsw * 0.2), (-0.128, -0.505 + lsw * 0.25)
        limb(ctx, [ls, le, lh], [0.068, 0.060, 0.052], C["coat_lt"], tint)
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, lh[0], lh[1] + 0.012, 0.024, 0.028)
        ctx.fill()
        if hold is not None:
            tx, ty = (hold[0] - x) / s, (hold[1] - y) / s
            c, sn = math.cos(-lean), math.sin(-lean)
            tx, ty = tx * c - ty * sn - sway, tx * sn + ty * c - bob
            re, rh = ik(*rs, tx, ty, 0.19, 0.18, bend=-1)
        else:
            re, rh = (0.132, -0.625 - lsw * 0.2), (0.128, -0.505 - lsw * 0.25)
        limb(ctx, [rs, re, rh], [0.068, 0.060, 0.052], C["coat_lt"], tint)
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, rh[0], rh[1], 0.024, 0.028)
        ctx.fill()
        pts["hand_r"] = anchor.point(ctx, *rh)
        # 頭
        ctx.translate(0, -0.84)
        ctx.rotate(head_tilt)
        ctx.translate(0, 0.84)
        src(ctx, C["skin_dk"], 1, tint)
        ellipse(ctx, -0.061, -0.898, 0.013, 0.020)
        ctx.fill()
        ellipse(ctx, 0.061, -0.898, 0.013, 0.020)
        ctx.fill()
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, 0, -0.900, 0.060, 0.066)
        ctx.fill()
        src(ctx, C["hair"], 1, tint)
        ctx.move_to(-0.060, -0.905)
        ctx.curve_to(-0.062, -0.99, 0.062, -0.99, 0.060, -0.905)
        ctx.curve_to(0.058, -0.880, 0.050, -0.866, 0.036, -0.858)
        ctx.curve_to(0.012, -0.852, -0.012, -0.852, -0.036, -0.858)
        ctx.curve_to(-0.050, -0.866, -0.058, -0.880, -0.060, -0.905)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["hair_dk"], 0.7, tint)
        ctx.set_line_width(0.004)
        for dx in (-0.025, 0.0, 0.022):
            ctx.move_to(dx, -0.955)
            ctx.curve_to(dx * 1.1, -0.92, dx * 1.2, -0.89, dx * 1.25, -0.865)
            ctx.stroke()
        # 眼鏡のつる
        src(ctx, C["glasses"], 1, tint)
        ctx.set_line_width(0.004)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.058, -0.912)
            ctx.line_to(sgn * 0.066, -0.906)
            ctx.stroke()
        pts["head_top"] = anchor.point(ctx, 0, -0.975)
    return pts


# ================================================================ 正面

def front(ctx, x, y, s, tint=None, blink=0.0, look=0.0):
    """正面の立ち姿（設定画用）。"""
    with place(ctx, x, y, s):
        src(ctx, C["skin_dk"], 1, tint)
        capsule(ctx, 0, -0.82, 0, -0.86, 0.046)
        ctx.fill()
        for sgn in (-1, 1):
            limb(ctx, [(sgn * 0.046, -0.48), (sgn * 0.050, -0.24), (sgn * 0.050, -0.02)],
                 [0.080, 0.066, 0.056], C["trousers"], tint)
            src(ctx, C["shoe"], 1, tint)
            ellipse(ctx, sgn * 0.054, -0.012, 0.040, 0.020)
            ctx.fill()
        # コート（前を開けて、シャツとネクタイが見える）
        ctx.move_to(-0.100, -0.812)
        ctx.curve_to(-0.126, -0.80, -0.128, -0.76, -0.124, -0.70)
        ctx.curve_to(-0.118, -0.56, -0.120, -0.42, -0.124, -0.296)
        ctx.line_to(0.124, -0.296)
        ctx.curve_to(0.120, -0.42, 0.118, -0.56, 0.124, -0.70)
        ctx.curve_to(0.128, -0.76, 0.126, -0.80, 0.100, -0.812)
        ctx.close_path()
        src(ctx, C["coat"], 1, tint)
        ctx.fill()
        src(ctx, C["shirt"], 1, tint)
        ctx.move_to(-0.040, -0.82)
        ctx.line_to(0.040, -0.82)
        ctx.line_to(0.020, -0.56)
        ctx.line_to(-0.020, -0.56)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["tie"], 1, tint)
        ctx.move_to(-0.012, -0.80)
        ctx.line_to(0.012, -0.80)
        ctx.line_to(0.016, -0.60)
        ctx.line_to(0, -0.585)
        ctx.line_to(-0.016, -0.60)
        ctx.close_path()
        ctx.fill()
        src(ctx, C["coat_lt"], 1, tint)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.040, -0.82)
            ctx.line_to(sgn * 0.085, -0.80)
            ctx.line_to(sgn * 0.030, -0.60)
            ctx.close_path()
            ctx.fill()
        src(ctx, C["coat_dk"], 1, tint)
        ctx.set_line_width(0.004)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.030, -0.60)
            ctx.line_to(sgn * 0.034, -0.296)
            ctx.stroke()
        # マフラー（首にかけて前に垂らす）
        src(ctx, C["scarf"], 1, tint)
        rrect(ctx, -0.060, -0.852, 0.120, 0.034, 0.014)
        ctx.fill()
        src(ctx, C["scarf_dk"], 1, tint)
        for sgn in (-1, 1):
            capsule(ctx, sgn * 0.040, -0.83, sgn * 0.046, -0.66, 0.032, 0.030)
            ctx.fill()
        # 腕
        for sgn in (-1, 1):
            sh, el, ha = (sgn * 0.112, -0.772), (sgn * 0.134, -0.625), (sgn * 0.128, -0.505)
            limb(ctx, [sh, el, ha], [0.068, 0.060, 0.052], C["coat_lt"], tint)
            src(ctx, C["skin"], 1, tint)
            ellipse(ctx, ha[0], ha[1] + 0.012, 0.024, 0.028)
            ctx.fill()
        # 頭
        src(ctx, C["skin_dk"], 1, tint)
        for sgn in (-1, 1):
            ellipse(ctx, sgn * 0.062, -0.900, 0.013, 0.020)
            ctx.fill()
        src(ctx, C["skin"], 1, tint)
        ellipse(ctx, 0, -0.902, 0.059, 0.068)
        ctx.fill()
        src(ctx, C["hair"], 1, tint)
        ctx.move_to(-0.061, -0.890)
        ctx.curve_to(-0.066, -0.975, -0.030, -0.992, 0.0, -0.990)
        ctx.curve_to(0.030, -0.992, 0.066, -0.975, 0.061, -0.890)
        ctx.line_to(0.054, -0.905)
        ctx.curve_to(0.050, -0.935, 0.030, -0.952, 0.0, -0.950)
        ctx.curve_to(-0.030, -0.952, -0.050, -0.935, -0.054, -0.905)
        ctx.close_path()
        ctx.fill()
        # 眉・目・眼鏡・鼻・口
        src(ctx, C["hair_dk"], 1, tint)
        ctx.set_line_width(0.0055)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.012, -0.927)
            ctx.line_to(sgn * 0.038, -0.924)
            ctx.stroke()
        src(ctx, C["eye"], 1, tint)
        for sgn in (-1, 1):
            ellipse(ctx, sgn * 0.024 + look * 0.004, -0.908, 0.0055, max(0.0045 * (1 - blink), 0.0012))
            ctx.fill()
        src(ctx, C["skin_dk"], 1, tint)
        ctx.set_line_width(0.003)
        for sgn in (-1, 1):
            ctx.move_to(sgn * 0.015, -0.918)
            ctx.line_to(sgn * 0.033, -0.918)
            ctx.stroke()
            ctx.move_to(sgn * 0.022, -0.884)
            ctx.curve_to(sgn * 0.026, -0.876, sgn * 0.024, -0.868, sgn * 0.020, -0.862)
            ctx.stroke()
        ctx.move_to(0.0, -0.905)
        ctx.line_to(-0.004, -0.884)
        ctx.line_to(0.004, -0.882)
        ctx.stroke()
        ctx.set_line_width(0.0035)
        ctx.move_to(-0.012, -0.866)
        ctx.line_to(0.012, -0.866)
        ctx.stroke()
        src(ctx, C["glasses"], 1, tint)
        ctx.set_line_width(0.0038)
        for sgn in (-1, 1):
            rrect(ctx, sgn * 0.024 - 0.016, -0.919, 0.032, 0.022, 0.006)
            ctx.stroke()
        ctx.move_to(-0.008, -0.910)
        ctx.line_to(0.008, -0.910)
        ctx.stroke()
