"""映像全体の設定。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

W, H = 1920, 1080
FPS = 24
SAMPLE_RATE = 48000

# 字幕・画面内の文字に使うフォント。上から順に探し、最初に見つかったものを使う
FONT_CANDIDATES = [
    ROOT / "engine" / "fonts" / "NotoSansJP-VF.ttf",
    Path("C:/Windows/Fonts/NotoSansJP-VF.ttf"),
    Path("C:/Windows/Fonts/YuGothM.ttc"),
    Path("C:/Windows/Fonts/meiryo.ttc"),
]
FONT_SERIF_CANDIDATES = [
    ROOT / "engine" / "fonts" / "NotoSerifJP-VF.ttf",
    Path("C:/Windows/Fonts/NotoSerifJP-VF.ttf"),
    Path("C:/Windows/Fonts/BIZ-UDMinchoM.ttc"),
]

LANGS = ("ja", "en")
