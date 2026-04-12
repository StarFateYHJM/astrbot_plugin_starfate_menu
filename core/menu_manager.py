import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class MenuManager:
    """菜单数据管理器"""
    
    def __init__(self, menu_file: Path):
        self.menu_file = menu_file
        self._data: Dict[str, Any] = {}
        self.reload()
    
    def reload(self):
        """重载菜单数据"""
        try:
            with open(self.menu_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception as e:
            print(f"[StarFate MenuManager] 加载菜单失败: {e}")
            self._data = self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """获取默认数据"""
        return {
            "title": "🌟 StarFate 功能菜单",
            "footer": "发送对应命令即可使用功能",
            "categories": []
        }
    
    @property
    def title(self) -> str:
        return self._data.get("title", "功能菜单")
    
    @property
    def footer(self) -> str:
        return self._data.get("footer", "")
    
    @property
    def categories(self) -> List[Dict[str, Any]]:
        return self._data.get("categories", [])
    
    def get_data(self) -> Dict[str, Any]:
        """获取完整数据"""
        return self._data.copy()
    
    def export(self) -> str:
        """导出为JSON字符串"""
        return json.dumps(self._data, ensure_ascii=False, indent=2)
