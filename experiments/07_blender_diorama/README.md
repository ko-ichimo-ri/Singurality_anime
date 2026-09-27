# 07_blender_diorama：Blender ジオラマ

木の人形とミニチュアの街。強いぼけでピントの合う範囲を狭くし、模型を撮ったように見せる。人形の動きは1秒12コマにして、コマ撮り（ストップモーション）風にしている。

3Dの舞台（駅前・改札・通り・街並み）と人形は [../blender/build.py](../blender/build.py) がコードだけで組み立てる。
人形は関節をつないだ簡単なもので、表情の演技はできない。そのぶん人形らしさを作風として活かしている。

## 書き出し方

```
<blender.exe> -b --factory-startup -P experiments/blender/build.py -- --variant diorama --out experiments/07_blender_diorama/renders/frames
.venv/Scripts/python -m engine.overlay experiments/07_blender_diorama
```

- 1つ目で 1,068 枚のフレーム画像を書き出す（途中で止めても、続きから再開できる）
- 2つ目で字幕・タイトル・音を重ねて、日本語版と英語版の動画にする
- 静止画だけ確認するときは `--still PL_c004:3.5 --scale 0.4` を付ける
