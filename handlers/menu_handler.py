import re
import json
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
        
        try:
            html = self._build_html(config, selected_menu, debug)
            
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

    def _build_html(self, config: dict, menu: dict, debug: bool) -> str:
        content = menu.get("content", "")
        content_escaped = json.dumps(content)
        
        bg_color = menu.get("background_color", "#1A1A2E")
        text_color = menu.get("text_color", "#FFFFFF")
        link_color = menu.get("link_color", "#00D2FF")
        code_bg_color = menu.get("code_bg_color", "#2D2D2D")
        code_text_color = menu.get("code_text_color", "#E6E6E6")
        border_color = menu.get("border_color", "#333355")
        css_zoom = menu.get("css_zoom", 2.0)
        padding_body = menu.get("padding_body", "40px 50px")
        
        bg_style = f"background-color: {bg_color};"
        overlay_html = ""
        bg_image = menu.get("background_image", "")
        
        if bg_image:
            bg_style += f" background-image: url('{bg_image}'); background-size: cover; background-position: center; background-repeat: no-repeat;"
            if menu.get("background_overlay", True):
                overlay_color = menu.get("overlay_color", "#000000")
                overlay_opacity = menu.get("overlay_opacity", 0.5)
                overlay_html = f'<div class="overlay" style="background-color: {overlay_color}; opacity: {overlay_opacity};"></div>'
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "SimHei", sans-serif;
                    zoom: {css_zoom};
                    background-color: transparent;
                    display: inline-block;
                }}
                .menu-container {{
                    display: block;
                    position: relative;
                    {bg_style}
                    padding: {padding_body};
                    color: {text_color};
                }}
                .overlay {{
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    pointer-events: none;
                    z-index: 1;
                }}
                .content {{
                    position: relative;
                    z-index: 2;
                }}
                .content h1 {{
                    font-size: 2.5em;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid {border_color};
                }}
                .content h2 {{
                    font-size: 2em;
                    margin-top: 30px;
                    margin-bottom: 15px;
                }}
                .content h3 {{
                    font-size: 1.5em;
                    margin-top: 25px;
                    margin-bottom: 10px;
                }}
                .content p {{
                    margin-bottom: 15px;
                    line-height: 1.6;
                }}
                .content ul, .content ol {{
                    margin-left: 25px;
                    margin-bottom: 15px;
                }}
                .content li {{
                    margin-bottom: 8px;
                    line-height: 1.6;
                }}
                .content a {{
                    color: {link_color};
                    text-decoration: none;
                }}
                .content a:hover {{
                    text-decoration: underline;
                }}
                .content code {{
                    background-color: {code_bg_color};
                    color: {code_text_color};
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: "Consolas", "Monaco", monospace;
                    font-size: 0.9em;
                }}
                .content pre {{
                    background-color: {code_bg_color};
                    padding: 15px;
                    border-radius: 8px;
                    overflow-x: auto;
                    margin-bottom: 15px;
                }}
                .content pre code {{
                    background: none;
                    padding: 0;
                    color: {code_text_color};
                }}
                .content table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .content th, .content td {{
                    border: 1px solid {border_color};
                    padding: 10px 15px;
                    text-align: left;
                }}
                .content th {{
                    background-color: rgba(255,255,255,0.1);
                    font-weight: bold;
                }}
                .content hr {{
                    border: none;
                    border-top: 2px solid {border_color};
                    margin: 30px 0;
                }}
                .content blockquote {{
                    border-left: 4px solid {border_color};
                    padding-left: 20px;
                    margin-left: 0;
                    margin-bottom: 15px;
                    opacity: 0.8;
                }}
                .content img {{
                    max-width: 100%;
                    height: auto;
                }}
                .content strong {{
                    font-weight: bold;
                }}
                .content em {{
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="menu-container">
                {overlay_html}
                <div class="content" id="content"></div>
            </div>
            <script>
                (function() {{
                    var markdown = {content_escaped};
                    document.getElementById('content').innerHTML = marked.parse(markdown);
                }})();
            </script>
        </body>
        </html>
        '''
