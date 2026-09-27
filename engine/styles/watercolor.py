"""水彩。紙の質感、にじんで単純になる形、顔料がたまる縁。

暗いところも真っ黒にはせず、紙の色が透けるようにする。
紙の目は3フレームごとに少しずつ揺らいで、手で描いたような揺らぎを出す。
"""

import numpy as np
from PIL import Image, ImageFilter

PAPER = np.array([243, 238, 226], np.float32) / 255
FINISH = {"grain": 1.5, "vignette": 0.22}
SUBTITLE = {"color": (250, 247, 240), "shadow": 8, "shadow_alpha": 210}

_tex = {}


def _paper(h, w, k):
    key = (h, w, k)
    if key not in _tex:
        rng = np.random.default_rng(100 + k)
        tex = np.zeros((h, w), np.float32)
        for scale, amp in ((3, 0.35), (12, 0.35), (48, 0.3)):
            small = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
            img = Image.fromarray((small * 255).astype(np.uint8)).resize((w + scale, h + scale), Image.BICUBIC)
            tex += np.asarray(img, np.float32)[:h, :w] / 255 * amp
        tex = (tex - tex.min()) / (tex.max() - tex.min())
        _tex[key] = tex[..., None]
    return _tex[key]


def post(arr, frame):
    h, w = arr.shape[:2]
    rgb = arr[..., 2::-1].astype(np.float32) / 255
    img = Image.fromarray((rgb * 255).astype(np.uint8))
    # 形を単純にしてにじませる
    small = img.resize((w // 3, h // 3), Image.BOX).filter(ImageFilter.MedianFilter(3))
    soft = np.asarray(small.resize((w, h), Image.BILINEAR), np.float32) / 255
    base = soft * 0.7 + rgb * 0.3
    # 顔料がたまる縁（明るさが急に変わるところを少し濃く）
    lum = Image.fromarray((base.mean(axis=2) * 255).astype(np.uint8))
    blur = np.asarray(lum.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    edge = np.abs(base.mean(axis=2) - blur)[..., None]
    base = base * (1 - np.clip(edge * 2.2, 0, 0.35))
    # 紙に色がのったように：黒は紙の色が透けた濃い色に、明るいところは紙の白に
    out = PAPER * (0.16 + 0.84 * base ** 0.9)
    # 紙の目（濃いところほど顔料の粒が目立つ）
    tex = _paper(h, w, (frame // 3) % 3)
    dark = 1 - base.mean(axis=2, keepdims=True)
    out *= 1 - (0.06 + 0.12 * dark) * tex
    arr[..., 2::-1] = np.clip(out * 255, 0, 255).astype(np.uint8)
