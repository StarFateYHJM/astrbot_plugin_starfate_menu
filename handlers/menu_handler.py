import copy
import json
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger


class MenuHandler:
    
    def __init__(self, plugin, menu_manager):
        self.plugin = plugin
        self.menu_manager = menu_manager
    
    async def handle(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        config = self.plugin.config
        
        trigger_commands = config.get("trigger_commands", ["/menu", "/菜单", "/功能", "/帮助", "/sfmenu"])
        
        group_id = event.get_group_id()
        is_group = bool(group_id)
        
        triggered = False
        for cmd in trigger_commands:
            if msg == cmd or msg.startswith(cmd + " ") or msg == cmd.lstrip('/'):
                triggered = True
                break
        
        if not triggered:
            return
        
        if is_group:
            group_require_at = config.get("group_require_at", True)
            if group_require_at and not self._is_at_me(event):
                return
        
        try:
            html = self._build_html(config)
            
            render_options = {
                "width": config.get("viewport_width", 300),
                "full_page": True
            }
            
            image_url = await self.plugin.html_render(html, {}, options=render_options)
            logger.info("菜单图片已生成")
            yield event.image_result(image_url)
            
        except Exception as e:
            logger.error(f"菜单渲染失败: {e}")
            yield event.plain_result(f"菜单渲染失败: {e}")
    
    def _build_html(self, config: dict) -> str:
        title = config.get("title_text") or "StarFate 功能菜单"
        footer = config.get("footer_text") or "发送对应命令即可使用功能"
        
        categories = config.get("menu_categories", [])
        categories = self._normalize_categories(categories)
        
        bg_color = config.get("background_color", "#1A1A2E")
        title_color = config.get("title_color", "#E6B800")
        title_size = config.get("title_size", 56)
        category_color = config.get("category_color", "#00D2FF")
        category_size = config.get("category_size", 40)
        item_name_color = config.get("item_name_color", "#FFFFFF")
        item_name_size = config.get("item_name_size", 32)
        command_color = config.get("command_color", "#888888")
        command_size = config.get("command_size", 28)
        desc_color = config.get("description_color", "#AAAAAA")
        desc_size = config.get("description_size", 26)
        footer_color = config.get("footer_color", "#666666")
        footer_size = config.get("footer_size", 28)
        border_color = config.get("border_color", "#333355")
        padding_body = config.get("padding_body", "60px 80px")
        css_zoom = config.get("css_zoom", 2.0)
        
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
                    padding: {padding_body};
                    min-height: 100vh;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    zoom: {css_zoom};
                }}
                .menu-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .menu-title {{
                    font-size: {title_size}px;
                    font-weight: bold;
                    color: {title_color};
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 30px;
                    border-bottom: 2px solid {border_color};
                }}
                .category {{
                    margin-bottom: 50px;
                }}
                .category-title {{
                    font-size: {category_size}px;
                    font-weight: bold;
                    color: {category_color};
                    margin-bottom: 30px;
                }}
                .menu-item {{
                    margin-bottom: 24px;
                    padding-left: 40px;
                }}
                .item-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    margin-bottom: 8px;
                }}
                .item-name {{
                    font-size: {item_name_size}px;
                    color: {item_name_color};
                    font-weight: 500;
                }}
                .item-command {{
                    font-size: {command_size}px;
                    color: {command_color};
                    font-family: "Consolas", "Monaco", monospace;
                }}
                .item-desc {{
                    font-size: {desc_size}px;
                    color: {desc_color};
                    padding-left: 30px;
                }}
                .menu-footer {{
                    margin-top: 60px;
                    padding-top: 30px;
                    border-top: 2px solid {border_color};
                    text-align: center;
                    font-size: {footer_size}px;
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
    
    def _normalize_categories(self, categories: list) -> list:
        """将 WebUI 配置格式转换为内部格式"""
        result = []
        for cat in categories:
            function_items = cat.get("function_items", "[]")
            if isinstance(function_items, str):
                try:
                    items = json.loads(function_items)
                except:
                    items = []
            else:
                items = function_items
            
            result.append({
                "name": cat.get("category_name", ""),
                "icon": cat.get("category_icon", "📌"),
                "items": items
            })
        return result
    
    def _is_at_me(self, event: AstrMessageEvent) -> bool:
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
