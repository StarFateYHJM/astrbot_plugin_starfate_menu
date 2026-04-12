def _build_html(self, config: dict, menu: dict, debug: bool, page: int) -> str:
    # ... 前面的解析代码不变 ...

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            /* 彻底重置所有元素的边距、填充、边框 */
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
                /* 背景直接设置在 body 上，确保无缝隙 */
                {bg_style}
                position: relative;
            }}
            .menu-container {{
                display: inline-block;
                position: relative;
                /* 容器不再设置背景，背景由 body 负责 */
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
            /* 以下为各元素的样式，保持不变 */
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
        <!-- 遮罩层直接放在 body 下，确保覆盖整个背景 -->
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
