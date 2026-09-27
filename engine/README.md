# engine

映像と音を生成する共通の仕組み（Python）です。各カットのスクリプト（`cuts/<カット>/cut.py`）や、デザイン（`03_design/`）から使います。

## 準備（初回のみ）

リポジトリの一番上で実行します。

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

- 使うライブラリ：pycairo（描画）、numpy（計算・音）、Pillow（文字）、PyYAML（字幕）、imageio-ffmpeg（動画の書き出し。ffmpeg が同梱されている）
- 字幕のフォントは Noto Sans JP / Noto Serif JP を使う（Windows に入っているもの。`engine/fonts/` に置けばそちらが優先）

## 使い方

```
.venv/Scripts/python -m engine.render <作品フォルダ>                 日本語版と英語版を書き出す
.venv/Scripts/python -m engine.render <作品フォルダ> --lang ja       日本語版だけ
.venv/Scripts/python -m engine.render <作品フォルダ> --contact       全カットの静止画一覧
.venv/Scripts/python -m engine.render <作品フォルダ> --still PL_c004:2.5   1枚だけ静止画
.venv/Scripts/python -m engine.render <作品フォルダ> --scale 0.5     半分の大きさで速く確認
.venv/Scripts/python -m engine.sheet characters/ossan               設定画（sheet.png）を作り直す
```

`<作品フォルダ>` は `pilot` や `10_ossan/production` など。中に次のものを置きます。

| ファイル | 中身 |
|---|---|
| `cuts/<カットID>/cut.py` | カットの描画。`DURATION`（秒）と `draw(ctx, t, env)` を持つ。カットは名前の順に並ぶ |
| `subtitles.yaml` | 字幕（日本語と英語を1項目に並べる）。英訳の抜けがあると警告が出る |
| `texts.yaml` | 画面内の文字（タイトルなど）。カットからは `env.text("title")` で取り出す |
| `sound/bgm.py` | 音。`build(timeline, duration)` がステレオの配列を返す |

## 部品

| ファイル | 中身 |
|---|---|
| `config.py` | 解像度（1920×1080）、24fps、音のサンプリング周波数、フォント |
| `draw.py` | 色、形、グラデーション、カメラ（`camera`）、キャラクターを置く（`place`）、時間のカーブ（`seg`・`smooth` など）、腕の計算（`ik`） |
| `rig.py` | キャラクターの骨組み：歩き方、腕や脚の描き方、描いた点の座標を取り出す（`Anchor`） |
| `fx.py` | 雨、波紋、しずく、光のにじみ、地面の照り返し、仕上げ（周辺減光・粒子） |
| `text.py` | 字幕や画面内の文字（日本語・英語） |
| `audio.py` | ピアノ風の音、和音、雨、傘の雨音、足音、残響、wav の書き出し |
| `assets.py` | `03_design/` のモデルの読み込み |
| `render.py` | カットを並べて映像にする。音と字幕ファイルも書き出す |
| `sheet.py` | 設定画の書き出し |

## カットの書き方（例）

```python
from engine import assets
from engine.draw import seg, smooth

DURATION = 4.5
ossan = assets.character("ossan")

def draw(ctx, t, env):
    # t はカットの頭からの秒数。env.lang で言語、env.text(key) で画面内の文字
    head = smooth(seg(t, 1.0, 2.0)) * -0.2   # 1〜2秒で顔を上げる
    ossan.side(ctx, 900, 960, 780, head=head)
```

同じ t からは、いつも同じ画が描かれるようにします（乱数は seed で固定）。そうすれば、どのフレームからでも書き出せます。

## 書き出し先

`<作品フォルダ>/renders/`（Git 管理外）

```
renders/
  audio.wav       音
  ja/             日本語版（mp4 と srt）
  en/             英語版（mp4 と srt）
  stills/         確認用の静止画
```
