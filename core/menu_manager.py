"""菜单文件管理器"""

import json
from pathlib import Path
from astrbot.api import logger


class MenuManager:
    
    def __init__(self, path: Path):
        self.path = path
        self.data = {}
        self.reload()

    def reload(self):
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            logger.info("菜单文件已加载")
        except Exception as e:
            logger.error(f"加载失败: {e}")
            self.data = {"title": "功能菜单", "footer": "", "categories": []}

    def get_data(self) -> dict:
        return self.data.copy()

    def export(self) -> str:
        return json.dumps(self.data, ensure_ascii=False, indent=2)
