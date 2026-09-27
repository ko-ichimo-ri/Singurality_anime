"""デザイン（03_design/）やカットのスクリプトを読み込む。

フォルダ名が数字で始まるため import 文では読めないので、ファイルの場所から読み込む。
"""

import importlib.util
import sys

from .config import ROOT

_cache = {}


def load(path):
    path = (ROOT / path).resolve()
    key = str(path)
    if key not in _cache:
        name = "asset_" + "_".join(path.relative_to(ROOT).with_suffix("").parts).replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _cache[key] = module
    return _cache[key]


def character(name):
    return load(f"03_design/characters/{name}/model.py")


def prop(name):
    return load(f"03_design/props/{name}/model.py")


def location(name):
    return load(f"03_design/locations/{name}/model.py")
