"""ほかの方法（Blender など）で書き出したフレーム画像に、字幕・タイトル・音を重ねて映像にする。

    .venv/Scripts/python -m engine.overlay experiments/06_blender_toon

作品フォルダの project.yaml に、フレーム画像の場所（frames）を書いておく。
カットの長さ・字幕・タイトル・音は、引き継ぎ元（inherit）の作品のものを使う。
タイトルは、引き継ぎ元のカットに overlay() があればそれで描く。
"""

import argparse
import sys
import time

import cairo
import numpy as np
from PIL import Image

from . import render
from .config import FPS, H, LANGS, W
from .draw import clamp, fade
from .fx import Finish


def load_frame(path, surface):
    rgb = np.asarray(Image.open(path).convert("RGB").resize((W, H)))
    buf = np.ndarray((H, surface.get_stride() // 4, 4), np.uint8, surface.get_data())[:, :W]
    surface.flush()
    buf[..., 0] = rgb[..., 2]
    buf[..., 1] = rgb[..., 1]
    buf[..., 2] = rgb[..., 0]
    buf[..., 3] = 255
    surface.mark_dirty()


def main(argv=None):
    ap = argparse.ArgumentParser(description="フレーム画像に字幕と音を重ねて映像にする")
    ap.add_argument("project")
    ap.add_argument("--lang", default="all", choices=("all",) + LANGS)
    ap.add_argument("--crf", type=int, default=20)
    args = ap.parse_args(argv)

    project = render.Project(args.project)
    frames_dir = project.dir / project.cfg.get("frames", "renders/frames")
    style = render.Style(None)
    fade_in = float(project.cfg.get("fade_in", 0))
    langs = LANGS if args.lang == "all" else (args.lang,)
    total = sum(c.frames for c in project.cuts)
    missing = [i for i in range(1, total + 1) if not (frames_dir / f"frame_{i:05d}.jpg").exists()]
    if missing:
        print(f"フレームが {len(missing)} 枚足りません（最初：{missing[0]}）", file=sys.stderr)
        sys.exit(1)

    for lang in langs:
        audio_path = render.build_audio(project, "", lang, False)
        out_dir = project.out / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        name = f"{project.dir.name}_{lang}"
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        proc = render.encoder(out_dir / f"{name}.mp4", W, H, audio_path, args.crf)
        finish = Finish(W, H, grain=2.0, vignette=0.3)
        n = 0
        t0 = time.time()
        for cut in project.cuts:
            for i in range(cut.frames):
                n += 1
                load_frame(frames_dir / f"frame_{n:05d}.jpg", surface)
                t = i / FPS
                ctx = cairo.Context(surface)
                env = render.Env(lang, project.texts, cut, i, cut.start + t, style)
                if hasattr(cut.module, "overlay"):
                    ctx.save()
                    cut.module.overlay(ctx, t, env)
                    ctx.restore()
                render.draw_subtitles(ctx, project, cut, t, lang, style)
                if fade_in and cut.start + t < fade_in:
                    fade(ctx, 1 - clamp((cut.start + t) / fade_in))
                surface.flush()
                finish.apply(surface, n)
                proc.stdin.write(render.frame_bytes(surface))
            print(f"  {lang} {cut.id} 完了（{time.time() - t0:.0f}秒経過）", flush=True)
        proc.stdin.close()
        proc.wait()
        render.write_srt(project, lang, out_dir / f"{name}.srt")
        print("  映像:", out_dir / f"{name}.mp4", flush=True)


if __name__ == "__main__":
    main()
