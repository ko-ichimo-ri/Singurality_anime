# 05_voice：声付き

パイロット版のアンドロイドのセリフに、音声合成の声を付けた版です。話しているあいだは BGM を少し下げます。
声の設定は [pilot/voices.yaml](../../pilot/voices.yaml) にあります。

| 言語 | ソフト | 声 | 選んだ理由 | 利用条件 |
|---|---|---|---|---|
| 日本語 | VOICEVOX | 冥鳴ひまり（ノーマル） | 落ち着いた、やわらかい大人の声。「人間そっくり」の設定に合う | 商用・非商用可。**「VOICEVOX:冥鳴ひまり」の表記が必要** |
| 英語 | Piper | kristin（アメリカ英語） | 穏やかで、日本語の声と雰囲気が近い | パブリックドメインの朗読から学習 |

## 聞き比べ用のサンプル

`renders/samples/` に、同じセリフをほかの声で読ませたものを置いています（Git 管理外）。

| ファイル | 声 | 利用条件 |
|---|---|---|
| ja_01_meimei-himari.wav | 冥鳴ひまり（採用） | 商用・非商用可、表記必要 |
| ja_02_no7.wav | No.7 | 非商用（同人・配信収入は可）、表記必要 |
| ja_03_sayo.wav | 小夜/SAYO | 商用・非商用可、表記必要 |
| ja_04_nurse-robo-type-t.wav | ナースロボ＿タイプＴ（ロボットらしい声） | 商用・非商用可、表記必要 |
| ja_05_voidoll.wav | Voidoll（ロボットのキャラクター） | 個人は商用・非商用可、表記「VOICEVOX:Voidoll(CV:丹下桜)」 |
| en_01_kristin.wav | kristin（採用・アメリカ英語） | パブリックドメイン |
| en_02_cori.wav | cori（イギリス英語） | パブリックドメイン |

声を変えたいときは、`pilot/voices.yaml` の `speaker`（VOICEVOX の番号）や `model` を書きかえて書き出し直します。

## 書き出し方

```
.venv/Scripts/python -m engine.render experiments/05_voice
```
