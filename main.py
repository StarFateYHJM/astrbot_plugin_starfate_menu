import json
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .handlers.menu_handler import MenuHandler
from .core.menu_manager import MenuManager
from .core.image_renderer import ImageRenderer


@register("astrbot_plugin_starfate_menu", "YHJM", "StarFate 功能菜单", "1.0.0")
class StarFateMenuPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.name = "astrbot_plugin_starfate_menu"
        self.display_name = "StarFate 功能菜单"
        
        # 获取插件数据目录（兼容字符串返回值）
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path
        data_path = get_astrbot_data_path()
        # 兼容字符串和 Path 对象两种情况
        if isinstance(data_path, str):
            data_path = Path(data_path)
        self.data_dir = data_path / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 菜单文件路径
        self.menu_file = self.data_dir / "menu_content.json"
        
        # 初始化默认菜单
        self._init_default_menu()
        
        # 初始化组件
        self.menu_manager = MenuManager(self.menu_file)
        self.renderer = ImageRenderer(self.data_dir)
        self.handler = MenuHandler(self, self.menu_manager, self.renderer)
        
        logger.info(f"{self.display_name} 插件已加载，数据目录: {self.data_dir}")

    def _init_default_menu(self):
        """初始化默认菜单文件"""
        if not self.menu_file.exists():
            default_menu = {
                "title": "🌟 StarFate 功能菜单",
                "footer": "发送对应命令即可使用功能",
                "categories": [
                    {
                        "name": "基础功能",
                        "icon": "📋",
                        "items": [
                            {"name": "协议签订", "command": "/协议", "description": "查看并签署用户协议"}
                        ]
                    },
                    {
                        "name": "娱乐功能",
                        "icon": "🎮",
                        "items": [
                            {"name": "示例功能", "command": "/example", "description": "这是一个示例功能"}
                        ]
                    }
                ]
            }
            with open(self.menu_file, "w", encoding="utf-8") as f:
                json.dump(default_menu, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建默认菜单文件: {self.menu_file}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """消息监听 - 处理菜单触发"""
        async for result in self.handler.handle(event):
            if result:
                yield result

    @filter.command("sfmenu_reload")
    async def cmd_reload(self, event: AstrMessageEvent):
        """重载菜单配置（仅管理员）"""
        if not await self._check_admin(event):
            yield event.plain_result("❌ 权限不足")
            return
        self.menu_manager.reload()
        yield event.plain_result("✅ StarFate 菜单配置已重载")

    @filter.command("sfmenu_export")
    async def cmd_export(self, event: AstrMessageEvent):
        """导出菜单配置（仅管理员）"""
        if not await self._check_admin(event):
            yield event.plain_result("❌ 权限不足")
            return
        content = self.menu_manager.export()
        yield event.plain_result(f"```json\n{content}\n```")

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        """检查管理员权限"""
        config = self.context.get_config()
        admin_list = config.get("admin_list", [])
        user_id = str(event.get_sender_id())
        return user_id in admin_list

    async def terminate(self):
        """插件卸载时调用"""
        logger.info(f"{self.display_name} 插件已卸载")
