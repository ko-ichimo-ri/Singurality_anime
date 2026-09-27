# パイロット版の作り比べ

パイロット版（[pilot/](../pilot/)・雨の駅前・44.5秒）を、いろいろな作り方・作風で作った試作です。
**どれも同じ8カット・同じ尺・同じ字幕**なので、見た目（と声）の違いだけを比べられます。
日本語版と英語版を、それぞれ別の動画として書き出しています。

| # | 名前 | 作り方 | 見どころ | 書き出し先（Git 管理外） |
|---|---|---|---|---|
| 00 | 元のパイロット版 | Python（cairo）の2Dベクター | 基準 | `pilot/renders/{ja,en}/` |
| 01 | [水彩](01_watercolor/) | 00 に水彩のフィルター | 紙の質感、にじみ、紙の目の揺らぎ | `01_watercolor/renders/{ja,en}/` |
| 02 | [漫画](02_manga/) | 00 に網点と描線のフィルター | 白黒の中で傘だけが色を持つ | `02_manga/renders/{ja,en}/` |
| 03 | [影絵](03_silhouette/) | 00 の人物を影に | 光と影だけ。首すじの光だけが影に染まらない | `03_silhouette/renders/{ja,en}/` |
| 04 | [紙芝居](04_kamishibai/) | 00 の決めの一瞬を水彩の1枚絵に | 木の舞台、絵の引き抜き、拍子木 | `04_kamishibai/renders/{ja,en}/` |
| 05 | [声付き](05_voice/) | 00 に音声合成の声 | 日本語は VOICEVOX、英語は Piper | `05_voice/renders/{ja,en}/` |
| 06 | [Blender トゥーン](06_blender_toon/) | Blender 5.2（EEVEE）の3D | セル調の陰影と輪郭線、濡れた地面の映り込み | `06_blender_toon/renders/{ja,en}/` |
| 07 | [Blender ジオラマ](07_blender_diorama/) | Blender 5.2（EEVEE）の3D | 木の人形とミニチュアの街、強いぼけ、コマ撮り風 | `07_blender_diorama/renders/{ja,en}/` |

全部を画面の3×3に並べて同時に流す比較用の動画：`experiments/renders/compare_{ja,en}.mp4`

## 書き出し方

リポジトリの一番上で実行します。

```
# 01〜05（Python だけで作るもの）
.venv/Scripts/python -m engine.render experiments/01_watercolor

# 06・07（Blender でフレームを書き出してから、字幕と音を重ねる）
<blender.exe> -b --factory-startup -P experiments/blender/build.py -- --variant toon --out experiments/06_blender_toon/renders/frames
.venv/Scripts/python -m engine.overlay experiments/06_blender_toon

# 比較用の動画
.venv/Scripts/python -m engine.compare
```

各フォルダの `project.yaml` に `inherit: pilot` と書いてあり、カット・字幕・音はパイロット版のものを引き継ぎます。

## 使っているソフト（どれも無料）

| ソフト | 用途 | 入れた場所 |
|---|---|---|
| Blender 5.2.2 LTS | 06・07 の3D | `%LOCALAPPDATA%\Programs\blender-5.2.2-windows-x64` |
| VOICEVOX エンジン 0.25.2 | 日本語の声 | `%LOCALAPPDATA%\Programs\voicevox_engine-0.25.2` |
| Piper | 英語の声 | `%LOCALAPPDATA%\Programs\piper`（声のデータは `voices/`） |

## 動画サイトに投稿するときの注意

- **05 声付き版**は、VOICEVOX の利用規約により **「VOICEVOX:冥鳴ひまり」のクレジット表記が必要**です（動画の最後に表示済み。概要欄にも書くのがおすすめ）
- 英語の声（Piper の kristin）は、パブリックドメインの朗読から作られた声です
- ほかの版は、声・音楽・絵のすべてをこのリポジトリのコードで作っているので、第三者の素材は含みません（フォントは Noto Sans / Serif JP、SIL Open Font License）
