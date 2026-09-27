"""パイロット版の音：BGM（ピアノ）と、雨・足音などの効果音。

曲はヘ長調、ゆっくり（1拍 約0.9秒）。素朴で、しんみりと明るく。
改札のカットでピアノが一音ずつ入りはじめ、アンドロイドが笑うあたりで旋律になり、
最後のタイトルで主和音に落ち着く。
雨の音はカットごとに大きさを変える（屋内ではこもらせる）。
"""

import numpy as np

from engine import audio
from engine.audio import SR, hz

BEAT = 60 / 66
BAR = BEAT * 4

CHORDS = [
    ["F2", "C3", "E3", "A3"],        # Fmaj7
    ["E2", "C3", "D3", "G3"],        # C/E
    ["D2", "A2", "C3", "F3"],        # Dm7
    ["Bb1", "F2", "A2", "D3"],       # B♭maj7
    ["A1", "F2", "C3", "A3"],        # F/A
    ["G1", "F2", "Bb2", "D3"],       # Gm7
    ["Bb1", "F2", "A2", "D3"],       # B♭maj7
    ["C2", "G2", "C3", "E3"],        # C
    ["F2", "C3", "E3", "A3"],        # Fmaj7
    ["F1", "Bb2", "D3", "F3"],       # B♭/F
    ["F1", "C3", "F3", "A3"],        # F
]

MELODY = {  # 小節: [(拍, 音, 長さ)]
    2: [(0, "A4", 1.5), (1.5, "G4", 0.5), (2, "F4", 1), (3, "E4", 1)],
    3: [(0, "D4", 2), (2, "F4", 1), (3, "A4", 1)],
    4: [(0, "C5", 1.5), (1.5, "Bb4", 0.5), (2, "A4", 2)],
    5: [(0, "G4", 1), (1, "A4", 1), (2, "Bb4", 1), (3, "D5", 1)],
    6: [(0, "C5", 3), (3, "A4", 1)],
    7: [(0, "G4", 2), (2, "E4", 1.5), (3.5, "F4", 0.5)],
    8: [(0, "F4", 1), (1, "A4", 1), (2, "C5", 1), (3, "E5", 1)],
    9: [(0, "D5", 2), (2, "C5", 2)],
    10: [(0, "A4", 4)],
}

# カットごとの雨の大きさ、こもり具合、傘にあたる雨音
RAIN_LEVEL = {"PL_c001": 1.0, "PL_c002": 0.30, "PL_c003": 0.60, "PL_c004": 0.55,
              "PL_c005": 0.45, "PL_c006": 0.55, "PL_c007": 0.45, "PL_c008": 0.65}
MUFFLED = {"PL_c002": 0.8}
PATTER = {"PL_c003": 0.8, "PL_c004": 0.5, "PL_c005": 1.0, "PL_c006": 0.4, "PL_c007": 1.0}


def envelope(timeline, table, n, default=0.0, smooth_s=0.12):
    """カットごとの値を、つなぎ目をなめらかにした時間の曲線にする。"""
    env = np.full(n, default, np.float32)
    for cid, start, dur in timeline:
        env[int(start * SR):int((start + dur) * SR)] = table.get(cid, default)
    k = int(smooth_s * SR)
    c = np.cumsum(np.concatenate([np.full(k // 2, env[0]), env, np.full(k - k // 2, env[-1])]), dtype=np.float64)
    avg = (c[k:] - c[:-k]) / k
    return avg[:n].astype(np.float32)[:, None]


def build(timeline, duration):
    n = int(duration * SR) + 1
    starts = {cid: start for cid, start, _ in timeline}
    out = audio.stereo(duration)

    # ---- 雨
    rain = audio.rain(duration + 0.1, seed=1)[:n]
    muffled = audio.band(rain, hi=600) * 1.6
    lvl = envelope(timeline, RAIN_LEVEL, n)
    muf = envelope(timeline, MUFFLED, n)
    out += (rain * lvl * (1 - muf) + muffled * muf) * 0.9
    pat = audio.patter(duration + 0.1, seed=2, rate=22)[:n]
    out += pat * envelope(timeline, PATTER, n) * 1.1

    # ---- 改札：構内の足音と、改札の電子音
    t0 = starts["PL_c002"]
    for k in range(6):
        ts = t0 + 0.25 + k / (0.82 * 2)
        if ts > t0 + 3.3:
            break
        audio.add(out, audio.step(seed=10 + k, wet=0.05), ts, gain=0.55, pan=-0.2 + 0.08 * k)
    beep = np.concatenate([
        np.sin(2 * np.pi * 2093 * np.arange(int(0.07 * SR)) / SR),
        np.zeros(int(0.03 * SR)),
        np.sin(2 * np.pi * 2637 * np.arange(int(0.09 * SR)) / SR),
    ]).astype(np.float32) * 0.06
    audio.add(out, audio.reverb(np.stack([beep, beep], 1), 1.2, 0.4), t0 + 0.9, pan=-0.4)

    # ---- 水たまりを踏む足音（後ろ姿のカット）
    for cid, rate_o, rate_a, gain in (("PL_c006", 0.82, 0.95, 0.35), ("PL_c007", 0.82, 0.95, 0.6)):
        cs = starts[cid]
        cd = next(d for c, _, d in timeline if c == cid)
        for rate, pan, seed0, g in ((rate_o, -0.25, 100, 1.0), (rate_a, 0.25, 200, 0.75)):
            k = 0
            while True:
                ts = cs + (k + 0.5) / (rate * 2)
                if ts > cs + cd:
                    break
                audio.add(out, audio.step(seed=seed0 + k, wet=1.0), ts, gain=gain * g, pan=pan)
                k += 1

    # ---- ピアノ
    music = audio.stereo(duration)
    m0 = starts["PL_c002"] + 0.4
    for bar, chord in enumerate(CHORDS):
        b0 = m0 + bar * BAR
        if b0 > duration:
            break
        last = bar == len(CHORDS) - 1
        if bar == 0:
            # はじめは低い音をひとつずつ
            audio.add(music, audio.piano(hz(chord[0]), 3.5, vel=0.45, seed=bar), b0, pan=-0.2)
            audio.add(music, audio.piano(hz("A4"), 3.0, vel=0.30, seed=bar + 50), b0 + 2 * BEAT, pan=0.2)
            continue
        if last:
            for i, note in enumerate(chord + ["C4", "F4"]):
                audio.add(music, audio.piano(hz(note), 6.0, vel=0.42, seed=bar * 10 + i), b0 + i * 0.05,
                          pan=-0.3 + 0.1 * i)
        else:
            # 分散和音（8分音符）
            pattern = [0, 1, 2, 3, 2, 1, 2, 3] if bar >= 2 else [0, 2, 3, 2]
            step_len = BAR / len(pattern)
            for i, idx in enumerate(pattern):
                vel = (0.38 if i == 0 else 0.24) * (0.8 if bar < 2 else 1.0)
                audio.add(music, audio.piano(hz(chord[idx]), step_len * 2.6, vel=vel, bright=0.35,
                                             seed=bar * 100 + i), b0 + i * step_len, pan=-0.35 + 0.1 * idx)
        for beat, note, length in MELODY.get(bar, []):
            audio.add(music, audio.piano(hz(note), length * BEAT + 1.6, vel=0.5, bright=0.6,
                                         seed=bar * 1000 + int(beat * 10)), b0 + beat * BEAT, pan=0.15)
    # 背景の和音（ストリングス風）
    for bar, chord in enumerate(CHORDS[1:], start=1):
        b0 = m0 + bar * BAR
        if b0 > duration:
            break
        freqs = [hz(n_) * 2 for n_ in chord[1:]]
        p = audio.pad(freqs, BAR + 2.5, attack=1.4, release=2.0, gain=0.05 if bar < 4 else 0.08, seed=bar)
        audio.add(music, p, b0 - 0.3)
    music = audio.reverb(music, seconds=3.2, mix=0.38)
    out += music * 1.25

    # ---- 頭と終わり
    audio.fade(out, 0, 1.4, fade_in=True)
    audio.fade(out, duration - 2.2, 2.2, fade_in=False)
    return out
