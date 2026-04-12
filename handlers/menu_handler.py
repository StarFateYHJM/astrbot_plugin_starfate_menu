from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from ..core.menu_manager import MenuManager
from ..core.image_renderer import ImageRenderer


class MenuHandler:
    """菜单消息处理器"""
    
    def __init__(self, plugin, menu_manager: MenuManager, renderer: ImageRenderer):
        self.plugin = plugin
        self.menu_manager = menu_manager
        self.renderer = renderer
    
    async def handle(self, event: AstrMessageEvent):
        """处理消息，判断是否触发菜单"""
        msg = event.message_str.strip()
        config = self.plugin.context.get_config()
        
        # 获取触发命令列表
        trigger_commands = config.get("trigger_commands", ["/menu", "/菜单", "/功能", "/帮助", "/sfmenu"])
        
        # 判断消息类型
        is_private = event.is_private()
        is_group = event.is_group()
        
        # 检查是否命中触发命令
        triggered = False
        for cmd in trigger_commands:
            if msg == cmd or msg.startswith(cmd + " "):
                triggered = True
                break
        
        if not triggered:
            return
        
        # 群聊需要检查@
        if is_group:
            group_require_at = config.get("group_require_at", True)
            if group_require_at and not self._is_at_me(event):
                return
        
        # 渲染并发送菜单
        async for result in self._send_menu(event, config):
            if result:
                yield result
    
    def _is_at_me(self, event: AstrMessageEvent) -> bool:
        """检查是否@了机器人"""
        if hasattr(event, 'is_at_me') and callable(event.is_at_me):
            try:
                return event.is_at_me()
            except:
                pass
        
        bot_qq = self.plugin.context.get_config().get("bot_qq", "")
        if bot_qq:
            for segment in event.get_messages():
                if hasattr(segment, 'type') and segment.type == "At":
                    qq = getattr(segment, 'qq', None)
                    if qq and str(qq) == str(bot_qq):
                        return True
        
        return False
    
    async def _send_menu(self, event: AstrMessageEvent, config: dict):
        """渲染并发送菜单图片"""
        try:
            menu_data = self.menu_manager.get_data()
            image_path = self.renderer.render(menu_data, config)
            yield event.image_result(image_path)
        except Exception as e:
            logger.error(f"菜单渲染失败: {e}")
            yield event.plain_result(f"❌ StarFate 菜单渲染失败: {e}\n\n请检查是否已安装 Pillow 库")
