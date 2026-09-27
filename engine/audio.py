"""音の合成の部品。楽器の音、雨の音、残響、書き出し。

音はすべて numpy の配列で扱う。ステレオは (サンプル数, 2) の配列。
"""

import wave

import numpy as np

from .config import SAMPLE_RATE as SR

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name):
    """'A4' や 'F#3'、'Bb2' を周波数にする。"""
    n = NOTE[name[0]]
    rest = name[1:]
    while rest and rest[0] in "#b":
        n += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + n
    return 440.0 * 2 ** ((midi - 69) / 12)


def stereo(seconds):
    return np.zeros((int(seconds * SR) + 1, 2), np.float32)


def add(buf, sound, start, gain=1.0, pan=0.0):
    """モノラルかステレオの音を、start 秒の位置に重ねる。pan は -1（左）〜 1（右）。"""
    i = int(start * SR)
    if i >= len(buf):
        return
    if sound.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        sound = np.stack([sound * l, sound * r], axis=1) * np.sqrt(2)
    n = min(len(sound), len(buf) - i)
    buf[i:i + n] += sound[:n] * gain


def piano(freq, seconds, vel=0.6, bright=0.5, seed=0):
    """やわらかいピアノ風の音。倍音ごとに消え方を変えて、打鍵のあとの響きを作る。"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros(n, np.float32)
    for k in range(1, 9):
        f = freq * k * (1 + 0.00035 * k * k)          # 弦の硬さで倍音が少し高くなる
        if f > SR / 2.2:
            break
        amp = (1 / k ** (1.9 - bright)) * (1 + 0.1 * rng.standard_normal())
        decay = 0.9 + 0.55 * k * (freq / 440) ** 0.5
        detune = 1 + 0.0007 * rng.standard_normal()
        out += (amp * np.exp(-decay * t) * np.sin(2 * np.pi * f * detune * t + rng.uniform(0, 6.28))).astype(np.float32)
    attack = np.minimum(t / 0.006, 1.0)
    release = np.minimum((seconds - t) / 0.25, 1.0).clip(0, 1)
    hammer = rng.standard_normal(n).astype(np.float32) * np.exp(-t * 180) * 0.04 * vel
    return ((out * attack * release) * vel * 0.22 + hammer).astype(np.float32)


def pad(freqs, seconds, attack=1.8, release=2.5, gain=0.08, seed=0):
    """ゆっくり立ち上がる和音の背景（ストリングス風）。"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), np.float32)
    for f in freqs:
        for ch in (0, 1):
            for d in (-0.004, 0.0, 0.0045):
                ph = rng.uniform(0, 6.28)
                vib = 1 + 0.0015 * np.sin(2 * np.pi * (4.3 + rng.uniform(-0.4, 0.4)) * t)
                w = np.sin(2 * np.pi * f * (1 + d) * vib * t + ph)
                w += 0.18 * np.sin(2 * np.pi * 2 * f * (1 + d) * t + ph)
                out[:, ch] += w.astype(np.float32)
    env = np.minimum(t / attack, 1.0) * np.clip((seconds - t) / release, 0, 1)
    return out * env[:, None] * gain / max(len(freqs), 1)


def band(x, lo=None, hi=None):
    """周波数で音を削る（lo より低い音と hi より高い音をなだらかに消す）。"""
    spec = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(spec * g, n=x.shape[0], axis=0).astype(np.float32)


def rain(seconds, seed=0, density=1.0):
    """雨の音。低く流れるざあっという音と、近くのぱらぱらという粒の音を重ねる。"""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    wash = band(rng.standard_normal((n, 2)).astype(np.float32), lo=250, hi=5200) * 0.16
    body = band(rng.standard_normal((n, 2)).astype(np.float32), lo=60, hi=500) * 0.10
    drops = np.zeros((n, 2), np.float32)
    count = int(seconds * 260 * density)
    click = np.exp(-np.arange(int(0.012 * SR)) / (0.0018 * SR)).astype(np.float32)
    for _ in range(count):
        i = rng.integers(0, max(n - len(click), 1))
        ch = rng.integers(0, 2)
        tone = np.sin(2 * np.pi * rng.uniform(1800, 5200) * np.arange(len(click)) / SR).astype(np.float32)
        drops[i:i + len(click), ch] += click * tone * rng.uniform(0.02, 0.09)
    return wash + body + band(drops, lo=900)


def patter(seconds, seed=0, rate=18):
    """傘にあたる雨のぽつぽつという音。"""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    out = np.zeros((n, 2), np.float32)
    ln = int(0.05 * SR)
    t = np.arange(ln) / SR
    for _ in range(int(seconds * rate)):
        i = rng.integers(0, max(n - ln, 1))
        f = rng.uniform(420, 900)
        s = np.sin(2 * np.pi * f * t) * np.exp(-t * rng.uniform(55, 90)) * rng.uniform(0.04, 0.12)
        s += rng.standard_normal(ln) * np.exp(-t * 400) * 0.03
        p = rng.uniform(-0.5, 0.5)
        out[i:i + ln, 0] += (s * (1 - p) / 2).astype(np.float32)
        out[i:i + ln, 1] += (s * (1 + p) / 2).astype(np.float32)
    return band(out, lo=250, hi=6000)


def step(seed=0, wet=1.0):
    """濡れた地面を歩く足音（ぴちゃっ）。"""
    rng = np.random.default_rng(seed)
    ln = int(0.18 * SR)
    t = np.arange(ln) / SR
    thud = np.sin(2 * np.pi * 95 * t) * np.exp(-t * 45) * 0.25
    splash = band(rng.standard_normal(ln).astype(np.float32), lo=1200, hi=7000) * np.exp(-t * 28) * 0.18 * wet
    return (thud + splash).astype(np.float32)


def reverb(x, seconds=2.4, mix=0.3, seed=7, predelay=0.02):
    """広い場所の残響。減衰するノイズを畳み込む。"""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-t * 6.9 / seconds)[:, None]
    ir = band(ir, hi=6500)
    ir = np.concatenate([np.zeros((int(predelay * SR), 2), np.float32), ir])
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    size = x.shape[0] + ir.shape[0]
    nfft = 1 << (size - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft, axis=0) * np.fft.rfft(ir, nfft, axis=0), nfft, axis=0)[:x.shape[0]]
    return (x * (1 - mix) + wet.astype(np.float32) * mix * 1.4).astype(np.float32)


def fade(buf, start, seconds, fade_in=True):
    i0 = int(start * SR)
    n = int(seconds * SR)
    ramp = np.linspace(0, 1, n, dtype=np.float32)
    if not fade_in:
        ramp = ramp[::-1]
    seg = buf[i0:i0 + n]
    seg *= ramp[:len(seg), None]
    if not fade_in:
        buf[i0 + n:] = 0


def write_wav(path, buf, peak=0.89):
    """音割れしないようにやわらかく抑えてから、16bit の wav に書き出す。"""
    m = np.abs(buf).max() or 1.0
    x = buf / m * 1.15
    x = np.tanh(x) / np.tanh(1.15) * peak
    data = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
