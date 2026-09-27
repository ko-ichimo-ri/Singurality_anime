# 04_kamishibai：紙芝居

パイロット版の各カットから「決めの一瞬」を1枚ずつ取り出し、水彩の絵にして、木の紙芝居の舞台で見せる版です。
動くのはカメラ（ゆっくり寄る）と、カットの終わりに絵を右へ引き抜く動きだけ。最後の絵を引き抜くとタイトルの紙が出てきます。
音はパイロット版の BGM に、冒頭の拍子木と、絵を引き抜く紙の音を足しています。

- 舞台と絵：[stage.py](stage.py)（`KEYS` でカットごとの「決めの一瞬」を選んでいる）
- 音：[sound/bgm.py](sound/bgm.py)

## 書き出し方

```
.venv/Scripts/python -m engine.render experiments/04_kamishibai
```

書き出し先：`renders/ja/`・`renders/en/`（Git 管理外）
