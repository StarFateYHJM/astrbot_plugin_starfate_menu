from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger


class MenuHandler:
    """菜单消息处理器"""
    
    def __init__(self, plugin, menu_manager):
        self.plugin = plugin
        self.menu_manager = menu_manager
    
    async def handle(self, event: AstrMessageEvent):
        """处理消息，判断是否触发菜单"""
        msg = event.message_str.strip()
        config = self.plugin.context.get_config()
        
        # 获取触发命令列表
        trigger_commands = config.get("trigger_commands", ["/menu", "/菜单", "/功能", "/帮助", "/sfmenu"])
        
        # 判断消息类型
        group_id = event.get_group_id()
        is_private = not group_id
        is_group = bool(group_id)
        
        # 检查是否命中触发命令（支持带/和不带/的版本）
        triggered = False
        for cmd in trigger_commands:
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
            html = self._build_html(menu_data, config)
            
            render_options = {
                "width": 600,
                "full_page": True,
                "scale": "device"
                "device_scale_factor": 2.0
            }
            
            image_url = await self.plugin.html_render(html, {}, options=render_options)
            logger.info("菜单图片已生成（高清模式）")
            yield event.image_result(image_url)
            
        except Exception as e:
            logger.error(f"菜单渲染失败: {e}")
            yield event.plain_result(f"❌ StarFate 菜单渲染失败: {e}")
    
    def _build_html(self, menu_data: dict, config: dict) -> str:
        """构建 HTML 模板"""
        title = menu_data.get("title", "🌟 StarFate 功能菜单")
        footer = menu_data.get("footer", "发送对应命令即可使用功能")
        categories = menu_data.get("categories", [])
        
        # 获取配色
        bg_color = config.get("image_background", "#1A1A2E")
        title_color = config.get("title_color", "#E6B800")
        category_color = config.get("category_color", "#00D2FF")
        item_name_color = config.get("item_name_color", "#FFFFFF")
        command_color = config.get("command_color", "#888888")
        desc_color = config.get("description_color", "#AAAAAA")
        footer_color = config.get("footer_color", "#666666")
        
        # 构建分类 HTML
        categories_html = ""
        for cat in categories:
            cat_name = cat.get("name", "")
            cat_icon = cat.get("icon", "📌")
            items = cat.get("items", [])
            
            items_html = ""
            for item in items:
                name = item.get("name", "")
                command = item.get("command", "")
                desc = item.get("description", "")
                
                items_html += f'''
                <div class="menu-item">
                    <div class="item-row">
                        <span class="item-name">• {name}</span>
                        <span class="item-command">{command}</span>
                    </div>
                    <div class="item-desc">{desc}</div>
                </div>
                '''
            
            categories_html += f'''
            <div class="category">
                <div class="category-title">{cat_icon} {cat_name}</div>
                {items_html}
            </div>
            '''
        
        # 完整 HTML
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "SimHei", sans-serif;
                    background-color: {bg_color};
                    padding: 30px 40px;
                    min-height: 100vh;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                }}
                .menu-container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .menu-title {{
                    font-size: 28px;
                    font-weight: bold;
                    color: {title_color};
                    text-align: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #333355;
                }}
                .category {{
                    margin-bottom: 25px;
                }}
                .category-title {{
                    font-size: 20px;
                    font-weight: bold;
                    color: {category_color};
                    margin-bottom: 15px;
                }}
                .menu-item {{
                    margin-bottom: 12px;
                    padding-left: 20px;
                }}
                .item-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    margin-bottom: 4px;
                }}
                .item-name {{
                    font-size: 16px;
                    color: {item_name_color};
                    font-weight: 500;
                }}
                .item-command {{
                    font-size: 14px;
                    color: {command_color};
                    font-family: "Consolas", "Monaco", monospace;
                }}
                .item-desc {{
                    font-size: 13px;
                    color: {desc_color};
                    padding-left: 15px;
                }}
                .menu-footer {{
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #333355;
                    text-align: center;
                    font-size: 14px;
                    color: {footer_color};
                }}
            </style>
        </head>
        <body>
            <div class="menu-container">
                <div class="menu-title">{title}</div>
                {categories_html}
                <div class="menu-footer">{footer}</div>
            </div>
        </body>
        </html>
        '''
    
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
