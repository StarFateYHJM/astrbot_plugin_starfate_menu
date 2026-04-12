# StarFate 功能菜单

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.0.0-blue)](https://astrbot.app)

一个为 AstrBot 设计的 Markdown 图片化菜单插件，支持多菜单、背景图、遮罩、缓存渲染。

---

## 效果预览

![菜单效果图](https://img.cdn1.vip/i/69db9cb4902c4_1776000180.webp)

---

## 特性

- Markdown 自由排版 - 使用 Markdown 语法编写菜单内容
- 多菜单支持 - 可创建多套独立菜单，通过 /menu <id> 切换
- 背景图片 - 支持 URL 背景图，可叠加半透明遮罩
- 缓存渲染 - 配置未变时不重复渲染
- 完全可配置 - 颜色、字号、缩放等全部可在 WebUI 配置
- 热重载 - /sfmenu_reload 刷新配置
- 调试模式 - 开启后输出详细日志

---

## 安装

### 方法一：Git 克隆

cd /path/to/AstrBot/data/plugins/
git clone https://github.com/YHJM/astrbot_plugin_starfate_menu.git

### 方法二：WebUI 上传

1. 下载插件压缩包
2. 在 AstrBot WebUI 中进入「插件管理」
3. 点击「上传插件」，选择压缩包上传

---

## 命令

| 命令 | 权限 | 说明 |
|------|------|------|
| /menu | 所有人 | 显示默认菜单 |
| /menu <id> | 所有人 | 显示指定菜单 |
| /sfmenu_list | 所有人 | 列出所有菜单 |
| /sfmenu_reload | 管理员 | 重载配置 |
| /sfmenu_export | 管理员 | 导出配置 |

---

## 配置示例

### Markdown 内容

# 功能菜单

## 基础功能

- **协议签订** `/协议` - 查看并签署用户协议
- **签到** `/sign` - 每日签到领积分

## 娱乐功能

| 功能 | 命令 | 描述 |
|------|------|------|
| 抽签 | `/draw` | 随机抽取运势签 |
| 猜数字 | `/guess` | 猜数字小游戏 |

---
*发送对应命令即可使用功能*

### 样式配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| background_color | #1A1A2E | 背景色 |
| text_color | #FFFFFF | 文字色 |
| css_zoom | 2.0 | 缩放倍数 |
| padding_body | 40px 50px | 内边距 |

---

## 作者

YHJM

---

## 许可证

MIT
