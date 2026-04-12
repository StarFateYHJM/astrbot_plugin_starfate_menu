"""StarFate 功能菜单插件 - 主入口"""

import json
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .handlers.menu_handler import MenuHandler
from .core.menu_manager import MenuManager


@register("astrbot_plugin_starfate_menu", "YHJM", "StarFate 功能菜单", "1.0.0")
class StarFateMenuPlugin(Star):
    """StarFate 功能菜单插件"""
    
    PAGE_NEXT = ["下一页", "next", "下页", ">"]
    PAGE_PREV = ["上一页", "prev", "上页", "<"]
    
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.name = "astrbot_plugin_starfate_menu"
        self.config = config or {}
        self.debug = self.config.get("debug_mode", False)
        
        self._init_paths()
        self._init_files()
        self._init_components()
        
        self._log(f"插件已加载，配置项: {len(self.config)}")

    def _log(self, msg: str, level: str = "info"):
        """统一日志输出"""
        if not self.debug and level == "debug":
            return
        getattr(logger, level)(f"[DEBUG] {msg}" if level == "debug" else msg)

    def _init_paths(self):
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path
        path = get_astrbot_data_path()
        self.data_dir = (Path(path) if isinstance(path, str) else path) / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _init_files(self):
        self.menu_file = self.data_dir / "menu_content.json"
        if not self.menu_file.exists():
            with open(self.menu_file, "w", encoding="utf-8") as f:
                json.dump({"title": "功能菜单", "footer": "", "categories": []}, f, ensure_ascii=False)
            logger.info("已创建默认菜单文件")

    def _init_components(self):
        self.menu_manager = MenuManager(self.menu_file)
        self.handler = MenuHandler(self)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        msg = event.message_str.strip().lower()
        
        if self.config.get("pagination_enabled", True):
            if msg in self.PAGE_NEXT:
                async for r in self._change_page(event, 1): yield r
                return event.stop_event()
            if msg in self.PAGE_PREV:
                async for r in self._change_page(event, -1): yield r
                return event.stop_event()
        
        has = False
        async for r in self.handler.handle(event):
            has = True
            yield r
        if has:
            event.stop_event()

    async def _change_page(self, event: AstrMessageEvent, delta: int):
        uid = str(event.get_sender_id())
        mid = await self.get_kv_data(f"menu_current_{uid}", "default")
        cur = await self.get_kv_data(f"menu_page_{uid}_{mid}", 0)
        new = max(0, cur + delta)
        await self.put_kv_data(f"menu_page_{uid}_{mid}", new)
        self._log(f"翻页: {cur} -> {new}", "debug")
        async for r in self.handler.handle(event, page=new, menu_id=mid):
            yield r

    @filter.command("sfmenu_reload")
    async def cmd_reload(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        await self._reload_config()
        self.menu_manager.reload()
        self._log(f"配置已重载", "debug")
        yield event.plain_result("菜单配置已重载")

    async def _reload_config(self):
        try:
            if sm := self.context.get_star_manager():
                if p := sm.get_star(self.name):
                    if p.config:
                        self.config = p.config
                        self.debug = self.config.get("debug_mode", False)
                        return
            if (cf := self.data_dir / "config.json").exists():
                self.config = json.loads(cf.read_text(encoding="utf-8"))
                self.debug = self.config.get("debug_mode", False)
        except Exception as e:
            self._log(f"刷新失败: {e}", "warning")

    @filter.command("sfmenu_list")
    async def cmd_list(self, event: AstrMessageEvent):
        if not (ms := self.config.get("menu_sets", [])):
            yield event.plain_result("暂无菜单")
            return
        lines = ["可用菜单："]
        for i, m in enumerate(ms, 1):
            name, mid = m.get("menu_name", "?"), m.get("menu_id", "?")
            default = " [默认]" if m.get("is_default") else ""
            lines.append(f"  {i}. {name} (/menu {mid}){default}")
        yield event.plain_result("\n".join(lines))

    @filter.command("sfmenu_export")
    async def cmd_export(self, event: AstrMessageEvent):
        if not await self._check_admin(event):
            yield event.plain_result("权限不足")
            return
        yield event.plain_result(f"```json\n{self.menu_manager.export()}\n```")

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        admins = self.context.get_config().get("admins_id") or []
        return str(event.get_sender_id()) in admins

    async def terminate(self):
        logger.info("插件已卸载")
