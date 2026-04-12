import json
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .handlers.menu_handler import MenuHandler
from .core.menu_manager import MenuManager


@register("astrbot_plugin_starfate_menu", "TF-MYMSI", "StarFate 功能菜单", "1.0.0")
class StarFateMenuPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.name = "astrbot_plugin_starfate_menu"
        self.display_name = "StarFate 功能菜单"
        self.config = config or {}
        
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path
        data_path = get_astrbot_data_path()
        if isinstance(data_path, str):
            data_path = Path(data_path)
        self.data_dir = data_path / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.menu_file = self.data_dir / "menu_content.json"
        self._init_default_menu()
        
        self.menu_manager = MenuManager(self.menu_file)
        self.handler = MenuHandler(self, self.menu_manager)
        
        logger.info(f"{self.display_name} 插件已加载")

    def _init_default_menu(self):
        if not self.menu_file.exists():
            default_menu = {
                "title": "StarFate 功能菜单",
                "footer": "发送对应命令即可使用功能",
                "categories": [
                    {
                        "name": "基础功能",
                        "icon": "📋",
                        "items": [
                            {"name": "协议签订", "command": "/协议", "description": "查看并签署用户协议"}
                        ]
                    }
                ]
            }
            with open(self.menu_file, "w", encoding="utf-8") as f:
                json.dump(default_menu, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建默认菜单文件: {self.menu_file}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        has_result = False
        async for result in self.handler.handle(event):
            if result:
                has_result = True
                yield result
        
        if has_result:
            event.stop_event()

    @filter.command("sfmenu_reload")
    async def cmd_reload(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        self.menu_manager.reload()
        yield event.plain_result("StarFate 菜单配置已重载")

    @filter.command("sfmenu_export")
    async def cmd_export(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        content = self.menu_manager.export()
        yield event.plain_result(f"```json\n{content}\n```")

    @filter.command("sfmenu_scan")
    async def cmd_scan(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        registered = self._collect_registered_functions()
        if registered:
            lines = ["已扫描到以下注册功能："]
            for func in registered:
                lines.append(f"  {func['icon']} {func['name']} - {func['command']} ({func['category']})")
            yield event.plain_result("\n".join(lines))
        else:
            yield event.plain_result("未扫描到任何注册功能")

    def _collect_registered_functions(self):
        registered = []
        
        try:
            star_manager = self.context.get_star_manager()
            plugins = star_manager.get_all_stars()
        except:
            logger.warning("无法获取插件列表")
            return registered
        
        for plugin in plugins:
            try:
                config = plugin.config or {}
                menu_reg = config.get("starfate_menu_register", {})
                
                if menu_reg.get("enabled", False):
                    registered.append({
                        "category": menu_reg.get("category", "其他功能"),
                        "name": menu_reg.get("display_name") or plugin.display_name or plugin.name,
                        "command": menu_reg.get("command", ""),
                        "description": menu_reg.get("description", ""),
                        "icon": menu_reg.get("icon", "🔧")
                    })
            except:
                continue
        
        logger.info(f"共扫描到 {len(registered)} 个注册功能")
        return registered

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        global_config = self.context.get_config()
        admin_list = global_config.get("admin_id", [])
        user_id = str(event.get_sender_id())
        return user_id in admin_list

    async def terminate(self):
        logger.info(f"{self.display_name} 插件已卸载")
