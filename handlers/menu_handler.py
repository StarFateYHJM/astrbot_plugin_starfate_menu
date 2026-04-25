"""菜单处理器"""

import re
import json
import hashlib
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger


class MenuHandler:
    
    def __init__(self, plugin):
        self.plugin = plugin
        self._cache = {}

    def _log(self, msg: str):
        if self.plugin.debug:
            logger.info(f"[DEBUG] {msg}")

    def _hash(self, menu: dict) -> str:
        data = json.dumps(menu, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data.encode()).hexdigest()[:8]

    async def handle(self, event: AstrMessageEvent, page: int = None, menu_id: str = None):
        raw = event.message_str.strip()
        cfg = self.plugin.config
        self._log(f"请求: {raw}")
        
        triggered, req_id = self._match(raw, cfg.get("trigger_commands", ["/menu"]))
        if not triggered and page is None:
            return
        
        if not (menus := cfg.get("menu_sets", [])):
            yield event.plain_result("暂无菜单")
            return
        
        menu = self._select(menus, req_id or menu_id)
        if not menu:
            yield event.plain_result(f"未找到菜单 '{req_id}'")
            return
        
        try:
            h = self._hash(menu)
            if h in self._cache:
                self._log(f"缓存命中: {h}")
                yield event.image_result(self._cache[h])
                return
            
            self._log(f"渲染: {h}")
            html = self._build(menu)
            url = await self.plugin.html_render(html, {"full_page": True})
            self._cache[h] = url
            logger.info("图片已生成")
            yield event.image_result(url)
        except Exception as e:
            logger.error(f"渲染失败: {e}")
            yield event.plain_result(f"渲染失败: {e}")

    def _match(self, raw: str, triggers: list) -> tuple:
        for t in triggers:
            c = t.lstrip('/')
            if re.match(rf'^(/{c}|{c})(\s|$)', raw, re.I):
                p = raw.split(maxsplit=1)
                return True, p[1].strip() if len(p) > 1 else None
        return False, None

    def _select(self, menus: list, req_id: str = None) -> dict:
        if req_id:
            for m in menus:
                if m.get("menu_id") == req_id:
                    return m
        for m in menus:
            if m.get("is_default"):
                return m
        return menus[0] if menus else None

    def _build(self, m: dict) -> str:
        bg = self.plugin.resolve_background(m.get("background_image", ""))
        overlay = f'<div class="overlay" style="background:{m.get("overlay_color","#000")};opacity:{m.get("overlay_opacity",0.5)}"></div>' if bg and m.get("background_overlay", True) else ""
        return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"Microsoft YaHei",sans-serif;zoom:{m.get("css_zoom",2)};background:{m.get("background_color","#1A1A2E")};position:relative;font-size:{m.get("base_font_size","16px")}}}
.bg-layer{{position:absolute;top:0;left:0;z-index:0}}
.bg-layer img{{display:block;width:100%;height:100%;object-fit:cover}}
.overlay{{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1}}
.menu-container{{position:relative;padding:{m.get("padding_body","40px 50px")};color:{m.get("text_color","#FFF")};z-index:2}}
.content h1{{color:{m.get("title_color","#E6B800")};font-size:{m.get("h1_font_size","2.5em")};border-bottom:2px solid {m.get("border_color","#333")};margin-bottom:20px;padding-bottom:15px}}
.content h2{{color:{m.get("h2_color","#E6B800")};font-size:{m.get("h2_font_size","2em")};margin:30px 0 15px}}
.content h3{{color:{m.get("h3_color","#E6B800")};font-size:{m.get("h3_font_size","1.5em")};margin:25px 0 10px}}
.content p{{margin-bottom:15px;line-height:1.6}}
.content ul,.content ol{{margin-left:25px;margin-bottom:15px}}
.content li{{margin-bottom:8px}}
.content a{{color:{m.get("link_color","#0DF")};text-decoration:none}}
.content code{{background:{m.get("code_bg_color","#2D2D2D")};color:{m.get("code_text_color","#E6E6E6")};padding:2px 6px;border-radius:4px}}
.content pre{{background:{m.get("code_bg_color","#2D2D2D")};padding:15px;border-radius:8px;overflow-x:auto}}
.content pre code{{background:none;padding:0}}
.content table{{width:100%;border-collapse:collapse}}
.content th,.content td{{border:1px solid {m.get("border_color","#333")};padding:10px 15px}}
.content hr{{border:none;border-top:2px solid {m.get("border_color","#333")};margin:30px 0}}
</style></head>
<body><div class="bg-layer" id="bgLayer"></div>{overlay}
<div class="menu-container"><div class="content" id="content"></div></div>
<script>
(function(){{
    document.getElementById('content').innerHTML = marked.parse({json.dumps(m.get("content",""))});
    var bg = '{bg}';
    if(bg){{
        var i = new Image();
        i.onload = function(){{
            var w = this.width, h = this.height, max = 2000;
            if(w > max || h > max){{ var s = Math.min(max/w, max/h); w = Math.round(w*s); h = Math.round(h*s); }}
            document.body.style.width = w + 'px';
            document.body.style.height = h + 'px';
            document.getElementById('bgLayer').innerHTML = '<img src="' + bg + '" style="width:' + w + 'px;height:' + h + 'px;">';
        }};
        i.src = bg;
    }}
}})();
</script></body></html>'''
