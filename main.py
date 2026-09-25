# main.py
import sys
import os
import json
import subprocess

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

from datetime import datetime, timedelta

from PyQt5.QtCore import (
    Qt, QTimer, QElapsedTimer, QSize, QRect, QPoint, QStandardPaths
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLayout, QLabel, QSizePolicy
)
from PyQt5.QtGui import QFont, QKeySequence, QIcon
from PyQt5.QtWidgets import QShortcut

from qfluentwidgets import (
    FluentWindow, ToolButton, TransparentToolButton, PushButton,
    PrimaryPushButton, ProgressRing, CardWidget, BodyLabel,
    CaptionLabel, SpinBox, SwitchButton, ComboBox, StrongBodyLabel,
    setTheme, Theme, FluentIcon as FIF,
    setThemeColor, isDarkTheme,
    NavigationItemPosition,
)


# ============================================================
# 资源路径处理（兼容 Nuitka 打包）
# ============================================================
def resource_path(relative_path: str) -> str:
    """获取资源的绝对路径，兼容开发环境与 Nuitka 打包后"""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 兼容
        base = sys._MEIPASS
    elif getattr(sys, "frozen", False):
        # Nuitka 打包后
        base = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


ICON_PATH = resource_path("AdvancedTimer.ico")


# ============================================================
# 主题色表
# ============================================================
THEME_COLORS = {
    "purple": "#8E8CD8", "blue": "#0078D4", "teal": "#038387",
    "green": "#107C10", "orange": "#F7630C", "red": "#E81123",
    "pink": "#E3008C",
}

COLOR_LABELS = [
    ("紫色", "purple"), ("蓝色", "blue"), ("青色", "teal"),
    ("绿色", "green"), ("橙色", "orange"), ("红色", "red"),
    ("粉色", "pink"),
]

THEME_LABELS = [
    ("跟随系统", "auto"), ("浅色", "light"), ("深色", "dark"),
]

_card_style_counter = 0


def apply_card_style(widget):
    global _card_style_counter
    _card_style_counter += 1
    tag = f"customCard{_card_style_counter}"
    widget.setObjectName(tag)
    widget.setAttribute(Qt.WA_StyledBackground, True)

    if isDarkTheme():
        widget.setStyleSheet(f"""
            #{tag} {{
                background-color: #2B2B2E;
                border: 1px solid #3A3A3D;
                border-radius: 8px;
            }}
        """)
    else:
        widget.setStyleSheet(f"""
            #{tag} {{
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }}
        """)
    widget.update()


# ============================================================
# 配置持久化
# ============================================================
class Settings:
    def __init__(self):
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not base:
            base = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.dir = base
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "settings.json")
        self.data = self._load()

    def _load(self):
        default = {
            "window": {"w": 1200, "h": 800},
            "always_on_top": False,
            "theme_color": "purple",
            "theme_mode": "auto",
            "cards": [
                {"title": "1 分钟", "duration_sec": 60},
                {"title": "3 分钟", "duration_sec": 180},
                {"title": "5 分钟", "duration_sec": 300},
                {"title": "10 分钟", "duration_sec": 600},
            ],
            "last_input": {"h": 0, "m": 0, "s": 30},
        }
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in default.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except Exception as e:
            print(f"[Settings] load failed: {e}")
        return default

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Settings] save failed: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


# ============================================================
# FlowLayout
# ============================================================
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, h_spacing=16, v_spacing=16):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item): self._items.append(item)
    def count(self): return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self): return True
    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self): return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x(); y = rect.y(); line_height = 0
        for item in self._items:
            widget = item.widget()
            if widget is None: continue
            hint = widget.sizeHint()
            w = hint.width(); h = hint.height()
            if x + w > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + self._v_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), QSize(w, h)))
            x = x + w + self._h_spacing
            line_height = max(line_height, h)
        return y + line_height - rect.y()


# ============================================================
# RingDisplay
# ============================================================
class RingDisplay(QWidget):
    def __init__(self, size: int, time_font_px: int = 28,
                 show_end_label: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet("background: transparent;")

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        self.ring = ProgressRing(self)
        self.ring.setFixedSize(size, size)
        self.ring.setTextVisible(False)
        self.ring.setValue(0)
        grid.addWidget(self.ring, 0, 0, Qt.AlignCenter)

        overlay = QWidget(self)
        overlay.setFixedSize(size, size)
        overlay.setStyleSheet("background: transparent;")
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        v = QVBoxLayout(overlay)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addStretch()

        self.timeLabel = QLabel("00:00.000", overlay)
        self.timeLabel.setAlignment(Qt.AlignCenter)
        self.timeLabel.setStyleSheet(
            "font-family: 'Segoe UI', 'Microsoft YaHei', Consolas, monospace;"
            f"font-size: {time_font_px}px; font-weight: 600;"
            "background: transparent; color: #202020;")
        v.addWidget(self.timeLabel)

        self.endTimeLabel = None
        if show_end_label:
            self.endTimeLabel = QLabel("", overlay)
            self.endTimeLabel.setAlignment(Qt.AlignCenter)
            self.endTimeLabel.setStyleSheet(
                "background: rgba(128,128,128,0.18); border-radius: 10px;"
                "padding: 2px 8px; font-size: 12px; color: #505050;")
            self.endTimeLabel.setFixedHeight(22)
            v.addWidget(self.endTimeLabel, 0, Qt.AlignHCenter)

        v.addStretch()
        grid.addWidget(overlay, 0, 0, Qt.AlignCenter)
        overlay.raise_()

    def setProgress(self, value: int): self.ring.setValue(value)
    def setTimeText(self, text: str): self.timeLabel.setText(text)
    def setEndTimeText(self, text: str, visible: bool):
        if self.endTimeLabel is None: return
        self.endTimeLabel.setText(text)
        self.endTimeLabel.setVisible(visible)


# ============================================================
# 单计时器基类
# ============================================================
class BaseTimerPage(QWidget):
    def __init__(self, object_name: str):
        super().__init__()
        self.setObjectName(object_name)
        self.isRunning = False
        self.elapsedBeforePause = 0
        self.stopwatch = QElapsedTimer()
        self.uiTimer = QTimer(self)
        self.uiTimer.setInterval(16)
        self.uiTimer.timeout.connect(self.onTick)

    def getDisplayTime(self) -> int: raise NotImplementedError
    def getProgress(self) -> int: raise NotImplementedError
    def canStart(self) -> bool: return True
    def onStarted(self): pass
    def onReset(self): pass
    def onFinished(self): pass

    def elapsedTotalMs(self) -> int:
        return self.elapsedBeforePause + (
            self.stopwatch.elapsed() if self.stopwatch.isValid() else 0)

    def start(self):
        if self.isRunning: return
        if not self.canStart(): return
        self.stopwatch.start()
        self.uiTimer.start()
        self.isRunning = True
        self.btnStart.setText("暂停")
        self.statusLabel.setText("计时中…")
        self.onStarted()

    def pause(self):
        if not self.isRunning: return
        self.elapsedBeforePause = self.elapsedTotalMs()
        self.stopwatch.invalidate()
        self.uiTimer.stop()
        self.isRunning = False
        self.btnStart.setText("继续")
        self.statusLabel.setText("已暂停")

    def reset(self):
        self.uiTimer.stop()
        self.stopwatch.invalidate()
        self.isRunning = False
        self.elapsedBeforePause = 0
        self.btnStart.setText("开始")
        self.statusLabel.setText("准备就绪")
        self.ringDisplay.setProgress(0)
        self.onReset()
        self.ringDisplay.setTimeText(self.formatTime(self.getDisplayTime()))

    def toggleStartPause(self):
        if self.isRunning: self.pause()
        else: self.start()

    def onTick(self):
        self.ringDisplay.setTimeText(self.formatTime(self.getDisplayTime()))
        self.ringDisplay.setProgress(self.getProgress())

    @staticmethod
    def formatTime(ms: int) -> str:
        ms = max(0, int(ms))
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        milli = ms % 1000
        if h > 0: return f"{h:02d}:{m:02d}:{s:02d}.{milli:03d}"
        return f"{m:02d}:{s:02d}.{milli:03d}"

    def buildCommonUi(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addSpacing(20)

        ringRow = QHBoxLayout()
        ringRow.addStretch()
        self.ringDisplay = RingDisplay(size=260, time_font_px=28)
        ringRow.addWidget(self.ringDisplay)
        ringRow.addStretch()
        layout.addLayout(ringRow)

        self.statusLabel = CaptionLabel("准备就绪")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statusLabel)

        self.customArea = QVBoxLayout()
        layout.addLayout(self.customArea)
        layout.addStretch()

        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        self.btnStart = PrimaryPushButton("开始")
        self.btnStart.setMinimumWidth(110)
        self.btnStart.clicked.connect(self.toggleStartPause)
        btnLayout.addWidget(self.btnStart)
        self.btnReset = PushButton("重置")
        self.btnReset.setMinimumWidth(110)
        self.btnReset.clicked.connect(self.reset)
        btnLayout.addWidget(self.btnReset)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)


class StopwatchPage(BaseTimerPage):
    def __init__(self):
        super().__init__("stopwatchPage")
        self.buildCommonUi()
    def getDisplayTime(self) -> int: return self.elapsedTotalMs()
    def getProgress(self) -> int:
        return int((self.elapsedTotalMs() % 60000) / 60000 * 100)


class CountdownPage(BaseTimerPage):
    def __init__(self):
        super().__init__("countdownPage")
        self.countdownTarget = 0
        self.buildCommonUi()
        self._buildDurationInput()

    def _buildDurationInput(self):
        card = CardWidget()
        apply_card_style(card)
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(8)
        row.addWidget(BodyLabel("时"))
        self.spinH = SpinBox(); self.spinH.setRange(0, 23); self.spinH.setValue(0)
        row.addWidget(self.spinH)
        row.addWidget(BodyLabel("分"))
        self.spinM = SpinBox(); self.spinM.setRange(0, 59); self.spinM.setValue(1)
        row.addWidget(self.spinM)
        row.addWidget(BodyLabel("秒"))
        self.spinS = SpinBox(); self.spinS.setRange(0, 59); self.spinS.setValue(0)
        row.addWidget(self.spinS)
        row.addStretch()
        self.customArea.addWidget(card)
        self.ringDisplay.setTimeText(self.formatTime(self._readDurationMs()))

    def _readDurationMs(self) -> int:
        return (self.spinH.value() * 3600 + self.spinM.value() * 60 + self.spinS.value()) * 1000

    def canStart(self) -> bool:
        if self.countdownTarget == 0:
            total = self._readDurationMs()
            if total <= 0:
                self.statusLabel.setText("请先设置倒计时时长")
                return False
            self.countdownTarget = total
            self.elapsedBeforePause = 0
        return True

    def getDisplayTime(self) -> int:
        return max(0, self.countdownTarget - self.elapsedTotalMs())

    def getProgress(self) -> int:
        if self.countdownTarget <= 0: return 0
        return min(100, int(100 * self.elapsedTotalMs() / self.countdownTarget))

    def onTick(self):
        super().onTick()
        if self.isRunning and self.elapsedTotalMs() >= self.countdownTarget:
            self._finish()

    def _finish(self):
        self.uiTimer.stop()
        self.stopwatch.invalidate()
        self.isRunning = False
        self.elapsedBeforePause = 0
        self.countdownTarget = 0
        self.btnStart.setText("开始")
        self.statusLabel.setText("⏰ 时间到！")
        self.ringDisplay.setProgress(100)
        self.ringDisplay.setTimeText("00:00.000")
        self.onFinished()

    def onReset(self):
        self.countdownTarget = 0
        self.ringDisplay.setTimeText(self.formatTime(self._readDurationMs()))


# ============================================================
# 多卡片
# ============================================================
class TimerCard(CardWidget):
    CARD_W = 280; CARD_H = 360; RING_SIZE = 170

    def __init__(self, title: str, duration_sec: int, on_remove=None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(self.CARD_W, self.CARD_H)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title = title
        self.duration_sec = duration_sec
        self.duration_ms = duration_sec * 1000
        self.countdownTarget = self.duration_ms
        self.elapsedBeforePause = 0
        self.stopwatch = QElapsedTimer()
        self.isRunning = False
        self._on_remove = on_remove
        self._buildUi()
        self.uiTimer = QTimer(self)
        self.uiTimer.setInterval(100)
        self.uiTimer.timeout.connect(self.onTick)
        self._refreshDisplay()

    def sizeHint(self) -> QSize: return QSize(self.CARD_W, self.CARD_H)

    def _buildUi(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        topRow = QHBoxLayout()
        topRow.setSpacing(4)
        self.titleLabel = BodyLabel(self.title)
        f = QFont(); f.setPointSize(11); f.setBold(True)
        self.titleLabel.setFont(f)
        topRow.addWidget(self.titleLabel)
        topRow.addStretch()
        self.btnFullscreen = TransparentToolButton(FIF.FULL_SCREEN)
        self.btnFullscreen.setFixedSize(28, 28)
        topRow.addWidget(self.btnFullscreen)
        self.btnPip = TransparentToolButton(FIF.VIDEO)
        self.btnPip.setFixedSize(28, 28)
        topRow.addWidget(self.btnPip)
        self.btnClose = TransparentToolButton(FIF.CLOSE)
        self.btnClose.setFixedSize(28, 28)
        self.btnClose.clicked.connect(self._remove)
        topRow.addWidget(self.btnClose)
        layout.addLayout(topRow)

        centerRow = QHBoxLayout()
        centerRow.addStretch()
        self.ringDisplay = RingDisplay(size=self.RING_SIZE, time_font_px=24, show_end_label=True)
        centerRow.addWidget(self.ringDisplay)
        centerRow.addStretch()
        layout.addLayout(centerRow)
        layout.addStretch()

        bottomRow = QHBoxLayout()
        bottomRow.addStretch()
        self.btnStart = ToolButton(FIF.PLAY, self)
        self.btnStart.setFixedSize(38, 38)
        self.btnStart.clicked.connect(self.toggleStartPause)
        bottomRow.addWidget(self.btnStart)
        self.btnReset = TransparentToolButton(FIF.SYNC, self)
        self.btnReset.setFixedSize(38, 38)
        self.btnReset.clicked.connect(self.reset)
        bottomRow.addWidget(self.btnReset)
        bottomRow.addStretch()
        layout.addLayout(bottomRow)

    def _remove(self):
        self.uiTimer.stop()
        self.stopwatch.invalidate()
        if callable(self._on_remove):
            self._on_remove(self)

    def elapsedTotalMs(self) -> int:
        return self.elapsedBeforePause + (
            self.stopwatch.elapsed() if self.stopwatch.isValid() else 0)

    def remainingMs(self) -> int:
        return max(0, self.countdownTarget - self.elapsedTotalMs())

    def toggleStartPause(self):
        if self.isRunning: self.pause()
        else: self.start()

    def start(self):
        if self.isRunning: return
        if self.remainingMs() <= 0: self.reset()
        self.stopwatch.start()
        self.uiTimer.start()
        self.isRunning = True
        self.btnStart.setIcon(FIF.PAUSE)

    def pause(self):
        if not self.isRunning: return
        self.elapsedBeforePause = self.elapsedTotalMs()
        self.stopwatch.invalidate()
        self.uiTimer.stop()
        self.isRunning = False
        self.btnStart.setIcon(FIF.PLAY)

    def reset(self):
        self.uiTimer.stop()
        self.stopwatch.invalidate()
        self.isRunning = False
        self.elapsedBeforePause = 0
        self.countdownTarget = self.duration_ms
        self.btnStart.setIcon(FIF.PLAY)
        self._refreshDisplay()

    def onTick(self):
        self._refreshDisplay()
        if self.isRunning and self.remainingMs() <= 0:
            self._finish()

    def _finish(self):
        self.uiTimer.stop()
        self.stopwatch.invalidate()
        self.isRunning = False
        self.elapsedBeforePause = self.duration_ms
        self.btnStart.setIcon(FIF.PLAY)
        self._refreshDisplay()

    def _refreshDisplay(self):
        remaining = self.remainingMs()
        progress = 0
        if self.duration_ms > 0:
            progress = int(100 * (self.duration_ms - remaining) / self.duration_ms)
        self.ringDisplay.setProgress(max(0, min(progress, 100)))
        total_sec = remaining // 1000
        h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        self.ringDisplay.setTimeText(f"{h:02d}:{m:02d}:{s:02d}")
        if self.isRunning:
            end_dt = datetime.now() + timedelta(milliseconds=remaining)
            self.ringDisplay.setEndTimeText(f"🔔 {end_dt.strftime('%H:%M')}", True)
        else:
            self.ringDisplay.setEndTimeText("", False)


class MultiTimerPage(QWidget):
    def __init__(self, settings: Settings):
        super().__init__()
        self.setObjectName("multiTimerPage")
        self.settings = settings

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        toolbar = CardWidget()
        apply_card_style(toolbar)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(18, 12, 18, 12)
        tb.setSpacing(10)
        tb.addWidget(BodyLabel("自定义时长"))
        tb.addSpacing(8)

        last = settings.get("last_input", {"h": 0, "m": 0, "s": 30})
        self.spinH = SpinBox(); self.spinH.setRange(0, 23); self.spinH.setValue(last.get("h", 0))
        self.spinH.setMinimumWidth(90); self.spinH.setAlignment(Qt.AlignCenter)
        tb.addWidget(self.spinH); tb.addWidget(BodyLabel("时")); tb.addSpacing(8)

        self.spinM = SpinBox(); self.spinM.setRange(0, 59); self.spinM.setValue(last.get("m", 0))
        self.spinM.setMinimumWidth(90); self.spinM.setAlignment(Qt.AlignCenter)
        tb.addWidget(self.spinM); tb.addWidget(BodyLabel("分")); tb.addSpacing(8)

        self.spinS = SpinBox(); self.spinS.setRange(0, 59); self.spinS.setValue(last.get("s", 30))
        self.spinS.setMinimumWidth(90); self.spinS.setAlignment(Qt.AlignCenter)
        tb.addWidget(self.spinS); tb.addWidget(BodyLabel("秒")); tb.addSpacing(12)

        self.btnAdd = PrimaryPushButton("添加")
        self.btnAdd.setMinimumWidth(90)
        self.btnAdd.clicked.connect(self._addCustomCard)
        tb.addWidget(self.btnAdd)
        tb.addStretch()

        self.btnClear = PushButton("清空全部")
        self.btnClear.setMinimumWidth(100)
        self.btnClear.clicked.connect(self._clearAll)
        tb.addWidget(self.btnClear)
        root.addWidget(toolbar)

        self.gridHost = QWidget()
        self.flow = FlowLayout(self.gridHost, margin=0, h_spacing=14, v_spacing=14)
        root.addWidget(self.gridHost, 1)
        self.cards = []

        for item in settings.get("cards", []):
            self._addCard(item["title"], item["duration_sec"], persist=False)

        self.spinH.valueChanged.connect(self._persist_last_input)
        self.spinM.valueChanged.connect(self._persist_last_input)
        self.spinS.valueChanged.connect(self._persist_last_input)

    def _addCard(self, title: str, duration_sec: int, persist: bool = True):
        card = TimerCard(title, duration_sec, on_remove=self._removeCard)
        apply_card_style(card)
        self.flow.addWidget(card)
        self.cards.append(card)
        self.gridHost.updateGeometry()
        if persist:
            self._persist_cards()
        return card

    def _addCustomCard(self):
        h, m, s = int(self.spinH.value()), int(self.spinM.value()), int(self.spinS.value())
        total_sec = h * 3600 + m * 60 + s
        if total_sec <= 0: return
        if h > 0: title = f"{h} 时 {m} 分 {s} 秒"
        elif m > 0: title = f"{m} 分 {s} 秒"
        else: title = f"{s} 秒"
        self._addCard(title, total_sec)
        self._persist_last_input()

    def _removeCard(self, card: TimerCard):
        if card not in self.cards: return
        self.cards.remove(card)
        self.flow.removeWidget(card)
        card.setParent(None)
        card.deleteLater()
        self.gridHost.updateGeometry()
        self._persist_cards()

    def _clearAll(self):
        for card in list(self.cards):
            self._removeCard(card)
        self._persist_cards()

    def _persist_cards(self):
        self.settings.set("cards", [
            {"title": c.title, "duration_sec": c.duration_sec} for c in self.cards
        ])
        self.settings.save()

    def _persist_last_input(self):
        self.settings.set("last_input", {
            "h": int(self.spinH.value()), "m": int(self.spinM.value()), "s": int(self.spinS.value()),
        })
        self.settings.save()


# ============================================================
# 设置页
# ============================================================
class SettingPage(QWidget):
    def __init__(self, settings: Settings, main_window):
        super().__init__()
        self.setObjectName("settingPage")
        self.settings = settings
        self.main_window = main_window

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(16)

        title = StrongBodyLabel("设置")
        f = QFont(); f.setPointSize(20); f.setBold(True)
        title.setFont(f)
        root.addWidget(title)
        root.addSpacing(8)

        # 主题模式
        card1 = CardWidget()
        apply_card_style(card1)
        c1 = QHBoxLayout(card1)
        c1.setContentsMargins(18, 14, 18, 14)
        c1.setSpacing(12)
        c1.addWidget(BodyLabel("主题模式"))
        c1.addStretch()
        self.cmbTheme = ComboBox()
        self.cmbTheme.setMinimumWidth(140)
        for label, _ in THEME_LABELS:
            self.cmbTheme.addItem(label)
        cur_mode = settings.get("theme_mode", "auto")
        for i, (_, key) in enumerate(THEME_LABELS):
            if key == cur_mode:
                self.cmbTheme.setCurrentIndex(i)
                break
        self.cmbTheme.currentIndexChanged.connect(self._on_theme_mode)
        c1.addWidget(self.cmbTheme)
        root.addWidget(card1)

        # 主题色
        card2 = CardWidget()
        apply_card_style(card2)
        c2 = QHBoxLayout(card2)
        c2.setContentsMargins(18, 14, 18, 14)
        c2.setSpacing(12)
        c2.addWidget(BodyLabel("主题色"))
        c2.addStretch()
        self.cmbColor = ComboBox()
        self.cmbColor.setMinimumWidth(140)
        for label, _ in COLOR_LABELS:
            self.cmbColor.addItem(label)
        cur_color = settings.get("theme_color", "purple")
        for i, (_, key) in enumerate(COLOR_LABELS):
            if key == cur_color:
                self.cmbColor.setCurrentIndex(i)
                break
        self.cmbColor.currentIndexChanged.connect(self._on_color_changed)
        c2.addWidget(self.cmbColor)
        root.addWidget(card2)

        # 窗口置顶
        card3 = CardWidget()
        apply_card_style(card3)
        c3 = QHBoxLayout(card3)
        c3.setContentsMargins(18, 14, 18, 14)
        c3.setSpacing(12)
        c3.addWidget(BodyLabel("窗口置顶"))
        c3.addStretch()
        self.swTop = SwitchButton()
        self.swTop.setOnText("开")
        self.swTop.setOffText("关")
        self.swTop.setChecked(bool(settings.get("always_on_top", False)))
        self.swTop.checkedChanged.connect(self._on_top_changed)
        c3.addWidget(self.swTop)
        root.addWidget(card3)

        # 数据文件路径
        card4 = CardWidget()
        apply_card_style(card4)
        c4 = QVBoxLayout(card4)
        c4.setContentsMargins(18, 14, 18, 14)
        c4.setSpacing(8)
        row4 = QHBoxLayout()
        row4.addWidget(BodyLabel("配置文件路径"))
        row4.addStretch()
        btnOpen = PushButton("打开目录")
        btnOpen.clicked.connect(self._open_settings_dir)
        row4.addWidget(btnOpen)
        c4.addLayout(row4)
        pathLabel = CaptionLabel(settings.path)
        pathLabel.setWordWrap(True)
        pathLabel.setStyleSheet("color: #808080;")
        c4.addWidget(pathLabel)
        root.addWidget(card4)

        # 恢复默认
        card5 = CardWidget()
        apply_card_style(card5)
        c5 = QHBoxLayout(card5)
        c5.setContentsMargins(18, 14, 18, 14)
        c5.setSpacing(12)
        c5.addWidget(BodyLabel("恢复默认设置"))
        c5.addStretch()
        btnReset = PushButton("重置")
        btnReset.clicked.connect(self._reset_settings)
        c5.addWidget(btnReset)
        root.addWidget(card5)

        root.addStretch()

    def _on_theme_mode(self, index: int):
        key = THEME_LABELS[index][1]
        self.settings.set("theme_mode", key)
        self.settings.save()
        if key == "light": setTheme(Theme.LIGHT)
        elif key == "dark": setTheme(Theme.DARK)
        else: setTheme(Theme.AUTO)

    def _on_color_changed(self, index: int):
        key = COLOR_LABELS[index][1]
        self.settings.set("theme_color", key)
        self.settings.save()
        setThemeColor(THEME_COLORS[key])

    def _on_top_changed(self, checked: bool):
        self.settings.set("always_on_top", bool(checked))
        self.settings.save()
        self.main_window.apply_always_on_top(checked)

    def _open_settings_dir(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.settings.dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.settings.dir])
            else:
                subprocess.Popen(["xdg-open", self.settings.dir])
        except Exception as e:
            print(f"[Settings] 打开目录失败: {e}")

    def _reset_settings(self):
        self.settings.set("theme_mode", "auto")
        self.settings.set("theme_color", "purple")
        self.settings.set("always_on_top", False)
        self.settings.save()
        setTheme(Theme.AUTO)
        setThemeColor(THEME_COLORS["purple"])
        self.cmbTheme.setCurrentIndex(0)
        self.cmbColor.setCurrentIndex(0)
        self.swTop.setChecked(False)
        self.main_window.apply_always_on_top(False)


# ============================================================
# 主窗口
# ============================================================
class MainWindow(FluentWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("高级计时器")

        # 设置窗口图标
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        win = settings.get("window", {"w": 1200, "h": 800})
        self.resize(win.get("w", 1200), win.get("h", 800))

        mode = settings.get("theme_mode", "auto")
        if mode == "light": setTheme(Theme.LIGHT)
        elif mode == "dark": setTheme(Theme.DARK)
        else: setTheme(Theme.AUTO)

        color_key = settings.get("theme_color", "purple")
        try:
            setThemeColor(THEME_COLORS.get(color_key, "#8E8CD8"))
        except Exception as e:
            print(f"[Theme] {e}")
            setThemeColor("#8E8CD8")

        self.stopwatchPage = StopwatchPage()
        self.countdownPage = CountdownPage()
        self.multiTimerPage = MultiTimerPage(settings)
        self.settingPage = SettingPage(settings, self)

        self.addSubInterface(self.stopwatchPage, FIF.STOP_WATCH, "正计时")
        self.addSubInterface(self.countdownPage, FIF.HISTORY, "倒计时")
        self.addSubInterface(self.multiTimerPage, FIF.TILES, "多路计时")
        self.addSubInterface(
            self.settingPage, FIF.SETTING, "设置",
            position=NavigationItemPosition.BOTTOM)

        # 快捷键 Ctrl+T 切换置顶
        self.shortcutPin = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcutPin.activated.connect(
            lambda: self.settingPage.swTop.setChecked(
                not self.settingPage.swTop.isChecked())
        )

        if settings.get("always_on_top", False):
            self.apply_always_on_top(True)

    def apply_always_on_top(self, checked: bool):
        """统一由设置页调用，不需要底部工具条"""
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.settings.set("always_on_top", bool(checked))
        self.settings.save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'settings'):
            self.settings.set("window", {"w": self.width(), "h": self.height()})

    def closeEvent(self, event):
        if hasattr(self, 'settings'):
            self.settings.set("window", {"w": self.width(), "h": self.height()})
            self.settings.save()
        super().closeEvent(event)


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    QApplication.setApplicationName("AdvancedTimer")
    QApplication.setOrganizationName("Ticker")

    app = QApplication(sys.argv)

    # 设置全局应用图标（任务栏、Alt+Tab 等）
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    settings = Settings()
    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec_())