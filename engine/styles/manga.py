"""漫画。白黒の網点（スクリーントーン）と描線。傘だけに色を残す。

同人誌で漫画にする予定だった、この作品の出発点への目くばせ。
"""

import numpy as np

INK = np.array([22, 20, 26], np.float32)
PAPER = np.array([246, 243, 236], np.float32)
OCHRE = np.array([214, 160, 63], np.float32)
FINISH = {"grain": 0, "vignette": 0}
SUBTITLE = {"color": (255, 255, 255), "shadow": 6, "shadow_alpha": 255}

_screen = {}


def _halftone(h, w, period=7.0):
    """45度に傾けた網点のしきい値（0〜1）。"""
    key = (h, w)
    if key not in _screen:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        u = (x + y) / np.sqrt(2) * (2 * np.pi / period)
        v = (x - y) / np.sqrt(2) * (2 * np.pi / period)
        _screen[key] = ((np.cos(u) + np.cos(v)) / 4 + 0.5)
    return _screen[key]


def post(arr, frame):
    h, w = arr.shape[:2]
    rgb = arr[..., 2::-1].astype(np.float32) / 255
    lum = rgb @ np.array([0.30, 0.59, 0.11], np.float32)
    # 夜の場面でも白と黒の両方が出るように、明るさを持ち上げる
    lo, hi = np.percentile(lum, 3), np.percentile(lum, 99.5)
    L = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1) ** 0.75
    # 網点：明るさに応じて点の大きさが変わる
    ink = (_halftone(h, w) > L).astype(np.float32)
    ink[L > 0.86] = 0
    ink[L < 0.10] = 1
    # 描線：明るさが急に変わるところ
    gx = np.zeros_like(L)
    gy = np.zeros_like(L)
    gx[:, 1:-1] = L[:, 2:] - L[:, :-2]
    gy[1:-1] = L[2:] - L[:-2]
    line = np.hypot(gx, gy) > 0.22
    ink[line] = 1
    out = PAPER * (1 - ink[..., None]) + INK * ink[..., None]
    # 傘（からし色）だけ色を残す
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    ochre = (r > g) & (g > b) & (sat > 0.42) & (mx > 0.30) & ((r - g) / np.maximum(mx - mn, 1e-3) < 0.75)
    shade = (0.55 + 0.6 * L)[..., None]
    out[ochre] = np.clip(OCHRE * shade, 0, 255)[ochre]
    arr[..., 2::-1] = np.clip(out, 0, 255).astype(np.uint8)
