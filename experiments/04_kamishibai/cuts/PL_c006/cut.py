"""紙芝居版 PL_c006（絵と舞台は ../../stage.py）。"""

from engine import assets

stage = assets.load("experiments/04_kamishibai/stage.py")
DURATION, draw = stage.make("PL_c006", 6.0)
