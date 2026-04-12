import copy
import math
import re
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger


class MenuHandler:
    
    def __init__(self, plugin, menu_manager):
        self.plugin = plugin
        self.menu_manager = menu_manager
    
    async def handle(self, event: AstrMessageEvent, page: int = None, menu_id: str = None):
        raw_msg = event.message_str.strip()
        config = self.plugin.config
        debug = config.get("debug_mode", False)
        user_id = str(event.get_sender_id())
        
        if debug:
            logger.info("=" * 50)
            logger.info(f"[DEBUG] 收到消息: user={user_id}, msg='{raw_msg}'")
        
        trigger_commands = config.get("trigger_commands", ["/menu", "/菜单", "/功能", "/帮助", "/sfmenu"])
        
        triggered = False
        requested_menu_id = menu_id
        
        for cmd in trigger_commands:
            cmd_clean = cmd.lstrip('/')
            pattern = rf'^(/{cmd_clean}|{cmd_clean})(\s|$)'
            match = re.match(pattern, raw_msg, re.IGNORECASE)
            if match:
                triggered = True
                if not requested_menu_id:
                    remaining = raw_msg[match.end():].strip()
                    if remaining:
                        requested_menu_id = remaining.split()[0]
                break
        
        if not triggered and page is None:
            return
        
        menu_sets = config.get("menu_sets", [])
        if not menu_sets:
            yield event.plain_result("暂无菜单配置")
            return
        
        selected_menu = None
        for menu in menu_sets:
            if requested_menu_id and menu.get("menu_id") == requested_menu_id:
                selected_menu = menu
                break
        
        if not selected_menu:
            for menu in menu_sets:
                if menu.get("is_default", False):
                    selected_menu = menu
                    break
        
        if not selected_menu:
            selected_menu = menu_sets[0]
        
        if requested_menu_id and requested_menu_id != selected_menu.get("menu_id"):
            yield event.plain_result(f"未找到菜单 '{requested_menu_id}'")
            return
        
        await self.plugin.put_kv_data(f"menu_current_{user_id}", selected_menu.get("menu_id", "default"))
        
        if page is None:
            page = await self.plugin.get_kv_data(f"menu_page_{user_id}_{selected_menu.get('menu_id')}", 0)
        
        try:
            html = self._build_html(config, selected_menu, debug, page)
            
            render_options = {
                "full_page": True
            }
            
            image_url = await self.plugin.html_render(html, {}, options=render_options)
            logger.info("菜单图片已生成")
            yield event.image_result(image_url)
            
        except Exception as e:
            logger.error(f"菜单渲染失败: {e}")
            if debug:
                import traceback
                logger.error(traceback.format_exc())
            yield event.plain_result(f"菜单渲染失败: {e}")

    def _build_html(self, config: dict, menu: dict, debug: bool, page: int) -> str:
        title = menu.get("title_text") or "功能菜单"
        footer = menu.get("footer_text") or "发送对应命令即可使用功能"
        
        raw_categories = menu.get("categories", [])
        all_categories = self._parse_categories(raw_categories, debug)
        
        pagination_enabled = menu.get("pagination_enabled", True)
        items_per_page = menu.get("items_per_page", 10)
        
        if pagination_enabled:
            categories, total_pages, _ = self._paginate_categories(all_categories, page, items_per_page)
        else:
            categories = all_categories
            total_pages = 1
        
        bg_color = menu.get("background_color", "#1A1A2E")
        title_color = menu.get("title_color", "#E6B800")
        title_size = menu.get("title_size", 56)
        category_color = menu.get("category_color", "#00D2FF")
        category_size = menu.get("category_size", 40)
        item_name_color = menu.get("item_name_color", "#FFFFFF")
        item_name_size = menu.get("item_name_size", 32)
        command_color = menu.get("command_color", "#888888")
        command_size = menu.get("command_size", 28)
        desc_color = menu.get("description_color", "#AAAAAA")
        desc_size = menu.get("description_size", 26)
        footer_color = menu.get("footer_color", "#666666")
        footer_size = menu.get("footer_size", 28)
        border_color = menu.get("border_color", "#333355")
        css_zoom = menu.get("css_zoom", 2.0)
        container_align = menu.get("container_align", "center")
        
        align_map = {
            "left": "flex-start",
            "center": "center",
            "right": "flex-end"
        }
        align_value = align_map.get(container_align, "center")
        
        bg_style = f"background-color: {bg_color};"
        overlay_html = ""
        bg_image = menu.get("background_image", "")
        
        if bg_image:
            bg_style += f" background-image: url('{bg_image}'); background-size: cover; background-position: center; background-repeat: no-repeat;"
            if menu.get("background_overlay", True):
                overlay_color = menu.get("overlay_color", "#000000")
                overlay_opacity = menu.get("overlay_opacity", 0.5)
                overlay_html = f'<div class="overlay" style="background-color: {overlay_color}; opacity: {overlay_opacity};"></div>'
        
        categories_html = ""
        for cat in categories:
            cat_name = cat.get("name", "")
            cat_icon = cat.get("icon", "📌")
            items = cat.get("items", [])
            
            if not items:
                continue
            
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
        
        page_info = ""
        if pagination_enabled and total_pages > 1:
            page_info = f'<div class="page-info">第 {page + 1}/{total_pages} 页 | 回复"下一页"或"上一页"翻页</div>'
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    border: 0;
                    box-sizing: border-box;
                }}
                html {{
                    width: max-content;
                    height: max-content;
                }}
                body {{
                    width: max-content;
                    height: max-content;
                    font-family: "Microsoft YaHei", sans-serif;
                    zoom: {css_zoom};
                    background-color: transparent;
                    {bg_style}
                    position: relative;
                }}
                .menu-container {{
                    display: inline-block;
                    position: relative;
                    padding: 40px 50px;
                }}
                .overlay {{
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    pointer-events: none;
                    z-index: 1;
                    background-color: transparent;
                }}
                .menu-title, .category, .menu-footer, .page-info {{
                    position: relative;
                    z-index: 2;
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
                .category {{ margin-bottom: 50px; }}
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
                    font-family: monospace;
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
                .page-info {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: {footer_size}px;
                    color: {footer_color};
                }}
            </style>
        </head>
        <body>
            {overlay_html}
            <div class="menu-container">
                <div class="menu-title">{title}</div>
                {categories_html}
                <div class="menu-footer">{footer}</div>
                {page_info}
            </div>
        </body>
        </html>
        '''

    def _parse_categories(self, categories: list, debug: bool) -> list:
        result = []
        for cat_str in categories:
            if not cat_str or not cat_str.strip():
                continue
            parts = cat_str.split("|")
            if len(parts) < 3:
                continue
            
            cat_name = parts[0].strip()
            cat_icon = parts[1].strip()
            func_str = parts[2].strip()
            
            items = []
            if func_str:
                for func in func_str.split(";"):
                    if not func.strip():
                        continue
                    func_items = func.split(",")
                    if len(func_items) >= 3:
                        items.append({
                            "name": func_items[0].strip(),
                            "command": func_items[1].strip(),
                            "description": func_items[2].strip()
                        })
                    elif len(func_items) == 2:
                        items.append({
                            "name": func_items[0].strip(),
                            "command": func_items[1].strip(),
                            "description": ""
                        })
            
            result.append({
                "name": cat_name,
                "icon": cat_icon,
                "items": items
            })
        
        return result

    def _paginate_categories(self, categories: list, page: int, per_page: int):
        all_items = []
        for cat in categories:
            for item in cat.get("items", []):
                all_items.append({
                    "category": cat.get("name", ""),
                    "icon": cat.get("icon", "📌"),
                    "item": item
                })
        
        total_items = len(all_items)
        total_pages = max(1, math.ceil(total_items / per_page))
        page = max(0, min(page, total_pages - 1))
        
        start = page * per_page
        page_items = all_items[start:start + per_page]
        
        paginated_categories = []
        cat_map = {}
        
        for item_data in page_items:
            cat_name = item_data["category"]
            if cat_name not in cat_map:
                cat_map[cat_name] = {
                    "name": cat_name,
                    "icon": item_data["icon"],
                    "items": []
                }
                paginated_categories.append(cat_map[cat_name])
            cat_map[cat_name]["items"].append(item_data["item"])
        
        return paginated_categories, total_pages, total_items
