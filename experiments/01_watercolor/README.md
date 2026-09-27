# 01_watercolor：水彩

パイロット版に水彩のフィルター（engine/styles/watercolor.py）をかけた版。形を単純にしてにじませ、顔料がたまる縁と紙の目を足す。暗いところも紙の色が透けるので、元の版よりやわらかく明るい。紙の目は3フレームごとに揺らいで、手で描いたような揺らぎを出す。

## 書き出し方

```
.venv/Scripts/python -m engine.render experiments/01_watercolor
```

書き出し先：`renders/ja/`・`renders/en/`（Git 管理外）
