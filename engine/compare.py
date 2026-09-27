"""いくつかの版を3×3に並べて、同時に流す比較用の動画を作る。

    .venv/Scripts/python -m engine.compare                     experiments/compare.yaml の版を並べる

音は1つ目の版のもの。書き出し先は experiments/renders/compare_{ja,en}.mp4。
"""

import subprocess

import cairo
import imageio_ffmpeg
import yaml

from . import text
from .config import LANGS, ROOT

TW, TH = 640, 360


def labels_png(items, path):
    """各マスの左上の名前と、9マス目の説明の画像。"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, TW * 3, TH * 3)
    ctx = cairo.Context(surf)
    for i, it in enumerate(items):
        x, y = (i % 3) * TW, (i // 3) * TH
        img = text.render(it["label"], 20, color=(255, 255, 255), shadow=0, weight=600)
        ctx.set_source_rgba(0, 0, 0, 0.55)
        ctx.rectangle(x, y, img.w - 4, img.h - 6)
        ctx.fill()
        img.paint(ctx, x + img.w / 2, y + img.h / 2)
    # 9マス目
    x, y = 2 * TW, 2 * TH
    ctx.set_source_rgb(0.07, 0.08, 0.12)
    ctx.rectangle(x, y, TW, TH)
    ctx.fill()
    for k, (s, size) in enumerate((("シンギュラリティ後の私たち", 30), ("パイロット版の作り比べ", 24),
                                   ("Us, After the Singularity", 22), ("Pilot variants", 20))):
        text.render(s, size, color=(235, 232, 225), shadow=0, serif=True).paint(ctx, x + TW / 2, y + 90 + k * 60)
    # マスの境目
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_line_width(3)
    for k in (1, 2):
        ctx.move_to(k * TW, 0)
        ctx.line_to(k * TW, TH * 3)
        ctx.move_to(0, k * TH)
        ctx.line_to(TW * 3, k * TH)
    ctx.stroke()
    surf.write_to_png(str(path))


def main():
    items = yaml.safe_load((ROOT / "experiments" / "compare.yaml").read_text(encoding="utf-8"))[:8]
    out_dir = ROOT / "experiments" / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "compare_labels.png"
    labels_png(items, png)
    for lang in LANGS:
        paths = [ROOT / it["path"].format(lang=lang) for it in items]
        missing = [str(p) for p in paths if not p.exists()]
        if missing:
            print(f"{lang}: まだない版があるので飛ばします:", *missing, sep="\n  ")
            continue
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error"]
        for p in paths:
            cmd += ["-i", str(p)]
        cmd += ["-loop", "1", "-i", str(png)]
        scales = "".join(f"[{i}:v]scale={TW}:{TH},setsar=1[v{i}];" for i in range(8))
        layout = "|".join(f"{(i % 3) * TW}_{(i // 3) * TH}" for i in range(8))
        filt = (scales + "color=c=black:s=%dx%d:r=24[bg];" % (TW, TH) + "".join(f"[v{i}]" for i in range(8)) +
                "[bg]xstack=inputs=9:layout=" + layout + f"|{2 * TW}_{2 * TH}:shortest=1[grid];"
                "[grid][8:v]overlay=shortest=1[out]")
        out = out_dir / f"compare_{lang}.mp4"
        cmd += ["-filter_complex", filt, "-map", "[out]", "-map", "0:a?", "-c:v", "libx264", "-crf", "21",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
        print("比較用の動画:", out)


if __name__ == "__main__":
    main()
