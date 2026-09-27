"""カットを順に描いて、1本の映像に書き出す。

使い方（リポジトリの一番上で実行）:

    .venv/Scripts/python -m engine.render pilot                 日本語版と英語版を書き出す
    .venv/Scripts/python -m engine.render pilot --lang ja       日本語版だけ
    .venv/Scripts/python -m engine.render pilot --contact       各カットの静止画を一覧にした確認用の画像
    .venv/Scripts/python -m engine.render pilot --still PL_c004:2.5   1枚だけ静止画
    .venv/Scripts/python -m engine.render pilot --scale 0.5     半分の大きさで速く確認

<作品フォルダ> には cuts/ と subtitles.yaml を置く。texts.yaml（画面内の文字）と
sound/bgm.py（音）はあれば使う。書き出し先は <作品フォルダ>/renders/。
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import cairo
import imageio_ffmpeg
import numpy as np
import yaml

from . import assets, audio, text
from .config import FPS, H, LANGS, ROOT, W
from .draw import clamp
from .fx import Finish


class Cut:
    def __init__(self, folder):
        self.id = folder.name
        self.module = assets.load(folder / "cut.py")
        self.duration = float(self.module.DURATION)
        self.frames = int(round(self.duration * FPS))
        self.start = 0.0


class Env:
    """カットのスクリプトに渡す情報。言語や、画面内の文字の取り出しなど。"""

    def __init__(self, lang, texts, cut, frame, t_global):
        self.lang = lang
        self.texts = texts
        self.cut = cut
        self.frame = frame
        self.T = t_global

    def text(self, key):
        entry = self.texts.get(key, {})
        return entry.get(self.lang) or entry.get("ja", "")


class Project:
    def __init__(self, folder):
        self.dir = (ROOT / folder).resolve()
        cut_dirs = sorted(p for p in (self.dir / "cuts").iterdir()
                          if p.is_dir() and not p.name.startswith("_") and (p / "cut.py").exists())
        self.cuts = [Cut(p) for p in cut_dirs]
        t = 0.0
        for c in self.cuts:
            c.start = t
            t += c.frames / FPS
        self.duration = t
        self.subs = yaml.safe_load((self.dir / "subtitles.yaml").read_text(encoding="utf-8")) or []
        tp = self.dir / "texts.yaml"
        self.texts = yaml.safe_load(tp.read_text(encoding="utf-8")) if tp.exists() else {}
        self.out = self.dir / "renders"

    def cut(self, cut_id):
        return next(c for c in self.cuts if c.id == cut_id)

    def check_translations(self):
        missing = [s for s in self.subs if not (s.get("en") or "").strip()]
        for s in missing:
            print(f"  ! 英訳がありません: {s['cut']} {s.get('ja')}", file=sys.stderr)
        return not missing


# ---------------------------------------------------------------- 1フレーム

def draw_subtitles(ctx, project, cut, t, lang):
    for s in project.subs:
        if s["cut"] != cut.id:
            continue
        at, dur = float(s["at"]), float(s["dur"])
        if not at <= t < at + dur:
            continue
        body = (s.get(lang) or "").strip()
        if not body:
            continue
        a = clamp((t - at) / 0.3) * clamp((at + dur - t) / 0.3)
        size = 50 if lang == "ja" else 48
        img = text.render(body, size, lang=lang, max_width=1500, weight=500, tracking=2 if lang == "ja" else 0)
        img.paint(ctx, W / 2, H - 64, alpha=a, anchor="bottom")


def render_frame(surface, scale, project, cut, i, lang, finish):
    t = i / FPS
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    ctx.scale(scale, scale)
    env = Env(lang, project.texts, cut, i, cut.start + t)
    ctx.save()
    cut.module.draw(ctx, t, env)
    ctx.restore()
    draw_subtitles(ctx, project, cut, t, lang)
    surface.flush()
    finish.apply(surface, int(cut.start * FPS) + i)


def frame_bytes(surface):
    w, h = surface.get_width(), surface.get_height()
    stride = surface.get_stride()
    arr = np.ndarray((h, stride // 4, 4), np.uint8, surface.get_data())
    return arr[:, :w].tobytes()


def new_surface(scale):
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)


# ---------------------------------------------------------------- 音・字幕ファイル

def build_audio(project):
    path = project.out / "audio.wav"
    bgm = project.dir / "sound" / "bgm.py"
    if not bgm.exists():
        return None
    module = assets.load(bgm)
    timeline = [(c.id, c.start, c.frames / FPS) for c in project.cuts]
    buf = module.build(timeline, project.duration)
    audio.write_wav(path, buf)
    return path


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(project, lang, path):
    starts = {c.id: c.start for c in project.cuts}
    rows = []
    for s in sorted(project.subs, key=lambda s: starts[s["cut"]] + float(s["at"])):
        body = (s.get(lang) or "").strip()
        if not body:
            continue
        a = starts[s["cut"]] + float(s["at"])
        rows.append(f"{len(rows) + 1}\n{srt_time(a)} --> {srt_time(a + float(s['dur']))}\n{body}\n")
    path.write_text("\n".join(rows), encoding="utf-8")


# ---------------------------------------------------------------- 書き出し

def render_video(project, lang, scale, audio_path):
    out_dir = project.out / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{project.dir.name}_{lang}"
    video = out_dir / f"{name}.mp4"
    surface = new_surface(scale)
    w, h = surface.get_width(), surface.get_height()
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-"]
    if audio_path:
        cmd += ["-i", str(audio_path)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
            "-tune", "animation", "-movflags", "+faststart"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(str(video))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    finish = Finish(w, h)
    t0 = time.time()
    for cut in project.cuts:
        for i in range(cut.frames):
            render_frame(surface, scale, project, cut, i, lang, finish)
            proc.stdin.write(frame_bytes(surface))
        print(f"  {lang} {cut.id} 完了（{time.time() - t0:.0f}秒経過）")
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg が失敗しました")
    write_srt(project, lang, out_dir / f"{name}.srt")
    return video


def render_still(project, cut_id, t, lang, scale, path):
    cut = project.cut(cut_id)
    surface = new_surface(scale)
    render_frame(surface, scale, project, cut, int(t * FPS), lang, Finish(surface.get_width(), surface.get_height()))
    surface.write_to_png(str(path))


def render_contact(project, lang, per_cut=3, scale=0.3):
    """各カットの始め・中ほど・終わりの静止画を並べた一覧を作る。"""
    tiles = []
    for cut in project.cuts:
        for k in range(per_cut):
            t = cut.duration * (k + 0.5) / per_cut
            s = new_surface(scale)
            render_frame(s, scale, project, cut, int(t * FPS), lang, Finish(s.get_width(), s.get_height()))
            tiles.append((cut.id, t, s))
    tw, th = tiles[0][2].get_width(), tiles[0][2].get_height()
    gap, label = 6, 26
    sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, per_cut * (tw + gap) + gap,
                               len(project.cuts) * (th + gap + label) + gap)
    ctx = cairo.Context(sheet)
    ctx.set_source_rgb(0.08, 0.08, 0.1)
    ctx.paint()
    for n, (cid, t, s) in enumerate(tiles):
        r, c = divmod(n, per_cut)
        x, y = gap + c * (tw + gap), gap + r * (th + gap + label)
        ctx.set_source_rgb(0.85, 0.85, 0.9)
        ctx.select_font_face("Consolas")
        ctx.set_font_size(16)
        ctx.move_to(x + 2, y + 18)
        ctx.show_text(f"{cid}  t={t:.2f}s")
        ctx.set_source_surface(s, x, y + label)
        ctx.paint()
    path = project.out / "stills" / f"contact_{lang}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.write_to_png(str(path))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="カットを描いて映像に書き出す")
    ap.add_argument("project", help="作品フォルダ（例：pilot）")
    ap.add_argument("--lang", default="all", choices=("all",) + LANGS)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--still", action="append", default=[], help="カットID:秒（例：PL_c004:2.5）")
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args(argv)

    project = Project(args.project)
    langs = LANGS if args.lang == "all" else (args.lang,)
    project.out.mkdir(parents=True, exist_ok=True)
    print(f"{project.dir.name}: {len(project.cuts)}カット、{project.duration:.1f}秒")

    if args.contact or args.still:
        for lang in langs:
            if args.contact:
                print("  一覧:", render_contact(project, lang))
            for spec in args.still:
                cid, t = spec.split(":")
                path = project.out / "stills" / f"{cid}_{float(t):05.2f}_{lang}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                render_still(project, cid, float(t), lang, args.scale, path)
                print("  静止画:", path)
        return

    if "en" in langs:
        project.check_translations()
    audio_path = None if args.no_audio else build_audio(project)
    if audio_path:
        print("  音:", audio_path)
    for lang in langs:
        print("  映像:", render_video(project, lang, args.scale, audio_path))


if __name__ == "__main__":
    main()
