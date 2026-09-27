"""影絵。人物を真っ黒な影にし、背景の光を持ち上げて、影の形と光だけで見せる。

傘の色と、アンドロイドの光の線（首すじ・手首）だけは影に染まらない。
"""

import numpy as np

FINISH = {"grain": 3.0, "vignette": 0.5}


def char_tint(tint):
    return ("#000000", 1.0)


def post(arr, frame):
    rgb = arr[..., :3].astype(np.float32) / 255
    # 暗いところを持ち上げる（真っ黒の影はそのまま残る）
    lifted = rgb ** 0.5
    lum = lifted.mean(axis=2, keepdims=True)
    lifted = np.clip(lum + (lifted - lum) * 1.35, 0, 1)
    arr[..., :3] = (lifted * 255).astype(np.uint8)
