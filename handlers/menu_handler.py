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
        
        # 判断消息类型：群聊时有 group_id，私聊时为空或 None
        group_id = event.get_group_id()
        is_private = not group_id
        is_group = bool(group_id)
        
        # 检查是否命中触发命令（支持带/和不带/的版本）
        triggered = False
        for cmd in trigger_commands:
            # 精确匹配、前缀匹配、去掉斜杠匹配
            if msg == cmd or msg.startswith(cmd + " ") or msg == cmd.lstrip('/'):
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
        try:
            menu_data = self.menu_manager.get_data()
            image_path = self.renderer.render(menu_data, config)
            logger.info(f"菜单图片已生成: {image_path}")
            yield event.image_result(image_path)
        except Exception as e:
            logger.error(f"菜单渲染失败: {e}")
            yield event.plain_result(f"❌ StarFate 菜单渲染失败: {e}\n\n请检查是否已安装 Pillow 库")
    
    def _is_at_me(self, event: AstrMessageEvent) -> bool:
        """检查是否@了机器人"""
        message_obj = event.message_obj
        if message_obj and hasattr(message_obj, 'message'):
            for segment in message_obj.message:
                if hasattr(segment, 'type') and segment.type == "At":
                    qq = getattr(segment, 'qq', None)
                    if qq:
                        self_id = event.get_self_id()
                        if str(qq) == str(self_id):
                            return True
        return False
