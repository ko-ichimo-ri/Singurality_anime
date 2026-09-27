"""紙芝居版の音：パイロット版の BGM に、拍子木と、絵を引き抜く紙の音を足す。"""

import numpy as np

from engine import assets, audio
from engine.audio import SR

base = assets.load("pilot/sound/bgm.py")
PULL = 0.8


def clap(seed=0):
    """拍子木（木の棒を打ち合わせる音）。"""
    rng = np.random.default_rng(seed)
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    tone = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
               for f, a, d in ((1850, 0.5, 38), (3120, 0.3, 55), (4600, 0.15, 80), (920, 0.25, 30)))
    click = rng.standard_normal(n) * np.exp(-t * 900) * 0.6
    return (tone + click).astype(np.float32) * 0.5


def slide(seed=0):
    """紙がこすれて引き抜かれる音。"""
    rng = np.random.default_rng(seed)
    n = int(PULL * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / PULL, 0, 1)) ** 1.5 * (0.6 + 0.4 * t / PULL)
    noise = audio.band(rng.standard_normal(n).astype(np.float32), lo=1500, hi=9000)
    return noise * env.astype(np.float32) * 0.22


def build(timeline, duration):
    out = base.build(timeline, duration)
    for k, t0 in enumerate((0.15, 0.75, 1.15, 1.45)):
        audio.add(out, audio.reverb(np.stack([clap(k)] * 2, 1), 1.0, 0.25), t0, gain=0.9 - 0.1 * k)
    for i, (cid, start, dur) in enumerate(timeline):
        at = start + (3.3 if i == len(timeline) - 1 else dur - PULL)
        audio.add(out, slide(i), at, gain=1.0, pan=0.3)
    return out
