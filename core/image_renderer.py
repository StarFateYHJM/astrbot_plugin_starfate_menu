import os
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageColor


class ImageRenderer:
    """图片菜单渲染器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.font_dir = Path(__file__).parent.parent / "fonts"
        self.font_dir.mkdir(exist_ok=True)
        
        # 字体路径
        self.font_path = self._find_font()
        
    def _find_font(self) -> str:
        """查找可用字体"""
        # 优先使用插件自带字体
        local_font = self.font_dir / "Sarasa-Regular.ttf"
        if local_font.exists():
            return str(local_font)
        
        # 尝试系统字体
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
        for path in font_candidates:
            if os.path.exists(path):
                return path
        
        # 回退到PIL默认字体
        return ""
    
    def render(self, menu_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        渲染菜单为图片
        返回图片路径
        """
        # 获取配置
        width = config.get("image_width", 600)
        bg_color = config.get("image_background", "#1A1A2E")
        title_color = config.get("title_color", "#E6B800")
        category_color = config.get("category_color", "#00D2FF")
        item_name_color = config.get("item_name_color", "#FFFFFF")
        command_color = config.get("command_color", "#888888")
        desc_color = config.get("description_color", "#AAAAAA")
        footer_color = config.get("footer_color", "#666666")
        
        # 计算高度
        height = self._calculate_height(menu_data)
        
        # 创建画布
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        y = 30
        
        # 加载字体
        title_font = self._get_font(24)
        category_font = self._get_font(20)
        item_font = self._get_font(16)
        small_font = self._get_font(14)
        
        # 绘制标题
        title = menu_data.get("title", "功能菜单")
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        draw.text(((width - title_width) // 2, y), title, fill=title_color, font=title_font)
        y += 50
        
        # 绘制分割线
        draw.line([(30, y), (width - 30, y)], fill="#333355", width=1)
        y += 20
        
        # 绘制分类
        for category in menu_data.get("categories", []):
            # 分类标题
            cat_name = f"{category.get('icon', '📌')} {category.get('name', '')}"
            draw.text((30, y), cat_name, fill=category_color, font=category_font)
            y += 35
            
            # 分类下的功能项
            for item in category.get("items", []):
                # 功能名称
                name = item.get("name", "")
                draw.text((50, y), f"• {name}", fill=item_name_color, font=item_font)
                
                # 命令
                cmd = item.get("command", "")
                if cmd:
                    cmd_width = draw.textbbox((0, 0), cmd, font=small_font)[2]
                    draw.text((width - 30 - cmd_width, y), cmd, fill=command_color, font=small_font)
                y += 22
                
                # 描述
                desc = item.get("description", "")
                if desc:
                    draw.text((70, y), desc, fill=desc_color, font=small_font)
                    y += 22
                
                y += 8  # 项目间距
            
            y += 10  # 分类间距
        
        # 绘制底部分割线
        draw.line([(30, y), (width - 30, y)], fill="#333355", width=1)
        y += 20
        
        # 绘制底部文字
        footer = menu_data.get("footer", "")
        if footer:
            bbox = draw.textbbox((0, 0), footer, font=small_font)
            footer_width = bbox[2] - bbox[0]
            draw.text(((width - footer_width) // 2, y), footer, fill=footer_color, font=small_font)
        
        # 保存图片
        output_dir = self.data_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "menu.png"
        img.save(str(output_path), "PNG")
        
        return str(output_path)
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取字体"""
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except:
                pass
        return ImageFont.load_default()
    
    def _calculate_height(self, menu_data: Dict[str, Any]) -> int:
        """计算图片高度"""
        height = 80  # 标题区域
        
        for category in menu_data.get("categories", []):
            height += 35  # 分类标题
            for item in category.get("items", []):
                height += 22  # 功能名称
                if item.get("description"):
                    height += 22  # 描述
                height += 8  # 间距
            height += 10  # 分类间距
        
        height += 40  # 底部区域
        
        return max(height, 400)  # 最小高度400
