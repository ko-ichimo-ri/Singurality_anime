"""カットを順に描いて、1本の映像に書き出す。

使い方（リポジトリの一番上で実行）:

    .venv/Scripts/python -m engine.render pilot                 日本語版と英語版を書き出す
    .venv/Scripts/python -m engine.render pilot --lang ja       日本語版だけ
    .venv/Scripts/python -m engine.render pilot --style manga   作風を変える（engine/styles/ にあるもの）
    .venv/Scripts/python -m engine.render pilot --voice         声を付ける（voices.yaml の設定を使う）
    .venv/Scripts/python -m engine.render pilot --contact       各カットの静止画を一覧にした確認用の画像
    .venv/Scripts/python -m engine.render pilot --still PL_c004:2.5   1枚だけ静止画
    .venv/Scripts/python -m engine.render pilot --scale 0.5     半分の大きさで速く確認

<作品フォルダ> には cuts/ と subtitles.yaml を置く。texts.yaml（画面内の文字）、sound/bgm.py（音）、
voices.yaml（声）はあれば使う。project.yaml に `inherit: pilot` と書くと、自分のフォルダにない
ファイルは pilot のものを使う。project.yaml の style / voice は、コマンドで指定しなかったときの既定値。
書き出し先は <作品フォルダ>/renders/。
"""

import argparse
import importlib
import subprocess
import sys
import time

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


class Style:
    """作風。engine/styles/<名前>.py を読み込む。名前がなければ、そのままの見た目。

    作風のファイルに書けるもの（どれも省略できる）:
      char_tint(tint) / prop_tint(tint)  キャラクター・小物の色の寄せ方を上書きする
      post(arr, frame)                   書き上がった画面（高さ×幅×4 の BGRA 配列）を加工する
      FINISH                             仕上げ（粒子・周辺減光）の強さ
      SUBTITLE                           字幕の色と影
    """

    def __init__(self, name):
        self.name = name
        self.mod = importlib.import_module(f"engine.styles.{name}") if name else None

    def _get(self, key, default=None):
        return getattr(self.mod, key, default) if self.mod else default

    def char_tint(self, tint):
        f = self._get("char_tint")
        return f(tint) if f else tint

    def prop_tint(self, tint):
        f = self._get("prop_tint")
        return f(tint) if f else tint

    def finish(self, w, h):
        return Finish(w, h, **self._get("FINISH", {}))

    def post(self, surface, frame):
        f = self._get("post")
        if not f:
            return
        surface.flush()
        h, stride = surface.get_height(), surface.get_stride()
        arr = np.ndarray((h, stride // 4, 4), np.uint8, surface.get_data())[:, :surface.get_width()]
        f(arr, frame)
        surface.mark_dirty()

    @property
    def subtitle(self):
        return self._get("SUBTITLE", {})


class Env:
    """カットのスクリプトに渡す情報。言語、作風、画面内の文字の取り出しなど。"""

    def __init__(self, lang, texts, cut, frame, t_global, style):
        self.lang = lang
        self.texts = texts
        self.cut = cut
        self.frame = frame
        self.T = t_global
        self.style = style

    def text(self, key):
        entry = self.texts.get(key, {})
        return entry.get(self.lang) or entry.get("ja", "")

    def char_tint(self, tint=None):
        """キャラクターに渡す色の寄せ方。作風によって上書きされる（影絵なら真っ黒になど）。"""
        return self.style.char_tint(tint)

    def prop_tint(self, tint=None):
        return self.style.prop_tint(tint)


class Project:
    def __init__(self, folder):
        self.dir = (ROOT / folder).resolve()
        cfg_path = self.dir / "project.yaml"
        self.cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        self.cfg = self.cfg or {}
        self.base = (ROOT / self.cfg["inherit"]).resolve() if self.cfg.get("inherit") else None
        cut_dirs = sorted(p for p in (self.dir / "cuts").iterdir()
                          if p.is_dir() and not p.name.startswith("_") and (p / "cut.py").exists())
        self.cuts = [Cut(p) for p in cut_dirs]
        t = 0.0
        for c in self.cuts:
            c.start = t
            t += c.frames / FPS
        self.duration = t
        self.subs = self._yaml("subtitles.yaml") or []
        self.texts = self._yaml("texts.yaml") or {}
        self.voices = self._yaml("voices.yaml") or {}
        self.out = self.dir / "renders"

    def find(self, name):
        for d in (self.dir, self.base):
            if d is not None and (d / name).exists():
                return d / name
        return None

    def _yaml(self, name):
        p = self.find(name)
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p else None

    def cut(self, cut_id):
        return next(c for c in self.cuts if c.id == cut_id)

    def check_translations(self):
        missing = [s for s in self.subs if not (s.get("en") or "").strip()]
        for s in missing:
            print(f"  ! 英訳がありません: {s['cut']} {s.get('ja')}", file=sys.stderr)
        return not missing


# ---------------------------------------------------------------- 1フレーム

def draw_subtitles(ctx, project, cut, t, lang, style):
    st = style.subtitle
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
        img = text.render(body, size, lang=lang, max_width=1500, weight=500,
                          tracking=2 if lang == "ja" else 0,
                          color=tuple(st.get("color", (255, 255, 255))),
                          shadow=st.get("shadow", 10), shadow_alpha=st.get("shadow_alpha", 190))
        img.paint(ctx, W / 2, H - 64, alpha=a, anchor="bottom")


def render_frame(surface, scale, project, cut, i, lang, finish, style):
    t = i / FPS
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    ctx.scale(scale, scale)
    env = Env(lang, project.texts, cut, i, cut.start + t, style)
    ctx.save()
    cut.module.draw(ctx, t, env)
    ctx.restore()
    frame = int(cut.start * FPS) + i
    style.post(surface, frame)
    ctx = cairo.Context(surface)
    ctx.scale(scale, scale)
    if hasattr(cut.module, "overlay"):
        # 作風のフィルターをかけずに重ねるもの（タイトルなど）
        ctx.save()
        cut.module.overlay(ctx, t, env)
        ctx.restore()
    draw_subtitles(ctx, project, cut, t, lang, style)
    surface.flush()
    finish.apply(surface, frame)


def frame_bytes(surface):
    w, h = surface.get_width(), surface.get_height()
    stride = surface.get_stride()
    arr = np.ndarray((h, stride // 4, 4), np.uint8, surface.get_data())
    return arr[:, :w].tobytes()


def new_surface(scale):
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)


# ---------------------------------------------------------------- 音・字幕ファイル

def timeline(project):
    return [(c.id, c.start, c.frames / FPS) for c in project.cuts]


def build_music(project):
    """BGM と効果音。言語によらず共通。"""
    bgm = project.find("sound/bgm.py")
    if not bgm:
        return None
    return assets.load(bgm).build(timeline(project), project.duration)


def add_voices(buf, project, lang):
    """字幕に合わせて声を重ね、話しているあいだは BGM を少し下げる。"""
    from . import voice
    starts = {c.id: c.start for c in project.cuts}
    duck = np.ones(len(buf), np.float32)
    for s in project.subs:
        who = s.get("who")
        body = (s.get(lang) or "").strip()
        cfg = project.voices.get(who, {}).get(lang) if who else None
        if not (cfg and body):
            continue
        clip = voice.speak(lang, body, cfg, cache=project.out / "voice_cache")
        t0 = starts[s["cut"]] + float(s.get("voice_at", s["at"]))
        i0, n = int(t0 * audio.SR), len(clip)
        ramp = int(0.25 * audio.SR)
        env = np.ones(n + 2 * ramp, np.float32) * 0.55
        env[:ramp] = np.linspace(1, 0.55, ramp)
        env[-ramp:] = np.linspace(0.55, 1, ramp)
        a, b = max(i0 - ramp, 0), min(i0 + n + ramp, len(duck))
        duck[a:b] = np.minimum(duck[a:b], env[a - (i0 - ramp):b - (i0 - ramp)])
        clip = audio.reverb(np.stack([clip, clip], 1), seconds=0.9, mix=0.12)
        audio.add(buf, clip * float(cfg.get("gain", 1.0)), t0)
    return buf, duck


def build_audio(project, variant, lang, voiced, music_cache={}):
    key = str(project.dir)
    if key not in music_cache:
        music_cache[key] = build_music(project)
    music = music_cache[key]
    if music is None:
        return None
    path = project.out / (f"audio_{variant}_{lang}.wav" if voiced else "audio.wav")
    if voiced:
        voices = np.zeros_like(music)
        voices, duck = add_voices(voices, project, lang)
        mixed = music * duck[:, None] + voices
    else:
        mixed = music
    project.out.mkdir(parents=True, exist_ok=True)
    audio.write_wav(path, mixed)
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

def variant_name(style, voiced):
    parts = [style.name] if style.name else []
    if voiced:
        parts.append("voice")
    return "_".join(parts)


def encoder(path, w, h, audio_path, crf):
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-"]
    if audio_path:
        cmd += ["-i", str(audio_path)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-tune", "animation", "-movflags", "+faststart"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(str(path))
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def output_dir(project, variant, lang):
    return project.out / variant / lang if variant else project.out / lang


def render_video(project, lang, scale, audio_path, style, variant, crf):
    out_dir = output_dir(project, variant, lang)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "_".join(p for p in (project.dir.name, variant, lang) if p)
    video = out_dir / f"{name}.mp4"
    surface = new_surface(scale)
    proc = encoder(video, surface.get_width(), surface.get_height(), audio_path, crf)
    finish = style.finish(surface.get_width(), surface.get_height())
    t0 = time.time()
    for cut in project.cuts:
        for i in range(cut.frames):
            render_frame(surface, scale, project, cut, i, lang, finish, style)
            proc.stdin.write(frame_bytes(surface))
        print(f"  {variant or 'base'} {lang} {cut.id} 完了（{time.time() - t0:.0f}秒経過）", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg が失敗しました")
    write_srt(project, lang, out_dir / f"{name}.srt")
    return video


def render_still(project, cut_id, t, lang, scale, path, style):
    cut = project.cut(cut_id)
    surface = new_surface(scale)
    render_frame(surface, scale, project, cut, int(t * FPS), lang,
                 style.finish(surface.get_width(), surface.get_height()), style)
    surface.write_to_png(str(path))


def render_contact(project, lang, style, per_cut=3, scale=0.3):
    """各カットの始め・中ほど・終わりの静止画を並べた一覧を作る。"""
    tiles = []
    for cut in project.cuts:
        for k in range(per_cut):
            t = cut.duration * (k + 0.5) / per_cut
            s = new_surface(scale)
            render_frame(s, scale, project, cut, int(t * FPS), lang,
                         style.finish(s.get_width(), s.get_height()), style)
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
    suffix = f"_{style.name}" if style.name else ""
    path = project.out / "stills" / f"contact{suffix}_{lang}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.write_to_png(str(path))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="カットを描いて映像に書き出す")
    ap.add_argument("project", help="作品フォルダ（例：pilot）")
    ap.add_argument("--lang", default="all", choices=("all",) + LANGS)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--style", default=None, help="作風（engine/styles/ のファイル名）")
    ap.add_argument("--voice", action="store_true", default=None, help="声を付ける")
    ap.add_argument("--crf", type=int, default=20, help="画質（小さいほど高画質・大きいファイル）")
    ap.add_argument("--still", action="append", default=[], help="カットID:秒（例：PL_c004:2.5）")
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args(argv)

    project = Project(args.project)
    style = Style(args.style if args.style is not None else project.cfg.get("style"))
    voiced = args.voice if args.voice is not None else bool(project.cfg.get("voice"))
    variant = project.cfg.get("variant") or variant_name(style, voiced)
    langs = LANGS if args.lang == "all" else (args.lang,)
    project.out.mkdir(parents=True, exist_ok=True)
    print(f"{project.dir.name}: {len(project.cuts)}カット、{project.duration:.1f}秒、"
          f"作風={style.name or 'そのまま'}、声={'あり' if voiced else 'なし'}", flush=True)

    if args.contact or args.still:
        for lang in langs:
            if args.contact:
                print("  一覧:", render_contact(project, lang, style))
            for spec in args.still:
                cid, t = spec.split(":")
                suffix = f"_{style.name}" if style.name else ""
                path = project.out / "stills" / f"{cid}_{float(t):05.2f}{suffix}_{lang}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                render_still(project, cid, float(t), lang, args.scale, path, style)
                print("  静止画:", path)
        return

    if "en" in langs:
        project.check_translations()
    for lang in langs:
        audio_path = None if args.no_audio else build_audio(project, variant, lang, voiced)
        if audio_path:
            print("  音:", audio_path, flush=True)
        print("  映像:", render_video(project, lang, args.scale, audio_path, style, variant, args.crf), flush=True)


if __name__ == "__main__":
    main()
