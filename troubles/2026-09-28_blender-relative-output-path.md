# Blender の書き出し先がリポジトリの外（C:\experiments）になった

- 日付：2026-09-28
- ブランチ：experiments/pilot-variants
- 状態：解決済み

## 何が起きたか

Blender を `-P experiments/blender/build.py -- --out experiments/06_blender_toon/renders/stills` のように、
相対パスの書き出し先で実行した。画像はリポジトリの中ではなく `C:\experiments\06_blender_toon\renders\stills\` に保存された。

## 原因

Blender の中の Python では、相対パスがリポジトリの一番上を基準に解釈されなかった（C ドライブの直下が基準になった）。

## 対処

- できた画像を正しい場所へ移し、`C:\experiments` を削除した
- `build.py` で、相対パスはリポジトリの一番上を基準に絶対パスへ直すようにした

## 再発防止

Blender など、別のプログラムにファイルの場所を渡すときは絶対パスにする（スクリプトの中で `Path(__file__)` から組み立てる）。
