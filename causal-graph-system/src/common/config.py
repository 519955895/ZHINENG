"""配置加载：统一读取 configs/*.yaml，供编排层与各模块使用。"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml


class Config:
    """轻量配置对象，支持点号访问（cfg.get("extraction.model_name")）。"""

    def __init__(self, data: Dict[str, Any], path: str = ""):
        self._data = data
        self.path = path

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """按 'a.b.c' 点号路径取值。"""
        cur: Any = self._data
        for part in dotted_key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    def section(self, name: str) -> Dict[str, Any]:
        v = self._data.get(name, {})
        return v if isinstance(v, dict) else {}

    def raw(self) -> Dict[str, Any]:
        return self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __repr__(self) -> str:  # pragma: no cover
        return f"Config(path={self.path!r})"


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Config(data, path=path)


def resolve_path(base_dir: str, p: Optional[str]) -> Optional[str]:
    """把配置里的相对路径解析为基于 base_dir 的绝对路径。"""
    if not p:
        return None
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(base_dir, p))
