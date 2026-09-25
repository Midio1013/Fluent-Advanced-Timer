# AdvancedTimer

一个基于 **PyQt5 + qfluentwidgets** 的现代化多路计时器，采用 Fluent Design 风格界面，支持正计时、倒计时、多卡片并行计时，以及主题模式、主题色、窗口置顶等个性化设置。

---

## ✨ 功能特性

- **正计时**：秒表式计时，毫秒级精度，环形进度显示每分钟进度。
- **倒计时**：自定义时/分/秒，环形进度实时反馈，时间到自动提示。
- **多路计时**：以卡片形式并行管理多个倒计时，支持添加、删除、清空，配置自动持久化。
- **主题系统**：
  - 主题模式：跟随系统 / 浅色 / 深色
  - 主题色：紫、蓝、青、绿、橙、红、粉，共 7 种
- **窗口置顶**：支持快捷键 `Ctrl+T` 一键切换。
- **配置持久化**：窗口大小、主题、卡片列表、上次输入等均自动保存到本地 JSON。
- **高 DPI 适配**：启用 High DPI 缩放与像素图支持，适配 4K/缩放屏幕。
- **Fluent 风格**：基于 `qfluentwidgets`，界面圆角、卡片、导航栏均符合 WinUI 3 视觉规范。

---

## 🖼️ 界面预览

| 页面 | 说明 |
| --- | --- |
| 正计时 | 环形进度 + 毫秒级时间显示，开始 / 暂停 / 重置 |
| 倒计时 | 时/分/秒输入卡片 + 环形进度 + 结束时间提示 |
| 多路计时 | 卡片流式布局，每张卡片独立控制 |
| 设置 | 主题模式、主题色、窗口置顶、配置文件路径、恢复默认 |

---

## 🚀 快速开始
### 运行

下载Release并安装

首次运行会自动在系统应用数据目录生成 `settings.json` 配置文件。

## 🗂️ 项目结构

```
AdvancedTimer/
├── main.py                 # 主程序入口
├── AdvancedTimer.ico       # 应用图标
├── README.md               # 说明文档
└── settings.json           # 运行时生成的配置文件
```

### 核心模块

| 模块 | 职责 |
| --- | --- |
| `Settings` | 配置读写与持久化 |
| `FlowLayout` | 流式布局，卡片自动换行 |
| `RingDisplay` | 环形进度 + 时间文字显示 |
| `BaseTimerPage` | 计时器基类，封装开始/暂停/重置逻辑 |
| `StopwatchPage` | 正计时页面 |
| `CountdownPage` | 倒计时页面 |
| `TimerCard` | 多路计时卡片 |
| `MultiTimerPage` | 多路计时管理页面 |
| `SettingPage` | 设置页面 |
| `MainWindow` | 主窗口，集成导航与快捷键 |

---

## ⚙️ 配置文件

配置文件默认位于系统应用数据目录：

- **Windows**：`%APPDATA%\Ticker\AdvancedTimer\settings.json`
- **Linux**：`~/.local/share/Ticker/AdvancedTimer/settings.json`
- **macOS**：`~/Library/Application Support/Ticker/AdvancedTimer/settings.json`

主要字段：

```json
{
  "window": { "w": 1200, "h": 800 },
  "always_on_top": false,
  "theme_color": "purple",
  "theme_mode": "auto",
  "cards": [
    { "title": "1 分钟", "duration_sec": 60 },
    { "title": "3 分钟", "duration_sec": 180 }
  ],
  "last_input": { "h": 0, "m": 0, "s": 30 }
}
```

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl + T` | 切换窗口置顶 |

---

## 🎨 自定义主题色

在 `main.py` 的 `THEME_COLORS` 字典中可扩展或修改主题色：

```python
THEME_COLORS = {
    "purple": "#8E8CD8", "blue": "#0078D4", "teal": "#038387",
    "green": "#107C10", "orange": "#F7630C", "red": "#E81123",
    "pink": "#E3008C",
}
```

同时更新 `COLOR_LABELS` 以在设置页中显示对应名称。

---

## 📝 开发说明

- 计时逻辑基于 `QElapsedTimer`，UI 刷新由 `QTimer` 驱动，精度与性能兼顾。
- 多路计时卡片使用自定义 `FlowLayout`，支持窗口缩放自适应换行。
- 卡片样式通过 `apply_card_style()` 动态注入，兼容浅色/深色模式。
- 配置持久化在每次修改后立即写入，避免意外丢失。

---

## 📄 许可证

本项目仅供学习与个人使用，未附带特定开源许可证。若需商用，请自行确认依赖库（PyQt5、qfluentwidgets）的许可条款。

---

## 🙏 致谢

- [PyQt5](https://pypi.org/project/PyQt5/)
- [qfluentwidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [Nuitka](https://nuitka.net/)

---

如有问题或建议，欢迎提交 Issue 或 PR。
