import json
from pathlib import Path
from typing import Dict, List, Any
from astrbot.api import logger


class MenuManager:
    
    def __init__(self, menu_file: Path):
        self.menu_file = menu_file
        self._data: Dict[str, Any] = {}
        self.reload()
    
    def reload(self):
        try:
            with open(self.menu_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"菜单配置已加载: {self.menu_file}")
        except Exception as e:
            logger.error(f"加载菜单失败: {e}")
            self._data = self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        return {
            "title": "StarFate 功能菜单",
            "footer": "发送对应命令即可使用功能",
            "categories": []
        }
    
    def get_data(self) -> Dict[str, Any]:
        return self._data.copy()
    
    def export(self) -> str:
        return json.dumps(self._data, ensure_ascii=False, indent=2)
