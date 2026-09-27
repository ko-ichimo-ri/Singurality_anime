"""Blender 版のパイロット：3Dの舞台と人形を作り、パイロット版と同じ8カットを書き出す。

Blender の中で実行する（コマンド例はリポジトリの一番上で）:

    blender -b --factory-startup -P experiments/blender/build.py -- --variant toon --out <フォルダ>
    blender -b --factory-startup -P experiments/blender/build.py -- --variant diorama --still PL_c004:3.5 --out <フォルダ>

--variant  toon（セル調＋輪郭線）/ diorama（木の人形とミニチュアの街、コマ撮り風）
--out      フレーム画像（jpg）を書き出すフォルダ
--still    カットID:秒 を指定すると、その1枚だけ書き出す（何度でも指定できる）
--frames   書き出すフレームの範囲（例：1-120）。省略すると全部
--scale    解像度の倍率（確認用に 0.5 など）

字幕・タイトル・音はここでは付けない。engine/overlay.py で日英それぞれに重ねる。
単位はメートル。Z が上。人形の正面は -Y 方向。
"""

import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

FPS = 24
CUTS = [("PL_c001", 5.0), ("PL_c002", 4.5), ("PL_c003", 5.0), ("PL_c004", 4.5),
        ("PL_c005", 4.5), ("PL_c006", 6.0), ("PL_c007", 7.5), ("PL_c008", 7.5)]
FONT = "C:/Windows/Fonts/NotoSansJP-VF.ttf"
TAU = math.tau

ARGS = {"variant": "toon", "out": None, "still": [], "frames": None, "scale": 1.0}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    i = 0
    while i < len(argv):
        k = argv[i].lstrip("-")
        v = argv[i + 1]
        if k == "still":
            ARGS["still"].append(v)
        elif k == "scale":
            ARGS["scale"] = float(v)
        else:
            ARGS[k] = v
        i += 2


# ================================================================ 時間

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= b)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def cut_at(frame):
    """フレーム番号（1から）→ (カットID, カットの中の秒数)。"""
    f = frame - 1
    for cid, dur in CUTS:
        n = int(round(dur * FPS))
        if f < n:
            return cid, f / FPS
        f -= n
    return CUTS[-1][0], CUTS[-1][1]


def cut_start_frame(cid):
    f = 1
    for c, dur in CUTS:
        if c == cid:
            return f
        f += int(round(dur * FPS))
    raise KeyError(cid)


TOTAL_FRAMES = sum(int(round(d * FPS)) for _, d in CUTS)


# ================================================================ 材質

def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return nt, out


def srgb(hexcol, mul=1.0):
    h = hexcol.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) * mul for x in c]
    return (*lin, 1.0)


_mats = {}


def mat(name, color, kind="paint", rough=0.6, emit=0.0, alpha=1.0):
    """variant によって作り方が変わる材質。kind: paint / wood / glass / ground / emit / rain"""
    key = (name, ARGS["variant"])
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    v = ARGS["variant"]
    if kind == "emit":
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = srgb(color)
        e.inputs["Strength"].default_value = emit
        nt.links.new(e.outputs[0], out.inputs["Surface"])
    elif kind == "rain":
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = srgb(color)
        e.inputs["Strength"].default_value = emit
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(e.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
    elif kind == "ground":
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = srgb(color)
        p.inputs["Roughness"].default_value = 0.12 if v == "toon" else 0.08
        p.inputs["Metallic"].default_value = 0.0
        # 水たまりのムラ
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 0.35
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.45
        ramp.color_ramp.elements[0].color = (0.03, 0.03, 0.03, 1)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = (0.35, 0.35, 0.35, 1)
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], p.inputs["Roughness"])
        nt.links.new(p.outputs[0], out.inputs["Surface"])
    elif v == "toon" and kind in ("paint", "wood"):
        # セル調：光の当たり方を3段階の色に置きかえる
        p = nt.nodes.new("ShaderNodeBsdfDiffuse")
        p.inputs["Color"].default_value = (1, 1, 1, 1)
        s2r = nt.nodes.new("ShaderNodeShaderToRGB")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        base = srgb(color)
        els = ramp.color_ramp.elements
        els[0].position = 0.0
        els[0].color = (base[0] * 0.28, base[1] * 0.30, base[2] * 0.42, 1)
        els[1].position = 0.06
        els[1].color = (base[0] * 0.62, base[1] * 0.64, base[2] * 0.75, 1)
        e3 = els.new(0.22)
        e3.color = base
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(p.outputs[0], s2r.inputs[0])
        nt.links.new(s2r.outputs["Color"], bw.inputs[0])
        nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    else:
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = srgb(color)
        p.inputs["Roughness"].default_value = rough
        if kind == "wood" or v == "diorama":
            # 木目・塗りのムラ
            tex = nt.nodes.new("ShaderNodeTexWave")
            tex.inputs["Scale"].default_value = 18.0 if kind == "wood" else 40.0
            tex.inputs["Distortion"].default_value = 6.0
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.25 if kind == "wood" else 0.08
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
        if kind == "glass":
            p.inputs["Emission Color"].default_value = srgb(color)
            p.inputs["Emission Strength"].default_value = emit
        nt.links.new(p.outputs[0], out.inputs["Surface"])
    _mats[key] = m
    return m


def windows_mat(name, wall, seed):
    """窓の明かりが並ぶビルの壁。レンガ模様を窓の格子として使う。"""
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 2.6
    brick.inputs["Mortar Size"].default_value = 0.6
    brick.inputs["Brick Width"].default_value = 1.2
    brick.inputs["Row Height"].default_value = 1.5
    brick.inputs["Color1"].default_value = (1, 1, 1, 1)
    brick.inputs["Color2"].default_value = (0.2, 0.2, 0.2, 1)
    brick.inputs["Mortar"].default_value = (0, 0, 0, 1)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    xy = nt.nodes.new("ShaderNodeMath")
    xy.operation = "ADD"
    nt.links.new(sep.outputs["X"], xy.inputs[0])
    nt.links.new(sep.outputs["Y"], xy.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(xy.outputs[0], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (seed * 3.7, seed * 1.3, 0)
    nt.links.new(comb.outputs[0], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs[0], brick.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    snap = nt.nodes.new("ShaderNodeVectorMath")
    snap.operation = "SNAP"
    snap.inputs[1].default_value = (0.46, 0.46, 0.58)
    nt.links.new(mapping.outputs[0], snap.inputs[0])
    nt.links.new(snap.outputs[0], noise.inputs["Vector"])
    lit = nt.nodes.new("ShaderNodeMath")
    lit.operation = "GREATER_THAN"
    lit.inputs[1].default_value = 0.8
    nt.links.new(noise.outputs["Value"], lit.inputs[0])
    win = nt.nodes.new("ShaderNodeMath")
    win.operation = "MULTIPLY"
    nt.links.new(brick.outputs["Fac"], win.inputs[0])
    nt.links.new(lit.outputs[0], win.inputs[1])
    warm = nt.nodes.new("ShaderNodeMix")
    warm.data_type = "RGBA"
    warm.inputs["A"].default_value = srgb("#9fc3ff")
    warm.inputs["B"].default_value = srgb("#ffcf7f")
    nt.links.new(noise.outputs["Color"], warm.inputs["Factor"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(warm.outputs["Result"], em.inputs["Color"])
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 0.9
    nt.links.new(win.outputs[0], strength.inputs[0])
    nt.links.new(strength.outputs[0], em.inputs["Strength"])
    body = nt.nodes.new("ShaderNodeBsdfDiffuse")
    body.inputs["Color"].default_value = srgb(wall)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(body.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m


# ================================================================ 形

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def obj_from_bm(name, bm, material=None, collection="set", smooth_shade=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth_shade:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if material:
        ob.data.materials.append(material)
    coll(collection).objects.link(ob)
    return ob


def box(name, size, loc, material=None, collection="set"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    ob = obj_from_bm(name, bm, material, collection)
    ob.location = loc
    return ob


def cylinder(name, r1, r2, depth, material=None, collection="set", segs=16, base_at_origin=True):
    """底面の中心が原点、+Z に伸びる円柱（先細り）。"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=depth)
    if base_at_origin:
        bmesh.ops.translate(bm, vec=Vector((0, 0, depth / 2)), verts=bm.verts)
    return obj_from_bm(name, bm, material, collection, smooth_shade=True)


def sphere(name, r, material=None, collection="set", scale=(1, 1, 1), segs=20):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return obj_from_bm(name, bm, material, collection, smooth_shade=True)


def ring(name, r, thick, material, collection="set"):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=thick, major_segments=24, minor_segments=6)
    ob = bpy.context.active_object
    ob.name = name
    for c in ob.users_collection:
        c.objects.unlink(ob)
    coll(collection).objects.link(ob)
    ob.data.materials.append(material)
    return ob


def empty(name, parent=None, loc=(0, 0, 0), collection="chars"):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.05
    coll(collection).objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_mode = "XYZ"
    return ob


def attach(ob, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def text_obj(name, body, size, loc, rot, material, collection="set"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    try:
        cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    except RuntimeError:
        pass
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    ob.data.materials.append(material)
    coll(collection).objects.link(ob)
    return ob


# ================================================================ 人形

class Person:
    """関節（エンプティ）をつないだ人形。pose() で姿勢を決める。"""

    def __init__(self, name, height, palette, kind):
        self.name = name
        self.h = height
        self.kind = kind
        s = height / 1.7
        self.s = s
        P = palette
        wood = ARGS["variant"] == "diorama"
        M = lambda n, c, **k: mat(f"{name}_{n}", c, kind="wood" if wood and n == "skin" else "paint", **k)
        self.root = empty(f"{name}_root")
        self.hips = empty(f"{name}_hips", self.root, (0, 0, 0.92 * s))
        self.spine = empty(f"{name}_spine", self.hips)
        # 胴とコート
        coat_len = (0.92 - (0.52 if kind == "ossan" else 0.60)) * s
        coat = cylinder(f"{name}_coat", 0.20 * s if kind == "ossan" else 0.22 * s, 0.16 * s, coat_len + 0.46 * s,
                        M("coat", P["coat"]), "chars")
        attach(coat, self.spine, (0, 0, -coat_len))
        coat.scale = (1.0, 0.72, 1.0)
        if kind == "android":
            skirt = cylinder(f"{name}_skirt", 0.2 * s, 0.16 * s, 0.12 * s, M("skirt", P["skirt"]), "chars")
            attach(skirt, self.spine, (0, 0, -coat_len - 0.08 * s))
            skirt.scale = (1, 0.75, 1)
        # 首と頭
        self.neck = empty(f"{name}_neck", self.spine, (0, 0, 0.47 * s))
        neck = cylinder(f"{name}_neckm", 0.05 * s, 0.045 * s, 0.1 * s, M("skin", P["skin"]), "chars")
        attach(neck, self.neck)
        self.head = empty(f"{name}_head", self.neck, (0, 0, 0.1 * s))
        hr = (0.105 if kind == "ossan" else 0.112) * s
        head = sphere(f"{name}_headm", hr, M("skin", P["skin"]), "chars", scale=(0.95, 0.95, 1.08))
        attach(head, self.head, (0, 0, hr * 0.95))
        if kind == "ossan":
            hair = sphere(f"{name}_hair", hr * 1.06, M("hair", P["hair"]), "chars", scale=(1.0, 1.0, 0.9))
            attach(hair, self.head, (0, 0.012 * s, hr * 1.08))
        else:
            hair = sphere(f"{name}_hair", hr * 1.07, M("hair", P["hair"]), "chars", scale=(1.02, 0.95, 0.8))
            attach(hair, self.head, (0, 0.02 * s, hr * 1.3))
        for sx in (-1, 1):
            eye = sphere(f"{name}_eye{sx}", 0.012 * s, M("eye", P["eye"]), "chars")
            attach(eye, self.head, (sx * 0.038 * s, -hr * 0.9, hr * 1.02))
        if kind == "ossan":
            gl = mat(f"{name}_glass", "#16161a")
            for sx in (-1, 1):
                r = ring(f"{name}_glasses{sx}", 0.026 * s, 0.004 * s, gl, "chars")
                attach(r, self.head, (sx * 0.038 * s, -hr * 0.97, hr * 1.02), (math.pi / 2, 0, 0))
            scarf = cylinder(f"{name}_scarf", 0.09 * s, 0.085 * s, 0.07 * s, M("scarf", P["scarf"]), "chars")
            attach(scarf, self.neck, (0, 0, -0.03 * s))
        else:
            light = mat(f"{name}_light", P["light"], kind="emit", emit=6.0)
            nl = ring(f"{name}_necklight", 0.052 * s, 0.004 * s, light, "chars")
            attach(nl, self.neck, (0, 0, 0.05 * s))
            # ボブの髪の横と後ろ
            bob = sphere(f"{name}_bob", hr * 1.08, M("hair", P["hair"]), "chars", scale=(1.02, 0.85, 0.95))
            attach(bob, self.head, (0, 0.04 * s, hr * 0.9))
            bangs = sphere(f"{name}_bangs", hr * 0.8, M("hair", P["hair"]), "chars", scale=(1.15, 0.45, 0.4))
            attach(bangs, self.head, (0, -hr * 0.62, hr * 1.55))
        # 腕
        self.arm = {}
        for side, sx in (("L", 1), ("R", -1)):
            sh = empty(f"{name}_sh{side}", self.spine, (sx * 0.19 * s, 0, 0.42 * s))
            up = cylinder(f"{name}_up{side}", 0.05 * s, 0.045 * s, 0.30 * s, M("sleeve", P["sleeve"]), "chars")
            attach(up, sh, (0, 0, -0.30 * s))
            el = empty(f"{name}_el{side}", sh, (0, 0, -0.30 * s))
            fo = cylinder(f"{name}_fo{side}", 0.045 * s, 0.04 * s, 0.27 * s, M("sleeve", P["sleeve"]), "chars")
            attach(fo, el, (0, 0, -0.27 * s))
            hand = empty(f"{name}_hand{side}", el, (0, 0, -0.30 * s))
            hm = sphere(f"{name}_handm{side}", 0.045 * s, M("skin", P["skin"]), "chars", scale=(0.8, 1.0, 1.2))
            attach(hm, hand)
            if kind == "android":
                wl = ring(f"{name}_wrist{side}", 0.042 * s, 0.003 * s, light, "chars")
                attach(wl, el, (0, 0, -0.25 * s))
            self.arm[side] = (sh, el, hand)
        # 脚
        self.leg = {}
        for side, sx in (("L", 1), ("R", -1)):
            hp = empty(f"{name}_hp{side}", self.hips, (sx * 0.085 * s, 0, 0))
            th = cylinder(f"{name}_th{side}", 0.07 * s, 0.06 * s, 0.45 * s, M("legs", P["legs"]), "chars")
            attach(th, hp, (0, 0, -0.45 * s))
            kn = empty(f"{name}_kn{side}", hp, (0, 0, -0.45 * s))
            sn = cylinder(f"{name}_sn{side}", 0.058 * s, 0.05 * s, 0.43 * s, M("legs", P["legs"]), "chars")
            attach(sn, kn, (0, 0, -0.43 * s))
            ft = box(f"{name}_ft{side}", (0.10 * s, 0.24 * s, 0.07 * s), (0, -0.06 * s, -0.46 * s),
                     M("shoe", P["shoe"]), "chars")
            ft.parent = kn
            self.leg[side] = (hp, kn)

    def place(self, x, y, yaw=0.0, z=0.0):
        """足もとを (x, y) に置き、yaw（ラジアン）だけ向きを変える。yaw=0 で -Y を向く。"""
        self.root.location = (x, y, z)
        self.root.rotation_euler = (0, 0, yaw)

    def pose(self, walk=None, amt=1.0, hunch=0.06, head=0.0, head_turn=0.0, lean=0.0, tiptoe=0.0,
             arms=None):
        """姿勢。arms は {"L": (前後, 横, 肘), "R": ...}（ラジアン）。なければ歩きに合わせて振る。"""
        s = self.s
        ph = walk or 0.0
        a = amt if walk is not None else 0.0
        bob = 0.02 * s * abs(math.cos(TAU * ph)) * a
        self.hips.location = (0, 0, 0.92 * s - bob + 0.05 * s * tiptoe)
        self.spine.rotation_euler = (hunch, lean, 0)
        self.neck.rotation_euler = (head, 0, head_turn)
        for side, sgn in (("L", 1), ("R", -1)):
            p = ph + (0.0 if side == "L" else 0.5)
            sw = 0.42 * math.sin(TAU * p) * a
            bend = a * (0.1 + 0.7 * max(0.0, math.sin(TAU * p + 1.9)))
            hp, kn = self.leg[side]
            hp.rotation_euler = (-sw, 0, 0)
            kn.rotation_euler = (bend, 0, 0)
            sh, el, _ = self.arm[side]
            if arms and side in arms:
                fwd, out, elbow = arms[side]
                sh.rotation_euler = (-fwd, sgn * out, 0)
                el.rotation_euler = (-elbow, 0, 0)
            else:
                sh.rotation_euler = (sw * 0.6, sgn * 0.08, 0)
                el.rotation_euler = (-0.25 - 0.15 * a, 0, 0)

    def hand_matrix(self, side):
        bpy.context.view_layer.update()
        return self.arm[side][2].matrix_world.copy()


# ================================================================ 傘

class Umbrella:
    def __init__(self, radius=0.62):
        wood = ARGS["variant"] == "diorama"
        canopy_m = mat("umb_canopy", "#d6a03f", kind="paint", rough=0.35)
        self.root = empty("umbrella", collection="chars")
        bm = bmesh.new()
        ribs = 8
        k = 6
        apex = bm.verts.new((0, 0, 0.78))
        ring_v = []
        for i in range(ribs * k):
            ang = TAU * i / (ribs * k)
            u = (i % k) / k
            dip = 0.05 * math.sin(math.pi * u)      # 骨と骨のあいだは少し上がる
            r = radius * (1 - 0.04 * math.sin(math.pi * u))
            ring_v.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), 0.52 + dip)))
        mid = []
        for i in range(ribs * k):
            ang = TAU * i / (ribs * k)
            mid.append(bm.verts.new((radius * 0.62 * math.cos(ang), radius * 0.62 * math.sin(ang), 0.72)))
        n = len(ring_v)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((apex, mid[i], mid[j]))
            bm.faces.new((mid[i], ring_v[i], ring_v[j], mid[j]))
        canopy = obj_from_bm("umb_canopym", bm, canopy_m, "chars", smooth_shade=True)
        canopy.modifiers.new("solid", "SOLIDIFY").thickness = 0.008
        canopy.parent = self.root
        shaft = cylinder("umb_shaft", 0.008, 0.008, 0.86, mat("umb_shaft", "#3b3b42"), "chars", segs=8)
        attach(shaft, self.root, (0, 0, -0.06))
        handle = ring("umb_handle", 0.04, 0.012, mat("umb_handle", "#6e4a31", kind="wood" if wood else "paint"),
                      "chars")
        attach(handle, self.root, (0.04, 0, -0.08), (math.pi / 2, 0, 0))

    def hold(self, matrix, offset=(0, 0, 0.0), tilt=(0, 0)):
        """手の位置に持ち手を合わせ、軸は上へ（tilt で傾ける）。"""
        pos = matrix.to_translation()
        self.root.location = pos + Vector(offset)
        self.root.rotation_euler = (tilt[0], tilt[1], 0)


# ================================================================ 雨

class Rain:
    """雨粒の板をたくさん並べた1つのメッシュ。毎フレーム、頂点を動かす。"""

    def __init__(self, count=3500, size=(24, 24, 12)):
        import random
        rnd = random.Random(7)
        self.count = count
        self.size = size
        self.seeds = [(rnd.random(), rnd.random(), rnd.random(), rnd.uniform(6.5, 9.0), rnd.uniform(0.18, 0.38))
                      for _ in range(count)]
        bm = bmesh.new()
        for _ in range(count):
            vs = [bm.verts.new((0, 0, 0)) for _ in range(8)]
            bm.faces.new(vs[0:4])
            bm.faces.new(vs[4:8])
        emit = 0.5 if ARGS["variant"] == "toon" else 0.4
        self.ob = obj_from_bm("rain", bm, mat("rain", "#c9d6ff", kind="rain", emit=emit, alpha=0.30), "fx")
        self.ob.visible_shadow = False

    def update(self, t, center):
        cx, cy, cz = center
        sx, sy, sz = self.size
        w = 0.004
        co = []
        for fx, fy, fz, v, ln in self.seeds:
            x = cx + (fx - 0.5) * sx
            y = cy + (fy - 0.5) * sy
            z = cz + sz / 2 - ((fz * sz + v * t) % sz)
            dx = 0.12 * ln   # 少し斜めに降る
            top, bot = (x - dx, y, z + ln), (x, y, z)
            co += [(bot[0] - w, y, bot[2]), (bot[0] + w, y, bot[2]), (top[0] + w, y, top[2]), (top[0] - w, y, top[2])]
            co += [(bot[0], y - w, bot[2]), (bot[0], y + w, bot[2]), (top[0], y + w, top[2]), (top[0], y - w, top[2])]
        flat = [c for p in co for c in p]
        self.ob.data.vertices.foreach_set("co", flat)
        self.ob.data.update()


# ================================================================ 舞台

PALETTE_OSSAN = {"coat": "#2e3442", "sleeve": "#3a4152", "skin": "#d7a687", "hair": "#97938d",
                 "legs": "#1f222a", "shoe": "#121215", "scarf": "#6a3c38", "eye": "#1b1819"}
PALETTE_ANDROID = {"coat": "#e8e0d1", "sleeve": "#f0e9dc", "skin": "#f2d9c7", "hair": "#2d2433",
                   "legs": "#3a3343", "shoe": "#5b3c2d", "skirt": "#5f5470", "eye": "#2a2130", "light": "#72e3d4"}


def build_world():
    v = ARGS["variant"]
    sc = bpy.context.scene
    world = bpy.data.worlds.new("night")
    sc.world = world
    nt, _ = None, None
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = srgb("#0b1024" if v == "toon" else "#161a30")
    bg.inputs["Strength"].default_value = 0.6 if v == "toon" else 0.9

    wall = "#1c2236"
    ground = box("ground", (400, 400, 0.1), (0, -60, -0.05), mat("ground", "#10141f", kind="ground"))
    # 駅舎
    box("station", (24, 8, 7), (0, 12, 3.5), mat("station_wall", wall))
    box("station_top", (24.2, 8.2, 0.4), (0, 12, 7.1), mat("station_top", "#12172a"))
    box("glass", (5, 0.1, 3), (0, 7.98, 1.5), mat("glass", "#f3ead6", kind="emit", emit=2.2))
    for x in (-2.5, -0.85, 0.85, 2.5):
        box(f"mullion{x}", (0.08, 0.14, 3), (x, 7.95, 1.5), mat("mullion", "#12172a"))
    box("canopy", (8, 2.8, 0.3), (0, 6.6, 3.3), mat("canopy", "#0d111e"))
    box("canopy_light", (7.6, 0.1, 0.05), (0, 5.3, 3.13), mat("canopy_light", "#fff4dc", kind="emit", emit=6.0))
    for x in (-7.5, -5.5, 5.5, 7.5, -9.5, 9.5):
        box(f"win2_{x}", (1.0, 0.1, 1.4), (x, 7.98, 4.8),
            mat(f"win2_{int(x) % 2}", "#9fc3ff" if int(x) % 2 else "#ffcf7f", kind="emit", emit=1.2))
    box("sign", (4.0, 0.2, 0.8), (0, 7.85, 5.2), mat("sign", "#eef4ff", kind="emit", emit=2.5))
    text_obj("sign_text", "北口   North Exit", 0.42, (0, 7.72, 5.2), (math.pi / 2, 0, 0), mat("sign_ink", "#19203a"))
    # 光源
    L = lambda n, kind, loc, power, color, **kw: _light(n, kind, loc, power, color, **kw)
    L("entrance", "AREA", (0, 7.6, 1.6), 900, "#fff1d6", size=(5, 3), rot=(math.pi / 2, 0, 0))
    L("canopy_down", "AREA", (0, 6.0, 3.1), 500, "#fff4dc", size=(7, 2))
    for x in (-9, 9):
        lamp(x, 4.0)
    L("moon", "SUN", (0, 0, 20), 0.25, "#8aa0ff", rot=(0.9, 0.2, 0.6))
    # 奥のビル群（駅の向こう）
    import random
    rnd = random.Random(3)
    x = -60.0
    while x < 60:
        w = rnd.uniform(6, 14)
        h = rnd.uniform(12, 45)
        box(f"far_{x:.0f}", (w, 8, h), (x, rnd.uniform(35, 60), h / 2), windows_mat(f"win_far_{x:.0f}", "#0f1428", rnd.random()))
        x += w + rnd.uniform(0.5, 3)
    build_street()
    build_interior()


def _light(name, kind, loc, power, color, size=None, rot=(0, 0, 0), spot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = power
    ld.color = srgb(color)[:3]
    if kind == "AREA" and size:
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = size
    if kind == "SPOT" and spot:
        ld.spot_size = spot
        ld.spot_blend = 0.6
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    coll("lights").objects.link(ob)
    return ob


def lamp(x, y, side=1):
    box(f"lamp_pole_{x}_{y}", (0.12, 0.12, 5.6), (x, y, 2.8), mat("pole", "#0b0e16"))
    box(f"lamp_head_{x}_{y}", (0.7, 0.3, 0.12), (x - side * 0.3, y, 5.6), mat("lamp_head", "#fff2d0", kind="emit", emit=12.0))
    _light(f"lamp_{x}_{y}", "SPOT", (x - side * 0.3, y, 5.45), 700, "#ffd48a", spot=1.6)


def build_street():
    """駅前から -Y 方向へまっすぐ延びる通り。両側に店とビル。"""
    import random
    rnd = random.Random(11)
    for sx in (-1, 1):
        y = -14.0
        while y > -170:
            ln = rnd.uniform(6, 13)
            h = rnd.uniform(7, 20)
            cx = sx * (5.5 + 4)
            box(f"st_{sx}_{y:.0f}", (8, ln - 0.4, h), (cx, y - ln / 2, h / 2),
                windows_mat(f"win_st_{sx}_{y:.0f}", ["#141a31", "#1a2139", "#171d33"][rnd.randrange(3)], rnd.random()))
            if rnd.random() < 0.75:
                col = rnd.choice(["#ffcf7f", "#9fc3ff", "#ffe2b0"])
                box(f"shop_{sx}_{y:.0f}", (0.1, ln - 1.4, 2.6), (sx * 5.45, y - ln / 2, 1.5),
                    mat(f"shop_{col}", col, kind="emit", emit=0.7))
            if rnd.random() < 0.4:
                col = rnd.choice(["#ff5a4f", "#72e3d4", "#c89cff", "#ffcf7f"])
                box(f"sign_{sx}_{y:.0f}", (0.8, 0.12, 1.8), (sx * 5.0, y - 1.0, 4.3),
                    mat(f"signc_{col}", col, kind="emit", emit=3.0))
            y -= ln
        for k in range(9):
            lamp(sx * 4.6, -18 - k * 18, side=sx)
    # 歩道の縁
    for sx in (-1, 1):
        box(f"curb{sx}", (0.15, 160, 0.12), (sx * 3.6, -94, 0.06), mat("curb", "#3a4258"))


def build_interior():
    """改札（別の場所に作る。カメラで映したときだけ見える）。"""
    ox = 100.0
    box("in_floor", (20, 10, 0.1), (ox, 3, -0.04), mat("in_floor", "#a7a49c"))
    box("in_wall", (20, 0.2, 5), (ox, 4.5, 2.5), mat("in_wall", "#e4e3dd"))
    box("in_ceiling", (20, 10, 0.2), (ox, 3, 4.2), mat("in_ceil", "#c9ccd6"))
    for i in range(7):
        box(f"in_light{i}", (1.6, 0.3, 0.05), (ox - 8 + i * 3, 1.5, 4.08), mat("in_lamp", "#fffbea", kind="emit", emit=8))
    _light("in_fill", "AREA", (ox, 0, 4.0), 2500, "#fff8ea", size=(18, 6))
    for i in range(6):
        x = ox - 5 + i * 1.8
        box(f"gate{i}", (0.3, 1.4, 1.05), (x, 2.2, 0.52), mat("gate", "#3a3f4d"))
        box(f"gate_top{i}", (0.26, 0.4, 0.04), (x, 1.8, 1.06), mat(f"gate_led{i % 5 == 0}",
                                                                   "#ff7a6a" if i % 5 == 0 else "#72e3d4",
                                                                   kind="emit", emit=4))
    # 出口の向こう（夜）
    box("in_exit_frame", (0.3, 10, 5), (ox + 4.2, 3, 2.5), mat("in_frame", "#2a2f3c"))
    box("in_exit_hole", (0.32, 3.0, 3.2), (ox + 4.2, 1.2, 1.6), mat("in_night", "#0a0f1e", kind="emit", emit=0.3))
    box("in_sign", (2.5, 0.1, 0.5), (ox - 5, 4.35, 3.1), mat("in_sign", "#27324f"))
    text_obj("in_sign_text", "出口  Exit →", 0.26, (ox - 5, 4.28, 3.1), (math.pi / 2, 0, 0),
             mat("in_sign_ink", "#f0ecdc", kind="emit", emit=1.5))


# ================================================================ カメラ

CAMS = {}
FILL = None


def camera(cid, lens=35.0):
    cd = bpy.data.cameras.new(cid)
    cd.lens = lens
    cd.clip_end = 400
    ob = bpy.data.objects.new(f"cam_{cid}", cd)
    coll("cams").objects.link(ob)
    CAMS[cid] = ob
    return ob


def look(cam, pos, target, roll=0.0):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if roll:
        cam.rotation_euler.rotate_axis("Z", roll)


def dof(cam, target_dist, fstop):
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = target_dist
    cam.data.dof.aperture_fstop = fstop


# ================================================================ カットごとの動き

def diorama():
    return ARGS["variant"] == "diorama"


def stepped(t):
    """コマ撮り風：人形の動きは1秒12コマにする。"""
    return math.floor(t * 12) / 12 if diorama() else t


def lift(pos, dz):
    return (pos[0], pos[1], pos[2] + dz)


def stage(cid, t, O, A, U, rain):
    """カット cid の t 秒目の、人形・傘・カメラ・雨を決める。"""
    tp = stepped(t)
    cam = CAMS[cid]
    D = 1.6 if diorama() else 0.0      # ジオラマ版はカメラを高くして見下ろす
    if cid == "PL_c001":
        O.place(0, -200)
        A.place(3.6, 2.2, yaw=math.pi)
        A.pose(hunch=0.0, arms={"R": (0.9, 0.1, 1.3), "L": (0.1, 0.05, 0.2)})
        U.hold(A.hand_matrix("R"), offset=(0, 0, 0.02))
        z = lerp(0, 1, smooth(t / 5))
        look(cam, lift((1.5, -12 + 2.2 * z, 2.0), D * 3), (0.8, 6, 2.8))
        cam.data.lens = 28
        rain.update(t, (1, -4, 6))
    elif cid == "PL_c002":
        go = 1 - smooth(seg(tp, 2.4, 3.3))
        x = 96.8 + 2.9 * ease_out(seg(tp, 0, 3.3))
        O.place(x, 0.6, yaw=math.pi / 2)
        O.pose(walk=min(tp, 3.3) * 0.82, amt=go, hunch=lerp(0.14, 0.06, seg(tp, 3.2, 4.1)),
               head=lerp(0.35, -0.05, smooth(seg(tp, 3.2, 4.1))),
               arms={"L": (0.04, -0.1, 0.3), "R": (0.04, -0.1, 0.3)})
        A.place(0, -300)
        U.root.location = (0, -300, 0)
        cx = lerp(97.6, 99.2, smooth(seg(t, 0, 3.4)))
        look(cam, lift((cx, -5.2, 1.3), D), (cx, 1, 1.1))
        cam.data.lens = 38
        rain.update(t, (160, 1, 5))   # 室内なので雨は映さない
    elif cid == "PL_c003":
        O.place(0, -300)
        A.place(3.6, 2.2, yaw=math.pi)
        wave = smooth(seg(tp, 2.6, 3.1)) * (1 - smooth(seg(tp, 4.3, 4.9)))
        w = math.sin(tp * 9) * 0.25 * wave
        A.pose(hunch=0.0, head=lerp(0.0, -0.08, seg(tp, 1.0, 1.6)), head_turn=lerp(0.5, 0.0, smooth(seg(tp, 1.0, 1.6))),
               arms={"R": (0.9, 0.1, 1.3), "L": (0.2 + 1.9 * wave, 0.35 * wave + w, 0.2 + 1.6 * wave)})
        U.hold(A.hand_matrix("R"), offset=(0, 0, 0.02))
        look(cam, lift((3.4, 5.6, 1.55), D * 0.6), (3.6, 2.2, 1.25 - D * 0.1))
        cam.data.lens = 50
        dof(cam, 3.4, 2.0 if not diorama() else 0.6)
        rain.update(t, (3.5, 2, 4))
    elif cid == "PL_c004":
        O.place(2.8, 5.7, yaw=0.0)
        look_up = smooth(seg(tp, 1.8, 2.8))
        O.pose(hunch=lerp(0.1, 0.02, look_up), head=lerp(0.2, -0.45, look_up),
               arms={"L": (0.12, -0.12, 0.55), "R": (0.12, -0.12, 0.55)})
        ay = lerp(3.4, 4.75, ease_out(seg(tp, 0, 1.3)))
        go = 1 - smooth(seg(tp, 0.9, 1.35))
        raise_ = smooth(seg(tp, 1.3, 2.7))
        tip = smooth(seg(tp, 1.4, 2.4))
        A.place(2.8, ay, yaw=math.pi)
        wob = math.sin(tp * 7) * 0.12 * smooth(seg(tp, 2.6, 3.0))
        A.pose(walk=tp * 1.1, amt=go, tiptoe=tip, head=lerp(0, -0.5, raise_), hunch=0.0,
               arms={"R": (lerp(0.9, 2.9, raise_), 0.1 + wob, lerp(1.3, 0.2, raise_)), "L": (0.1, 0.05, 0.2)})
        U.hold(A.hand_matrix("R"), offset=(0, 0, 0.02), tilt=(lerp(0, -0.25, raise_), 0))
        look(cam, lift((8.6, 5.0, 1.35), D), (2.8, 5.1, 1.35))
        cam.data.lens = 40
        rain.update(t, (3.5, 4, 4))
    elif cid == "PL_c005":
        O.place(2.8, 5.55, yaw=0.0)
        A.place(2.8, 4.9, yaw=math.pi)
        reach = ease_out(seg(tp, 0.5, 1.7))
        release = smooth(seg(tp, 2.3, 3.4))
        up = 0.06 * smooth(seg(tp, 3.2, 4.5))
        O.pose(hunch=0.02, head=-0.4, arms={"R": (lerp(0.3, 2.5, reach), 0.1, lerp(1.0, 0.35, reach)),
                                             "L": (0.12, -0.12, 0.55)})
        A.pose(tiptoe=1 - release * 0.8, head=-0.45, hunch=0.0,
               arms={"R": (lerp(2.8, 0.4, release), 0.1, lerp(0.25, 0.6, release)), "L": (0.1, 0.05, 0.2)})
        holder = "A" if tp < 1.8 else "O"
        m = A.hand_matrix("R") if holder == "A" else O.hand_matrix("R")
        U.hold(m, offset=(0, 0, 0.02 + (up if holder == "O" else 0)), tilt=(-0.1, 0))
        bpy.context.view_layer.update()
        ha = A.arm["R"][2].matrix_world.to_translation()
        ho = O.arm["R"][2].matrix_world.to_translation()
        mid = (ha + ho) / 2 if tp < 2.3 else ho
        tgt = (mid.x, mid.y, mid.z + 0.05)
        look(cam, lift((mid.x + 0.95, mid.y - 0.55, mid.z - 0.15), D * 0.3), tgt)
        cam.data.lens = 50
        dof(cam, 1.1, 1.4 if not diorama() else 0.5)
        rain.update(t, (3, 5, 3))
    elif cid in ("PL_c006", "PL_c007"):
        if cid == "PL_c006":
            d = 3.0 + 0.62 * t
            base_y = -10.0 - d
            cam_pos = lift((0.0, -10.0, 1.6), D * 0.4)
            cam_tgt = (0.0, -30, 1.1 - D * 0.5)
            lens = 35
            walk_o, walk_a = tp * 0.82, tp * 0.95 + 0.3
        else:
            travel = 1.05 * t
            base_y = -22 - travel
            cam_pos = lift((0.0, base_y + 1.9 + D * 0.9, 1.5), D * 0.25)
            cam_tgt = (0.0, base_y - 20, 1.2 - D * 0.1)
            lens = 45
            walk_o, walk_a = tp * 0.82, tp * 0.95 + 0.3
        lean = smooth(seg(tp, 3.4, 4.6)) if cid == "PL_c007" else 0.0
        # 後ろ姿：二人は -Y へ歩き、カメラは +Y 側から追う
        # カメラは -Y を向いているので、画面の左が +X。おっさんを左、アンドロイドを右にする
        O.place(0.27, base_y, yaw=0.0)
        A.place(lerp(-0.33, -0.27, lean), base_y, yaw=0.0)
        O.pose(walk=walk_o, amt=0.85, hunch=0.05, arms={"R": (0.9, -0.45, 1.5), "L": (0.1, 0.05, 0.3)})
        A.pose(walk=walk_a, amt=0.85, hunch=0.0, lean=-0.12 * lean, head_turn=0.0, head=0.0)
        A.head.rotation_euler = (0, -0.18 * lean, 0)
        U.hold(O.hand_matrix("R"), offset=(0, 0, 0.02), tilt=(0, -0.12))   # アンドロイドの側へ傾ける
        look(cam, cam_pos, cam_tgt)
        cam.data.lens = lens
        rain.update(t, (0, base_y, 4))
    elif cid == "PL_c008":
        by = -30 - 0.6 * t
        O.place(0.27, by)
        A.place(-0.3, by)
        O.pose(walk=tp * 0.82, amt=0.8, hunch=0.05, arms={"R": (0.9, -0.45, 1.5), "L": (0.1, 0.05, 0.3)})
        A.pose(walk=tp * 0.95, amt=0.8)
        U.hold(O.hand_matrix("R"), offset=(0, 0, 0.02), tilt=(0, -0.12))
        tilt = smooth(seg(t, 1.2, 5.6))
        pos = (0.5, -10, 11)
        tgt = (lerp(0, 0, tilt), lerp(-31, -90, tilt), lerp(0, 34, tilt))
        look(cam, pos, tgt)
        cam.data.lens = 30
        rain.update(t, (6, -26, 8))


def miniature_focus(cid, O, A, U):
    """ジオラマ版：人形にピントを合わせ、手前と奥を大きくぼかしてミニチュアに見せる。"""
    if not diorama():
        return
    cam = CAMS[cid]
    focus = {"PL_c002": O.hips, "PL_c005": U.root}.get(cid, A.hips if cid in ("PL_c001", "PL_c003", "PL_c004") else O.hips)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus
    cam.data.dof.aperture_fstop = {"PL_c005": 0.5, "PL_c003": 0.6}.get(cid, 0.28)


# ================================================================ 書き出し

def setup_render():
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x = int(1920 * ARGS["scale"])
    sc.render.resolution_y = int(1080 * ARGS["scale"])
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 94
    ee = sc.eevee
    for attr, val in (("taa_render_samples", 24 if ARGS["variant"] == "toon" else 32),
                      ("use_raytracing", True), ("use_shadows", True),
                      ("use_bloom", True), ("use_gtao", True)):
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    sc.view_settings.view_transform = "Standard" if ARGS["variant"] == "toon" else "AgX"
    sc.view_settings.look = "None"
    if ARGS["variant"] == "diorama":
        sc.view_settings.exposure = 0.8
        sc.view_settings.look = "AgX - Punchy"
    if ARGS["variant"] == "toon":
        sc.render.use_freestyle = True
        sc.render.line_thickness_mode = "ABSOLUTE"
        sc.render.line_thickness = 1.4 * ARGS["scale"]
        fs = bpy.context.view_layer.freestyle_settings
        ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("lines")
        ls.select_by_collection = True
        ls.collection = coll("fx")
        ls.collection_negation = "EXCLUSIVE"
        if ls.linestyle is None:
            ls.linestyle = bpy.data.linestyles.new("ink")
        ls.linestyle.color = (0.04, 0.04, 0.07)
    else:
        # ジオラマ：コンポジットでビネット代わりに少しだけ周辺を落とす程度（DOF が主役）
        pass


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = TOTAL_FRAMES
    build_world()
    O = Person("ossan", 1.70, PALETTE_OSSAN, "ossan")
    A = Person("android", 1.50, PALETTE_ANDROID, "android")
    U = Umbrella()
    rain = Rain()
    for cid, _ in CUTS:
        camera(cid)
    if diorama():
        # 模型を撮るときのような、カメラについて動くやわらかい補助光
        global FILL
        FILL = _light("fill", "AREA", (0, 0, 0), 90, "#ffe6c4", size=(1.5, 1.5))
    setup_render()
    return O, A, U, rain


def render_frame(frame, path, O, A, U, rain):
    sc = bpy.context.scene
    cid, t = cut_at(frame)
    sc.frame_set(frame)
    stage(cid, t, O, A, U, rain)
    miniature_focus(cid, O, A, U)
    sc.camera = CAMS[cid]
    if FILL is not None:
        bpy.context.view_layer.update()
        FILL.matrix_world = CAMS[cid].matrix_world @ Matrix.Translation((0.3, 0.4, 0.0))
    bpy.context.view_layer.update()
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    parse_args()
    out = Path(ARGS["out"])
    if not out.is_absolute():
        # Blender は相対パスを別の場所から解釈するので、リポジトリの一番上を基準にする
        out = Path(__file__).resolve().parents[2] / out
    out.mkdir(parents=True, exist_ok=True)
    O, A, U, rain = build()
    if ARGS["still"]:
        for spec in ARGS["still"]:
            cid, t = spec.split(":")
            frame = cut_start_frame(cid) + int(float(t) * FPS)
            render_frame(frame, out / f"{cid}_{float(t):05.2f}.jpg", O, A, U, rain)
        return
    a, b = 1, TOTAL_FRAMES
    if ARGS["frames"]:
        a, b = map(int, ARGS["frames"].split("-"))
    for f in range(a, b + 1):
        path = out / f"frame_{f:05d}.jpg"
        if path.exists():
            continue   # 途中から再開できるように、書き出し済みのフレームは飛ばす
        render_frame(f, path, O, A, U, rain)
        if f % 24 == 0:
            print(f"frame {f}/{TOTAL_FRAMES}", flush=True)


main()
