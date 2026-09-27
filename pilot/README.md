# パイロット版：雨の駅前

おっさん編のメモ（[90_ideas/README.md](../90_ideas/README.md)）にある、雨の駅前の場面を映像にした試作です。
絵柄・動き・音の方向性を確かめるためのもので、本編のカット番号とは分けて `PL_` で始まるIDを使っています。

- 尺：44.5秒・8カット（[カット表](cut_list.md)）
- 字幕：日本語・英語（[subtitles.yaml](subtitles.yaml)）。セリフはメモにある一言だけ
- 画面内の文字：タイトルなど（[texts.yaml](texts.yaml)）
- 音：ピアノ・雨・足音を Python で合成（[sound/bgm.py](sound/bgm.py)）
- デザイン：[おっさん](../03_design/characters/ossan/sheet.png)・[アンドロイド](../03_design/characters/android/sheet.png)・[傘](../03_design/props/umbrella/sheet.png)・舞台（[03_design/locations/station_rain](../03_design/locations/station_rain/model.py)）

## 書き出し方

リポジトリの一番上で実行します（初回のみ、下の「準備」が必要）。

```
.venv/Scripts/python -m engine.render pilot              日本語版と英語版
.venv/Scripts/python -m engine.render pilot --contact    全カットの静止画一覧（確認用）
```

書き出し先（Git 管理外）：

| ファイル | 中身 |
|---|---|
| `renders/ja/pilot_ja.mp4` | 日本語版 |
| `renders/en/pilot_en.mp4` | 英語版 |
| `renders/*/pilot_*.srt` | 字幕ファイル |
| `renders/stills/` | 確認用の静止画 |

## 準備（初回のみ）

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

動画の書き出しに使う ffmpeg は、`imageio-ffmpeg` パッケージに同梱されたものを使います。

## ここで決めたこと（本編にも引き継ぐ案）

- 夜の雨は青を基調に、**傘だけを唯一のあたたかい色**（からし色）にする
- アンドロイドの機械らしさは、首すじと手首の細い光の線、瞳の奥の光だけで見せる
- おっさんは言葉ではなく、姿勢（猫背、うつむき、ポケットの手）で気持ちを見せる
- 二人の歩幅（足取りの速さ）をわざとずらしている
