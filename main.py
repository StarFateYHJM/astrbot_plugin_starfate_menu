import json
import os
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
        self.debug = self.config.get("debug_mode", False)
        
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
        
        if self.debug:
            logger.info(f"数据目录: {self.data_dir}")
        
        logger.info(f"{self.display_name} 插件已加载")

    def _init_default_menu(self):
        if not self.menu_file.exists():
            default_menu = {
                "title": "功能菜单",
                "footer": "发送对应命令即可使用功能",
                "categories": []
            }
            with open(self.menu_file, "w", encoding="utf-8") as f:
                json.dump(default_menu, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建默认菜单文件: {self.menu_file}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        msg = event.message_str.strip().lower()
        user_id = str(event.get_sender_id())
        
        if self.config.get("pagination_enabled", True):
            page_keywords_next = ["下一页", "next", "下页", ">"]
            page_keywords_prev = ["上一页", "prev", "上页", "<"]
            
            if msg in page_keywords_next:
                async for result in self._change_page(event, 1):
                    if result:
                        yield result
                event.stop_event()
                return
            elif msg in page_keywords_prev:
                async for result in self._change_page(event, -1):
                    if result:
                        yield result
                event.stop_event()
                return
        
        has_result = False
        async for result in self.handler.handle(event):
            if result:
                has_result = True
                yield result
        
        if has_result:
            event.stop_event()

    async def _change_page(self, event: AstrMessageEvent, delta: int):
        user_id = str(event.get_sender_id())
        menu_id = await self.get_kv_data(f"menu_current_{user_id}", "default")
        current_page = await self.get_kv_data(f"menu_page_{user_id}_{menu_id}", 0)
        new_page = max(0, current_page + delta)
        await self.put_kv_data(f"menu_page_{user_id}_{menu_id}", new_page)
        
        if self.debug:
            logger.info(f"用户 {user_id} 翻页: {current_page} -> {new_page}")
        
        async for result in self.handler.handle(event, page=new_page, menu_id=menu_id):
            yield result

    @filter.command("sfmenu_reload")
    async def cmd_reload(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        
        await self._reload_config()
        self.menu_manager.reload()
        
        if self.debug:
            logger.info(f"配置已重载，menu_sets 数量: {len(self.config.get('menu_sets', []))}")
        
        yield event.plain_result("菜单配置已重载")

    async def _reload_config(self):
        try:
            star_manager = self.context.get_star_manager()
            if star_manager:
                plugin = star_manager.get_star(self.name)
                if plugin and plugin.config:
                    self.config = plugin.config
                    self.debug = self.config.get("debug_mode", False)
                    return
            
            config_file = self.data_dir / "config.json"
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    self.debug = self.config.get("debug_mode", False)
                    return
        except Exception as e:
            logger.warning(f"刷新配置失败: {e}")

    @filter.command("sfmenu_export")
    async def cmd_export(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        content = self.menu_manager.export()
        yield event.plain_result(f"```json\n{content}\n```")

    @filter.command("sfmenu_list")
    async def cmd_list(self, event: AstrMessageEvent):
        menu_sets = self.config.get("menu_sets", [])
        if not menu_sets:
            yield event.plain_result("暂无菜单配置")
            return
        
        lines = ["可用菜单："]
        for i, menu in enumerate(menu_sets, 1):
            name = menu.get("menu_name", "未命名")
            mid = menu.get("menu_id", "unknown")
            default = " [默认]" if menu.get("is_default", False) else ""
            lines.append(f"  {i}. {name} (/menu {mid}){default}")
        
        yield event.plain_result("\n".join(lines))

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        global_config = self.context.get_config()
        admin_list = (
            global_config.get("admins_id") or 
            global_config.get("admin_list") or 
            global_config.get("admins") or 
            []
        )
        user_id = str(event.get_sender_id())
        return user_id in admin_list

    async def terminate(self):
        logger.info(f"{self.display_name} 插件已卸载")
