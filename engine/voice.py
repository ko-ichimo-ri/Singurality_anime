"""声の合成。日本語は VOICEVOX、英語は Piper を使う。

どちらも無料で、PC の中だけで動く（ネットに文章を送らない）。
一度作った声は renders/voice_cache/ にとっておき、同じ文章・同じ設定なら使い回す。

voices.yaml の書き方（話す人ごと・言語ごと）:

    android:
      ja: {engine: voicevox, speaker: 14, speed: 0.95, credit: "VOICEVOX:冥鳴ひまり"}
      en: {engine: piper, model: en_US-kristin-medium, length_scale: 1.05, credit: "..."}

VOICEVOX の声には、利用規約でクレジットの表記が求められる。credit に書いたものは、
声付きの版の最後に画面へ表示する。
"""

import atexit
import hashlib
import json
import os
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from .audio import SR

PROGRAMS = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs"
VOICEVOX_EXE = PROGRAMS / "voicevox_engine-0.25.2" / "run.exe"
PIPER_EXE = PROGRAMS / "piper" / "piper.exe"
PIPER_VOICES = PROGRAMS / "piper" / "voices"
VOICEVOX_URL = "http://127.0.0.1:50021"

_proc = None


def _voicevox_alive():
    try:
        urllib.request.urlopen(VOICEVOX_URL + "/version", timeout=1)
        return True
    except OSError:
        return False


def _ensure_voicevox():
    """VOICEVOX のエンジンが動いていなければ起動し、終わったら止める。"""
    global _proc
    if _voicevox_alive():
        return
    if not VOICEVOX_EXE.exists():
        raise FileNotFoundError(f"VOICEVOX のエンジンが見つかりません: {VOICEVOX_EXE}")
    _proc = subprocess.Popen([str(VOICEVOX_EXE), "--host", "127.0.0.1", "--port", "50021"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    atexit.register(_proc.terminate)
    for _ in range(120):
        if _voicevox_alive():
            return
        time.sleep(0.5)
    raise RuntimeError("VOICEVOX のエンジンが起動しませんでした")


def _voicevox(text, cfg):
    _ensure_voicevox()
    speaker = int(cfg["speaker"])
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    req = urllib.request.Request(f"{VOICEVOX_URL}/audio_query?{q}", method="POST")
    query = json.load(urllib.request.urlopen(req))
    query["speedScale"] = cfg.get("speed", 1.0)
    query["pitchScale"] = cfg.get("pitch", 0.0)
    query["intonationScale"] = cfg.get("intonation", 1.0)
    query["prePhonemeLength"] = 0.05
    query["postPhonemeLength"] = 0.2
    req = urllib.request.Request(f"{VOICEVOX_URL}/synthesis?speaker={speaker}",
                                 data=json.dumps(query).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return urllib.request.urlopen(req).read()


def _piper(text, cfg):
    model = PIPER_VOICES / f"{cfg['model']}.onnx"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.wav"
        cmd = [str(PIPER_EXE), "--model", str(model), "--output_file", str(out),
               "--length_scale", str(cfg.get("length_scale", 1.0))]
        subprocess.run(cmd, input=text.encode("utf-8"), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out.read_bytes()


def _resample(wav_bytes):
    """どんな形式の wav でも、48kHz のモノラルにそろえる。"""
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", "-", "-ac", "1", "-ar", str(SR),
           "-f", "s16le", "-"]
    raw = subprocess.run(cmd, input=wav_bytes, stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(raw, "<i2").astype(np.float32) / 32768


def speak(lang, text, cfg, cache):
    """文章を声にして、48kHz・モノラルの配列で返す。"""
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(json.dumps([lang, text, cfg], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    path = cache / f"{key}.wav"
    if not path.exists():
        engine = cfg.get("engine")
        raw = _voicevox(text, cfg) if engine == "voicevox" else _piper(text, cfg)
        data = _resample(raw)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    # 音声合成ソフトごとに音量が違うので、話し声の大きさ（RMS）をそろえる
    voiced = data[np.abs(data) > 0.01]
    rms = float(np.sqrt((voiced ** 2).mean())) if len(voiced) else 1.0
    data = data * (0.12 / max(rms, 1e-4))
    return np.clip(data, -0.95, 0.95) * float(cfg.get("level", 1.0))


def credits(voices, lang):
    """声付きの版に表示するクレジット。"""
    out = []
    for who, langs in voices.items():
        c = (langs.get(lang) or {}).get("credit")
        if c and c not in out:
            out.append(c)
    return out
