import json
import os
from pathlib import Path
from astrbot.api.plugin import Plugin, AstrMessageEvent, CommandResult
from astrbot.api.filter import filter, EventMessageType
from astrbot.api.message import MessageChain, Plain, Image
from .handlers.menu_handler import MenuHandler
from .core.menu_manager import MenuManager
from .core.image_renderer import ImageRenderer


class StarFateMenuPlugin(Plugin):
    def __init__(self, context):
        super().__init__(context)
        self.name = "astrbot_plugin_starfate_menu"
        self.display_name = "StarFate 功能菜单"
        
        # 数据目录
        self.data_dir = Path(context.get_data_dir()) / "plugins" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 菜单文件路径
        self.menu_file = self.data_dir / "menu_content.json"
        
        # 初始化默认菜单
        self._init_default_menu()
        
        # 初始化组件
        self.menu_manager = MenuManager(self.menu_file)
        self.renderer = ImageRenderer(self.data_dir)
        self.handler = MenuHandler(self, self.menu_manager, self.renderer)

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

    @filter.event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """消息监听"""
        result = await self.handler.handle(event)
        if result:
            yield result

    async def on_command(self, event: AstrMessageEvent, command: str):
        """命令处理"""
        # 管理命令
        if command == "sfmenu_reload":
            if not await self._check_admin(event):
                yield CommandResult().message("❌ 权限不足")
                return
            self.menu_manager.reload()
            yield CommandResult().message("✅ StarFate 菜单配置已重载")
            
        elif command == "sfmenu_export":
            if not await self._check_admin(event):
                yield CommandResult().message("❌ 权限不足")
                return
            content = self.menu_manager.export()
            yield CommandResult().message(f"```json\n{content}\n```")

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        """检查管理员权限"""
        config = self.context.get_config()
        admin_list = config.get("admin_list", [])
        user_id = str(event.get_sender_id())
        return user_id in admin_list
