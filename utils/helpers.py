import re
from typing import List


def extract_command(msg: str, prefixes: List[str]) -> tuple:
    """提取命令和参数"""
    for prefix in prefixes:
        if msg.startswith(prefix):
            parts = msg[len(prefix):].strip().split(maxsplit=1)
            cmd = parts[0] if parts else ""
            args = parts[1] if len(parts) > 1 else ""
            return cmd, args
    return "", ""


def match_keywords(text: str, keywords: List[str]) -> bool:
    """精确匹配关键词"""
    if not keywords:
        return False
    text = text.strip()
    if text in keywords:
        return True
    # 按标点分割后匹配
    for seg in re.split(r'[，,。！？；;:：\s]+', text):
        if seg in keywords:
            return True
    return False
