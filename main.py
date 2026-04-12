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
            logger.info(f"=== StarFate 插件初始化 ===")
            logger.info(f"数据目录: {self.data_dir}")
            logger.info(f"配置项数量: {len(self.config)}")
            logger.info(f"debug_mode: {self.debug}")
        
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
        if self.debug:
            logger.info(f"=== 收到 sfmenu_reload 命令 ===")
            logger.info(f"发送者: {event.get_sender_id()}")
        
        if not await self._check_admin(event):
            if self.debug:
                logger.warning("权限检查失败，拒绝执行")
            yield event.plain_result("权限不足")
            return
        
        self.menu_manager.reload()
        if self.debug:
            logger.info("菜单配置已重载")
        yield event.plain_result("StarFate 菜单配置已重载")

    @filter.command("sfmenu_export")
    async def cmd_export(self, event: AstrMessageEvent):
        if self.debug:
            logger.info(f"=== 收到 sfmenu_export 命令 ===")
        
        if not await self._check_admin(event):
            if self.debug:
                logger.warning("权限检查失败，拒绝执行")
            yield event.plain_result("权限不足")
            return
        
        content = self.menu_manager.export()
        yield event.plain_result(f"```json\n{content}\n```")

    @filter.command("sfmenu_scan")
    async def cmd_scan(self, event: AstrMessageEvent):
        if self.debug:
            logger.info(f"=== 收到 sfmenu_scan 命令 ===")
        
        if not await self._check_admin(event):
            if self.debug:
                logger.warning("权限检查失败，拒绝执行")
            yield event.plain_result("权限不足")
            return
        
        if self.debug:
            logger.info("开始扫描插件注册功能...")
        
        registered = self._collect_registered_functions()
        
        if self.debug:
            logger.info(f"扫描完成，共发现 {len(registered)} 个注册功能")
        
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
            if self.debug:
                logger.info(f"获取到 {len(plugins)} 个已加载插件")
        except Exception as e:
            logger.warning(f"无法获取插件列表: {e}")
            return registered
        
        for plugin in plugins:
            try:
                config = plugin.config or {}
                menu_reg = config.get("starfate_menu_register", {})
                
                if menu_reg.get("enabled", False):
                    func_info = {
                        "category": menu_reg.get("category", "其他功能"),
                        "name": menu_reg.get("display_name") or plugin.display_name or plugin.name,
                        "command": menu_reg.get("command", ""),
                        "description": menu_reg.get("description", ""),
                        "icon": menu_reg.get("icon", "🔧")
                    }
                    registered.append(func_info)
                    
                    if self.debug:
                        logger.info(f"  发现注册: {plugin.name} -> {func_info['name']}")
            except Exception as e:
                if self.debug:
                    logger.debug(f"  扫描插件 {plugin.name} 失败: {e}")
                continue
        
        logger.info(f"共扫描到 {len(registered)} 个注册功能")
        return registered

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        """检查管理员权限"""
        global_config = self.context.get_config()
        
        if self.debug:
            logger.info(f"=== 权限检查 ===")
            logger.info(f"全局配置键: {list(global_config.keys())}")
        
        # 尝试多个可能的字段名
        admin_list = (
            global_config.get("admins_id") or 
            global_config.get("admin_list") or 
            global_config.get("admins") or 
            []
        )
        
        user_id = str(event.get_sender_id())
        
        if self.debug:
            logger.info(f"用户ID: {user_id}")
            logger.info(f"管理员列表: {admin_list}")
            logger.info(f"使用的字段: {self._get_admin_field_name(global_config)}")
            logger.info(f"检查结果: {user_id in admin_list}")
        
        return user_id in admin_list
    
    def _get_admin_field_name(self, global_config: dict) -> str:
        """获取实际使用的管理员字段名"""
        if "admins_id" in global_config:
            return "admins_id"
        elif "admin_list" in global_config:
            return "admin_list"
        elif "admins" in global_config:
            return "admins"
        else:
            return "未找到"

    async def terminate(self):
        if self.debug:
            logger.info(f"{self.display_name} 插件正在卸载")
        logger.info(f"{self.display_name} 插件已卸载")
