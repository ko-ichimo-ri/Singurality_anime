"""キャラクターの骨組み：歩くときの脚の動き、腕の描き方、座標の変換。

キャラクターは「足もとが (0, 0)、頭のてっぺんがおよそ (0, -1)」の座標で描く。
横向きは +x が顔の向き。後ろ向きは、キャラクターの右手が画面の右。
"""

import math

from .draw import TAU, capsule, limb_end, src


def walk_side(phase, amt, hip_y, thigh, shin, swing=0.32):
    """横から見た歩き。奥の脚・手前の脚の (腰, 膝, 足首) を返し、足が地面に着くように上下させる。"""
    legs = []
    for ph in (phase + 0.5, phase):
        s = math.sin(TAU * ph)
        a = swing * s * amt
        bend = amt * (0.06 + 0.55 * max(0.0, math.sin(TAU * ph + 1.9)))
        hip = (0.0, hip_y)
        knee = limb_end(*hip, a, thigh)
        ankle = limb_end(*knee, a - bend, shin)
        legs.append([hip, knee, ankle])
    lowest = max(l[2][1] for l in legs)
    dy = -lowest
    for leg in legs:
        for i, (x, y) in enumerate(leg):
            leg[i] = (x, y + dy)
    return legs, dy


def walk_back(phase, amt, hip_y, spread, length):
    """後ろから見た歩き。左右の脚の (腰, 膝, 足首) と、体の左右の揺れを返す。"""
    legs = []
    for k, ph in enumerate((phase, phase + 0.5)):
        x = spread * (-1 if k == 0 else 1)
        lift = max(0.0, math.sin(TAU * ph)) * 0.055 * amt
        hip = (x, hip_y)
        ankle = (x * 1.05, -lift)
        knee = (x * 1.08 + 0.004 * (-1 if k == 0 else 1), (hip_y - lift) / 2 - lift * 0.4)
        legs.append([hip, knee, ankle, lift])
    sway = 0.006 * math.sin(TAU * phase) * amt
    bob = -0.008 * abs(math.cos(TAU * phase)) * amt
    return legs, sway, bob


def limb(ctx, pts, widths, color, tint=None, a=1.0):
    """関節の点を順につないだ腕や脚を描く。widths は各点での太さ。"""
    src(ctx, color, a, tint)
    for (p0, p1), (w0, w1) in zip(zip(pts, pts[1:]), zip(widths, widths[1:])):
        capsule(ctx, *p0, *p1, w0, w1)
        ctx.fill()


def to_world(x, y, s, flip, lx, ly):
    """キャラクターの座標 (lx, ly) を、置いた場所での座標にする。"""
    return x + s * (-lx if flip else lx), y + s * ly


def to_local(x, y, s, flip, wx, wy):
    lx = (wx - x) / s
    return (-lx if flip else lx), (wy - y) / s


class Anchor:
    """キャラクターの中で計算した点（手の位置など）を、呼び出し側の座標に戻すための記録。

    描きはじめに Anchor(ctx) を作り、点を知りたいところで anchor.point(ctx, x, y) を呼ぶ。
    """

    def __init__(self, ctx):
        import cairo
        m = ctx.get_matrix()
        self.inv = cairo.Matrix(*m)
        self.inv.invert()

    def point(self, ctx, x, y):
        dx, dy = ctx.user_to_device(x, y)
        return self.inv.transform_point(dx, dy)
