"""紙芝居版 PL_c001（絵と舞台は ../../stage.py）。"""

from engine import assets

stage = assets.load("experiments/04_kamishibai/stage.py")
DURATION, draw = stage.make("PL_c001", 5.0)
