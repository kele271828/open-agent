import sys
import ctypes
import keyboard
import json
import re
import os
import tempfile
import uuid
from PyQt5.QtCore import QMimeData, Qt, QThread, pyqtSignal, QEvent, QTimer
from PyQt5.QtWidgets import (QFileDialog,
                             QApplication, QMainWindow, QSystemTrayIcon,
                             QMenu, QAction, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QDialog, QLabel,
                             QLineEdit, QSplitter, QListWidget, QListWidgetItem,
                             QTabWidget, QFormLayout, QMessageBox, QSpinBox, QScrollArea)
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView 
import html as pyhtml
import ast
from plyer import notification
# from settings import AI_NAME
from config import config
from string import Template

import logging

# =======================================================
# 引入你的原有 AI 依赖
# =======================================================
from Assistant import Assistant
from utils.tools_init import task_manager, event_queue, tools, read_file_content

assistant = Assistant(core_memory="./Memory/core_memory.md", medium_memory_path="./Memory/medium_memory.md")
task_manager.start()

# 获取当前脚本专用的 logger
logger = logging.getLogger(__name__)

# =======================================================
# 自定义输入框
# =======================================================
class ChatInputEdit(QTextEdit):
    send_signal = pyqtSignal()
    # 新增信号：向主窗口传递获取到的文件路径
    file_added_signal = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Microsoft YaHei", 10))
        self.setPlaceholderText("输入问题...\n[Enter] 发送 | [Ctrl+Enter] 换行 | [支持拖拽/粘贴文件]")
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 34, 40, 255); color: #FFFFFF;
                border: 1px solid #5C6370; border-radius: 6px; padding: 8px;
            }
            QTextEdit:focus { border: 1px solid #61AFEF; }
            QTextEdit:disabled { background-color: rgba(50, 54, 60, 255); color: #7F848E; }
        """)
        # 允许拖放
        self.setAcceptDrops(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ControlModifier:
                self.insertPlainText("\n")
            else:
                self.send_signal.emit()
                event.accept() 
        else:
            super().keyPressEvent(event)

    # ================= 处理粘贴 (Ctrl+V) =================
    def insertFromMimeData(self, source: QMimeData):
        # 1. 粘贴的是本地文件/文件管理器复制的文件
        if source.hasUrls():
            for url in source.urls():
                if url.isLocalFile():
                    self.file_added_signal.emit(url.toLocalFile())
            return # 拦截，不插入文本路径
            
        # 2. 粘贴的是内存中的截图 (如 QQ截图, Snipping Tool)
        elif source.hasImage():
            img = source.imageData()
            # 保存为临时文件，以便 read_file_content 能够读取
            temp_path = os.path.join(tempfile.gettempdir(), f"clipboard_img_{uuid.uuid4().hex[:8]}.png")
            img.save(temp_path)
            self.file_added_signal.emit(temp_path)
            return

        # 3. 普通文本粘贴，走默认逻辑
        super().insertFromMimeData(source)

    # ================= 处理拖拽 =================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.file_added_signal.emit(url.toLocalFile())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class CustomTitleBar(QWidget):
    def __init__(self, parent, title_text):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(50)
        
        # 【修改这里】：增加 border-top-left-radius 和 border-top-right-radius
        self.setStyleSheet("""
            QWidget { 
                background-color: #1E2227; 
                border-bottom: 1px solid #3E4451; 
                border-top-left-radius: 24px;
                border-top-right-radius: 24px;
            }
            QLabel { border: none; background: transparent; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 15, 0)

        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet("color: #ABB2BF; font-size: 36px; font-weight: bold;")

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #ABB2BF; font-size: 36px; border: none; border-radius: 10px;
            }
            QPushButton:hover { color: white; }
            QPushButton:pressed { color: red; }
        """)
        self.close_btn.clicked.connect(self.parent.close)

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.close_btn)

        self.start_pos = None

    # =========== 核心：实现鼠标拖拽窗口功能 ===========
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            delta = event.globalPos() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

# =======================================================
# 设置界面 Dialog
# =======================================================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(1200, 800) 

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setStyleSheet("""
            QDialog { 
                background: transparent; 
            }
            QWidget#bg_widget { 
                background-color: #282C34; 
                border: 1px solid #5C6370; 
                border-radius: 24px; 
            }
            QLabel { 
                color: #ABB2BF; 
                font-size: 28px; 
                border: none; 
                background: transparent; 
            }
            QLineEdit, QTextEdit, QSpinBox {
                background-color: #1E2227;
                color: #ABB2BF;
                border: 1px solid #5C6370;
                border-radius: 8px;
                padding: 10px; 
                font-size: 28px; 
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border: 1px solid #61AFEF;
            }
            QPushButton {
                background-color: #61AFEF;
                color: #282C34;
                font-weight: bold;
                font-size: 28px; 
                border-radius: 8px;
                padding: 12px 24px; 
            }
            QPushButton:hover {
                background-color: #56B6C2;
            }
            QTabWidget::pane {
                border: 1px solid #5C6370;
                border-radius: 8px;
                background-color: #282C34;
            }
            QTabBar::tab {
                background: #1E2227;
                color: #ABB2BF;
                font-size: 28px; 
                padding: 12px 24px;
                border: 1px solid #5C6370;
                border-bottom-color: #5C6370; 
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #282C34;
                color: #61AFEF;
                border-bottom-color: #282C34;
            }
            /* 滚动条深色适配 */
            QScrollBar:vertical {
                border: none;
                background: #282C34;
                width: 14px;
                margin: 15px 0 15px 0;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #5C6370;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ABB2BF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_widget = QWidget()
        self.bg_widget.setObjectName("bg_widget")
        outer_layout.addWidget(self.bg_widget)

        main_layout = QVBoxLayout(self.bg_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "⚙ AI 助手设置中心")
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        self.tabs = QTabWidget()
        self.setup_base_tab()
        self.setup_api_tab()
        self.setup_security_tab()
        self.setup_system_tab()
        self.setup_locations_tab()
        content_layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet("background-color: #5C6370; color: white;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self.save_all_configs)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        content_layout.addLayout(btn_layout)
        main_layout.addWidget(content_widget)

        # 核心：初始化时自动加载配置到 UI，保证打开时有值
        self.load_all_configs()

# ================= 辅助函数：创建滚动 Tab =================
    def create_scrollable_tab(self):
        """为包含多项设置的 Tab 创建带有滚动条的容器"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # 【修复核心 1】：强制 QScrollArea 视口背景透明
        scroll.setStyleSheet("background-color: transparent;") 
        
        container = QWidget()
        
        # 【修复核心 2】：强制内部承载表单的 QWidget 背景透明
        container.setStyleSheet("background-color: transparent;") 
        
        layout = QFormLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        scroll.setWidget(container)
        return scroll, layout

    # ================= UI 布局构建 =================
    def setup_base_tab(self):
        tab, layout = self.create_scrollable_tab()
        self.input_model_name = QLineEdit()
        self.input_ai_name = QLineEdit()
        layout.addRow("大语言模型:", self.input_model_name)
        layout.addRow("AI 称呼:", self.input_ai_name)
        self.tabs.addTab(tab, "基础")

    def setup_api_tab(self):
        tab, layout = self.create_scrollable_tab()
        self.input_api_url = QLineEdit()
        self.input_api_user = QLineEdit()
        self.input_api_pwd = QLineEdit()
        self.input_api_pwd.setEchoMode(QLineEdit.Password) # 密码掩码

        layout.addRow("服务端 URL:", self.input_api_url)
        layout.addRow("账户 ID:", self.input_api_user)
        layout.addRow("API 密码:", self.input_api_pwd)
        self.tabs.addTab(tab, "API")

    def setup_security_tab(self):
        tab, layout = self.create_scrollable_tab()

        self.input_allowed_drive = QLineEdit()
        self.spin_max_write_size = QSpinBox()
        self.spin_max_write_size.setRange(1, 1024)
        self.spin_max_write_size.setSuffix(" MB")

        # 多个多行输入框，高度设为 160 容纳大字体
        self.input_allowed_exts = QTextEdit(); self.input_allowed_exts.setFixedHeight(160)
        self.input_allowed_img_exts = QTextEdit(); self.input_allowed_img_exts.setFixedHeight(160)
        self.input_write_exts = QTextEdit(); self.input_write_exts.setFixedHeight(160)
        self.input_whitelist = QTextEdit(); self.input_whitelist.setFixedHeight(160)
        self.input_blacklist = QTextEdit(); self.input_blacklist.setFixedHeight(160)

        layout.addRow("基础沙箱驱动器:", self.input_allowed_drive)
        layout.addRow("最大写入大小:", self.spin_max_write_size)
        layout.addRow("允许读后缀:", self.input_allowed_exts)
        layout.addRow("允许读图片:", self.input_allowed_img_exts)
        layout.addRow("允许写后缀:", self.input_write_exts)
        layout.addRow("白名单路径(绝对):", self.input_whitelist)
        layout.addRow("黑名单路径(绝对):", self.input_blacklist)
        
        self.tabs.addTab(tab, "安全")

    def setup_system_tab(self):
        tab, layout = self.create_scrollable_tab()

        self.input_app_registry = QTextEdit()
        self.input_app_registry.setFixedHeight(300)
        self.input_app_registry.setPlaceholderText("格式:\n微信=C:/.../Weixin.exe\n浏览器=msedge.exe")

        self.input_allowed_processes = QTextEdit()
        self.input_allowed_processes.setFixedHeight(200)

        layout.addRow("应用注册表:", self.input_app_registry)
        layout.addRow("进程关闭白名单:", self.input_allowed_processes)

        self.tabs.addTab(tab, "系统")

    def setup_locations_tab(self):
        tab, layout = self.create_scrollable_tab()

        self.input_locations = QTextEdit()
        self.input_locations.setFixedHeight(400)
        self.input_locations.setPlaceholderText("格式:\n图书馆=34.123,108.456")

        layout.addRow("特定位置值:", self.input_locations)
        self.tabs.addTab(tab, "位置")


    # ================= 核心联动逻辑 =================
    def load_all_configs(self):
        """将 config 实例中的所有数据填充到 UI"""
        # 1. 基础 & API
        self.input_model_name.setText(config.MODEL_NAME)
        self.input_ai_name.setText(config.AI_NAME)
        self.input_api_url.setText(config.YS_BASE_URL)
        self.input_api_user.setText(config.YS_USER_ID)
        self.input_api_pwd.setText(config.YS_PASSWORD)

        # 2. 安全设置
        self.input_allowed_drive.setText(config.ALLOWED_DRIVE)
        self.spin_max_write_size.setValue(int(config.MAX_WRITE_SIZE / (1024 * 1024)))
        
        self.input_allowed_exts.setPlainText("\n".join(config.ALLOWED_EXTENSIONS))
        self.input_allowed_img_exts.setPlainText("\n".join(config.ALLOWED_IMAGE_EXTENSIONS))
        self.input_write_exts.setPlainText("\n".join(config.ALLOWED_WRITE_EXTENSIONS))
        self.input_whitelist.setPlainText("\n".join(config.WHITELIST_PATHS))
        self.input_blacklist.setPlainText("\n".join(config.BLACKLIST_PATHS))

        # 3. 系统 (字典转换为 Key=Value 字符串)
        reg_str = "\n".join([f"{k}={v}" for k, v in config.APP_REGISTRY.items()])
        self.input_app_registry.setPlainText(reg_str)
        self.input_allowed_processes.setPlainText("\n".join(config.ALLOWED_PROCESSES))

        # 4. 位置 (字典转换为 Name=Lat,Lng)
        loc_str = "\n".join([f"{k}={v[0]},{v[1]}" for k, v in config.MY_LOCATIONS.items()])
        self.input_locations.setPlainText(loc_str)


    def save_all_configs(self):
        """将 UI 数据反写回 config 实例并落盘"""
        try:
            # 1. 基础 & API
            config.MODEL_NAME = self.input_model_name.text().strip()
            config.AI_NAME = self.input_ai_name.text().strip()
            config.YS_BASE_URL = self.input_api_url.text().strip()
            config.YS_USER_ID = self.input_api_user.text().strip()
            config.YS_PASSWORD = self.input_api_pwd.text().strip()

            # 2. 安全设置
            config.ALLOWED_DRIVE = self.input_allowed_drive.text().strip()
            config._data["security"]["MAX_WRITE_SIZE_MB"] = self.spin_max_write_size.value()

            def get_set_from_text(widget):
                return {line.strip() for line in widget.toPlainText().split("\n") if line.strip()}

            config.ALLOWED_EXTENSIONS = get_set_from_text(self.input_allowed_exts)
            config.ALLOWED_IMAGE_EXTENSIONS = get_set_from_text(self.input_allowed_img_exts)
            config.ALLOWED_WRITE_EXTENSIONS = get_set_from_text(self.input_write_exts)
            config.WHITELIST_PATHS = get_set_from_text(self.input_whitelist)
            config.BLACKLIST_PATHS = get_set_from_text(self.input_blacklist)

            # 3. 系统 (解析 Key=Value)
            app_dict = {}
            for line in self.input_app_registry.toPlainText().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    app_dict[k.strip()] = v.strip()
            config.APP_REGISTRY = app_dict
            
            config.ALLOWED_PROCESSES = get_set_from_text(self.input_allowed_processes)

            # 4. 位置 (解析 Name=Lat,Lng)
            loc_dict = {}
            for line in self.input_locations.toPlainText().split("\n"):
                if "=" in line and "," in line:
                    k, coords = line.split("=", 1)
                    lat, lng = coords.split(",", 1)
                    loc_dict[k.strip()] = (float(lat.strip()), float(lng.strip()))
            config.MY_LOCATIONS = loc_dict

            # 触发落盘
            config.save()

            QMessageBox.information(self, "成功", "设置已保存！\n底层模型规则已实时热更新。")
            self.accept()

        except ValueError as ve:
            QMessageBox.warning(self, "格式错误", "字典数据格式解析失败，请检查是否严格使用了 '=' 和 ',' 分隔符。")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"发生了意外错误:\n{str(e)}")

# =======================================================
# 历史记录 Dialog (左右分栏 + WebEngine 渲染版)
# =======================================================
class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. 隐藏原生标题栏
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # 2. 【核心修复】：开启顶层窗口的背景透明属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(1800, 1200)

        # 3. 创建最外层的布局（0边距）
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # 4. 创建一块带有背景色和圆角的底层画板（bg_widget）
        self.bg_widget = QWidget()
        self.bg_widget.setObjectName("bg_widget")
        outer_layout.addWidget(self.bg_widget)

        # 5. 把所有的样式从 QDialog 转移到 QWidget#bg_widget 上，并加上 border-radius
        self.bg_widget.setStyleSheet("""
            QWidget#bg_widget { 
                background-color: #282C34; 
                border: 1px solid #5C6370; 
                border-radius: 24px; 
            }
            QLabel { color: #ABB2BF; font-size: 28px; border: none; background: transparent; }
            
            QLineEdit {
                background-color: #1E2227; color: #FFFFFF;
                border: 1px solid #5C6370; border-radius: 6px; padding: 8px; font-size: 28px;
            }
            QLineEdit:focus { border: 1px solid #61AFEF; }
            QListWidget {
                background-color: #1E2227; color: #ABB2BF;
                border: 1px solid #5C6370; border-radius: 6px; padding: 5px; font-size: 28px;
                outline: none;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #3E4451; }
            QListWidget::item:selected {
                background-color: #2C313A; color: #61AFEF; 
                border-left: 4px solid #61AFEF; border-radius: 4px;
            }
            /* ================= 滚动条美化 (Qt 原生) ================= */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4B5263;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5C6370;
            }
            /* 隐藏上下箭头 */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            /* 隐藏滚动条背景轨道 */
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            /* 水平滚动条 (如果有) */
            QScrollBar:horizontal {
                border: none;
                background: transparent;
                height: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4B5263;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5C6370;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            /* ================= 分割器 (QSplitter) 美化 ================= */
            QSplitter::handle {
                background-color: #282C34; /* 与弹窗主背景色一致，完美融入 */
            }
            QSplitter::handle:horizontal {
                width: 4px; /* 拖拽区域的宽度，保留一定的拖拽手感 */
            }
            QSplitter::handle:pressed {
                background-color: #61AFEF; /* 拖拽时稍微给一点蓝色高亮反馈，体验更好 */
            }
        """)

        # 6. 把原本的 main_layout 挂在 bg_widget 上
        main_layout = QVBoxLayout(self.bg_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 7. 顶部插入自定义标题栏
        self.title_bar = CustomTitleBar(self, "📜 历史记录与搜索")
        main_layout.addWidget(self.title_bar)

        # 8. 原有的 UI 逻辑放入 content_widget (保持不变)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部：搜索栏与按钮
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(60)
        self.search_input.setPlaceholderText("输入关键词搜索历史记录，留空则获取最近记录...")
        self.search_input.returnPressed.connect(self.do_search)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedSize(120, 60)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #61AFEF; color: #282C34; font-weight: bold; 
                border-radius: 6px; font-size: 28px;
            }
            QPushButton:hover { background-color: #56B6C2; }
        """)
        self.search_btn.clicked.connect(self.do_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        content_layout.addLayout(search_layout)

        # 中部：水平分割器
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.record_list = QListWidget()
        self.record_list.itemClicked.connect(self.on_record_clicked)
        
        # ======== [新增] 文本自动换行与禁用横向滚动条 ========
        self.record_list.setWordWrap(True) # 允许条目文本换行
        self.record_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # 彻底关闭横向滚动条
        # =====================================================
        
        self.chat_display = QWebEngineView()
        self.chat_display.setFocusPolicy(Qt.NoFocus)
        self.chat_display.page().setBackgroundColor(QColor(0, 0, 0, 0))
        
        # 初始化 HTML 模板
        final_html = HTML_TEMPLATE.safe_substitute(
            base_font_size="24px", 
            sys_color="#61AFEF",
            AI_NAME=config.AI_NAME,
        )
        self.chat_display.setHtml(final_html)

        self.splitter.addWidget(self.record_list)
        self.splitter.addWidget(self.chat_display)
        self.splitter.setSizes([350, 1450]) 
        content_layout.addWidget(self.splitter)

        # 将内容区域加入主布局
        main_layout.addWidget(content_widget)
        
        self.current_results = []
        
        # ======== 纯前端分页状态变量 ========
        self.all_results = []            # 存放后端返回的【所有】结果
        self.current_rendered_count = 0  # 当前已经在 UI 中渲染的数量
        self.items_per_page = 15         # 每次滑动到底部渲染的条数
        # =====================================

        self.is_page_ready = False
        self.chat_display.loadFinished.connect(self.on_page_loaded)

        # 监听滚动条事件
        self.record_list.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def keyPressEvent(self, event):
        """
        拦截回车键，防止触发 QDialog 的默认关闭行为
        """
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            # 直接 pass，不调用 super().keyPressEvent(event)
            # 这样既能阻止窗口关闭，又不会影响 QLineEdit 触发 returnPressed 信号
            pass
        else:
            super().keyPressEvent(event)

    def on_scroll(self, value):
        scrollbar = self.record_list.verticalScrollBar()
        # 滑动到底部，且还有未渲染的数据
        if value == scrollbar.maximum() and self.current_rendered_count < len(self.all_results):
            self.render_more_items()

    def do_search(self):
        query = self.search_input.text().strip()
        
        # 1. 重置界面和状态
        self.record_list.clear()
        self.all_results = []
        self.current_rendered_count = 0
        
        # 清空 Web 视图并提示
        self.chat_display.page().runJavaScript("document.getElementById('chat').innerHTML = '';")
        self.chat_display.page().runJavaScript(f"appendSysMsg('正在检索中...');")
        QApplication.processEvents() # 强制刷新 UI，防止卡死

        try:
            # 2. 一次性向后端请求全量/极大量的搜索结果
            # 注意：这里的 search_deep_memory 返回的是所有匹配项
            results = assistant.search_deep_memory(query, n_results=5000) 
            self.all_results = results if results else []
            
            if not self.all_results:
                self.chat_display.page().runJavaScript(f"appendSysMsg('未找到相关的历史记录。');")
                return

            self.chat_display.page().runJavaScript("document.getElementById('chat').innerHTML = '';")
            self.chat_display.page().runJavaScript(f"appendSysMsg('检索完成，共找到 {len(self.all_results)} 条记录。请点击左侧查看详情。');")

            # 3. 初始渲染第一页
            self.render_more_items()

        except Exception as e:
            logger.error(f"搜索历史记录异常: {e}")
            self.chat_display.page().runJavaScript(f"appendSysMsg('搜索出错: {str(e)}');")

    def render_more_items(self):
        """从 self.all_results 中切片取下一批数据渲染到 QListWidget"""
        start_idx = self.current_rendered_count
        end_idx = min(start_idx + self.items_per_page, len(self.all_results))
        
        # 切片获取要渲染的这一批数据
        batch_results = self.all_results[start_idx:end_idx]

        for i, res in enumerate(batch_results):
            title = res.get('title', '无标题')
            date = res.get('date', '未知日期')
            
            item = QListWidgetItem(f"{title}\n🕒 {date}")
            # 绑定的全局索引是 start_idx + i
            item.setData(Qt.UserRole, start_idx + i)
            self.record_list.addItem(item)
            
        # 更新已渲染的数量
        self.current_rendered_count = end_idx


    # [新增方法] 网页加载完成后再触发搜索
    def on_page_loaded(self, ok):
        if ok and not self.is_page_ready:
            self.is_page_ready = True
            self.do_search() # 初始化加载移到这里执行


    def on_record_clicked(self, item):
        # 取出刚才绑定的全局索引
        idx = item.data(Qt.UserRole)
        # 从全量列表中获取数据
        res = self.all_results[idx]
        context_raw = res.get('original_context', '')
        
        # 清空聊天界面
        self.chat_display.page().runJavaScript("document.getElementById('chat').innerHTML = '';")
        
        if not context_raw:
            self.chat_display.page().runJavaScript(f"appendSysMsg('该记录没有原始上下文。');")
            return

        # 尝试将 context_raw 解析为 Python List/Dict
        messages = context_raw
        if isinstance(context_raw, str):
            try:
                messages = json.loads(context_raw)
            except json.JSONDecodeError:
                try:
                    messages = ast.literal_eval(context_raw)
                except:
                    messages = context_raw # 解析失败则保留原样

        # 1. 格式为标准消息列表 [{"role": "user", "content": "..."}, ...]
        if isinstance(messages, list):
            for msg in messages:
                if not isinstance(msg, dict): continue
                role = msg.get('role', '')
                
                # 【修改点 1】: 不要直接 str()，保留原始类型（可能是 str，也可能是 list）
                raw_content = msg.get('content', '')
                
                if role == 'user':
                    display_html = self.process_history_user_content(raw_content)
                    self.chat_display.page().runJavaScript(f"appendUserMsg({json.dumps(display_html)});")
                    
                elif role == 'assistant' or role == 'model':
                    self.chat_display.page().runJavaScript("startAiMsg();")
                    html_content = self.process_history_ai_text(str(raw_content))
                    self.chat_display.page().runJavaScript(f"updateAiMsg({json.dumps(html_content)});")
                    
                elif role == 'system':
                    self.chat_display.page().runJavaScript(f"appendSysMsg({json.dumps(str(raw_content))});")
                    
        # 2. 回退机制：如果它只是一段普通的字符串
        elif isinstance(messages, str):
            self.chat_display.page().runJavaScript("startAiMsg();")
            html_content = self.process_history_ai_text(messages)
            self.chat_display.page().runJavaScript(f"updateAiMsg({json.dumps(html_content)});")
    
    def process_history_user_content(self, raw_content):
        """简单粗暴：列表里的最后一个文本块正常显示，其余全部折叠"""
        final_html = ""

        if isinstance(raw_content, list):
            # 1. 找到列表中最后一块文本的索引
            last_text_idx = -1
            for i, item in enumerate(raw_content):
                if isinstance(item, dict) and item.get("type") == "text":
                    last_text_idx = i

            # 2. 遍历渲染
            for i, item in enumerate(raw_content):
                if not isinstance(item, dict):
                    continue
                
                item_type = item.get("type")
                
                if item_type == "text":
                    text_data = item.get("text", "")
                    
                    if i == last_text_idx:
                        # 【最后一块文本】：判定为用户的提问，直接展示
                        final_html += pyhtml.escape(text_data).replace('\n', '<br>')
                    else:
                        # 【前面的文本】：判定为文本附件，进行折叠
                        # 尝试从内容中提取一下文件名，提取不到就用默认名
                        filename = "文本附件"
                        m = re.search(r'--- 文件内容开始 \((.*?)\) ---', text_data)
                        if m:
                            filename = m.group(1)
                        
                        safe_text = pyhtml.escape(text_data)
                        final_html += (
                            f'<details>'
                            f'<summary style="color: #98C379; cursor: pointer;">📎 {pyhtml.escape(filename)}</summary>'
                            f'<pre style="max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-size: 20px; background-color: #1E2227; padding: 10px; border-radius: 6px;">'
                            f'<code>{safe_text}</code></pre>'
                            f'</details><br>'
                        )
                        
                elif item_type == "image_url":
                    # 【图片】：一律判定为附件，进行折叠
                    img_url = item.get("image_url", {}).get("url", "")
                    final_html += (
                        f'<details>'
                        f'<summary style="color: #98C379; cursor: pointer;">🖼️ 图片附件 (点击展开)</summary>'
                        f'<img src="{img_url}" style="max-width: 100%; margin-top: 10px; border-radius: 8px;">'
                        f'</details><br>'
                    )
                    
        elif isinstance(raw_content, str):
            # 如果是纯字符串（比如没有附件时的历史记录），直接展示
            final_html = pyhtml.escape(raw_content).replace('\n', '<br>')

        return final_html

    def _format_user_text(self, text):
        """解析纯文本中的特殊文件包裹格式，转为折叠 UI"""
        # 利用正则匹配 FloatingWindow.handle_send 中的文本注入格式
        # re.DOTALL 使得 '.' 能够匹配换行符
        pattern = re.compile(r'--- 文件内容开始 \((.*?)\) ---\n(.*?)\n--- 文件内容结束 ---', re.DOTALL)
        
        last_end = 0
        html_str = ""

        for match in pattern.finditer(text):
            # 1. 把匹配到的前面的正常对话转为普通文本，并保留换行
            normal_text = text[last_end:match.start()]
            if normal_text:
                html_str += pyhtml.escape(normal_text).replace('\n', '<br>')

            # 2. 提取文件名和文件内容
            filename = match.group(1)
            file_data = match.group(2)
            safe_file_data = pyhtml.escape(file_data)

            # 3. 构建折叠模块（复用你在 HTML_TEMPLATE 里已经写好的 details 样式，加个最大高度限制防霸屏）
            fold_html = (
                f'<details>'
                f'<summary style="color: #98C379;">📎 文本附件: {pyhtml.escape(filename)}</summary>'
                f'<pre style="max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-size: 20px;">'
                f'<code>{safe_file_data}</code></pre>'
                f'</details>'
            )
            html_str += fold_html
            last_end = match.end()

        # 4. 把剩下没有匹配到的尾部正常文本加上去
        remaining_text = text[last_end:]
        if remaining_text:
            html_str += pyhtml.escape(remaining_text).replace('\n', '<br>')

        return html_str

    def process_history_ai_text(self, text):
        """复用主程序的 Markdown 和 标签折叠 逻辑"""
        answer_indices = [m.start() for m in re.finditer(r'\[回答\]', text)]
        
        if not answer_indices:
            # 如果没有 [回答] 标签，直接当作最终文本
            return text
            
        last_ans_idx = answer_indices[-1]
        process_text = text[:last_ans_idx].strip()
        answer_text = text[last_ans_idx + len('[回答]'):].strip()
        
        if process_text:
            process_text = re.sub(r'\[(思考|模型决定调用工具|执行工具|工具返回|工具执行完毕，大模型继续生成\.\.\.)\]', r'**[\1]**', process_text)
            process_text = re.sub(r'\[(回答)\]', r'**[中间输出]**', process_text)
            
            # 因为是历史记录，状态统一标记为已完成
            return f'<details><summary>⚙️ 思考与工具调用 （已折叠）</summary>\n\n{process_text}\n\n</details>\n\n{answer_text}'
        else:
            return answer_text


# =======================================================
# 1. AI 工作的后台处理线程
# =======================================================
class AIWorkerThread(QThread):
    start_ai_signal = pyqtSignal()
    update_ai_signal = pyqtSignal(str)
    sys_msg_signal = pyqtSignal(str) 
    finished_signal = pyqtSignal()

    def run(self):
        while True:
            event = event_queue.get()
            event_type = event.get("type")
            content = event.get("content")

            if event_type == "external_task":
                self.start_ai_signal.emit()
                msg = f"已接收系统任务：**{content}**\n\n<think>正在后台处理系统任务...</think>\n\n"
                self.update_ai_signal.emit(msg)
                
                output = assistant.deal_task(content, tools=tools)
                if not output:
                    continue
                
                msg += f"处理完成：\n{output}"
                self.update_ai_signal.emit(msg)
                if output != "PASS":
                    notification.notify(title="AI 系统任务完成", message=output[:50]+"...", app_name='AIGF', timeout=5)
                self.finished_signal.emit()

            elif event_type == "heart_beat":
                output = assistant.heart_beat(tools=tools)
                if not output:
                    continue
                if output != "PASS":
                    self.start_ai_signal.emit()
                    self.update_ai_signal.emit(f"**心跳检测响应**：\n{output}")
                    notification.notify(title="AI 心跳通知", message=output[:50]+"...", app_name='AIGF', timeout=5)
                    self.finished_signal.emit()

            elif event_type == "command":
                if content == "clear":
                    if assistant.clear_context() == "SUCCESS":
                        self.sys_msg_signal.emit("上下文已清空。")
                        self.finished_signal.emit()

            elif event_type == "user_input":
                self.start_ai_signal.emit()
                accumulated_text = ""
                try:
                    gen = assistant.stream_answer(content, tools=tools)
                    for chunk in gen:
                        # 兼容处理：确保不管是字符串还是字典都能正确提取文本
                        chunk_text = chunk if isinstance(chunk, str) else chunk.get("content", "")
                        accumulated_text += chunk_text
                        self.update_ai_signal.emit(accumulated_text)
                except Exception as e:
                    self.update_ai_signal.emit(accumulated_text + f"\n\n**[错误]** AI 处理异常: {e}")
                finally:
                    self.finished_signal.emit()
            
            elif event_type == "tribe_message":
                self.start_ai_signal.emit()
                msg = f"接收到部落消息：**{content}**\n\n<think>正在处理...</think>\n\n"
                self.update_ai_signal.emit(msg)
                
                output = assistant.answer(content, tools=tools)
                if not output:
                    continue
                
                msg += f"{msg}\n\n[思考]\n{output['reasoning_content']}\n\n[回答]\n{output['content']}"
                self.update_ai_signal.emit(msg)
                if output["content"] != "PASS":
                    notification.notify(title="AI 回复消息", message=output["content"][:50]+"...", app_name='AIGF', timeout=5)
                self.finished_signal.emit()

            event_queue.task_done()

# =======================================================
# 定义 Web 渲染的 HTML 模板 [视觉重构版 & 修复 KaTeX 警告]
# =======================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    
    <script>
        const at = function(n) {
            n = Math.trunc(n) || 0;
            if (n < 0) n += this.length;
            if (n < 0 || n >= this.length) return undefined;
            return this[n];
        };
        if (!Array.prototype.at) Array.prototype.at = at;
        if (!String.prototype.at) String.prototype.at = at;
    </script>
    
    <script src="https://cdn.jsdelivr.net/npm/marked@4.3.0/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js"></script>
    
    <style>
        /* ================= 全局排版 ================= */
        body {
            color: #D4D4D4; 
            font-family: -apple-system, "Microsoft YaHei", "Segoe UI", Roboto, sans-serif; 
            font-size: 28px; /* [调整] 基础字号放大到 28px */
            line-height: 1.7;
            background-color: transparent; 
            word-wrap: break-word; 
            padding: 10px 20px 40px 20px;
            margin: 0;
        }

        /* ================= 消息头部标签 ================= */
        .msg-header {
            font-size: 28px;
            font-weight: bold;
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .user-header { color: #98C379; margin-top: 10px; }
        .sys-header { color: #61AFEF; margin-bottom: 15px; }
        .ai-header { color: #E5C07B; margin-top: 25px; }
        
        .ai-content { color: #ECEFF4; } /* AI 最终回复更亮，提升对比度 */

        /* ================= Markdown 元素美化 ================= */
        h1, h2, h3, h4 { color: #FFFFFF; font-weight: 600; margin-top: 1.5em; margin-bottom: 0.8em; }
        h1, h2 { border-bottom: 1px solid #3E4451; padding-bottom: 0.3em; }
        p { margin-bottom: 1em; }
        
        /* 引用块美化 */
        blockquote {
            border-left: 4px solid #61AFEF;
            padding: 10px 15px;
            color: #ABB2BF;
            background-color: rgba(97, 175, 239, 0.1);
            border-radius: 0 8px 8px 0;
            margin: 0 0 1em 0;
        }

        /* 表格美化 */
        table { width: 100%; border-collapse: collapse; margin-bottom: 1.5em; font-size: 28px; }
        th, td { border: 1px solid #4B5263; padding: 10px 14px; text-align: left; }
        th { background-color: #2C313A; color: #FFFFFF; }
        tr:nth-child(even) { background-color: rgba(44, 49, 58, 0.4); }

        /* 代码块美化 */
        pre { 
            background-color: #1E2227; 
            padding: 22px; 
            border-radius: 8px; 
            overflow-x: auto; 
            border: 1px solid #3E4451; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            margin: 1.2em 0;
        }
        code { 
            font-family: Consolas, "Fira Code", monospace; 
            font-size: 24px; 
            color: #E06C75; 
            background-color: rgba(224, 108, 117, 0.1);
            padding: 2px 4px;
            border-radius: 4px;
        }
        pre code { color: #ABB2BF; background-color: transparent; padding: 0; }

        /* ================= 折叠面板 (思考/工具) 美化 ================= */
        details { 
            background-color: #21252B; 
            padding: 12px 16px; 
            border-radius: 8px; 
            margin: 16px 0; 
            border: 1px solid #3E4451; 
            color: #ABB2BF; 
            font-size: 22px;
            transition: all 0.3s ease;
        }
        details[open] { 
            border-color: #C678DD; 
            box-shadow: 0 0 12px rgba(198, 120, 221, 0.15); 
        }
        summary { 
            cursor: pointer; 
            color: #C678DD; 
            font-weight: 600; 
            outline: none; 
            user-select: none;
            display: flex;
            align-items: center;
        }
        /* 自定义折叠小箭头 */
        summary::-webkit-details-marker { display: none; }
        summary::before { 
            content: '▶'; 
            margin-right: 10px; 
            font-size: 24px; 
            transition: transform 0.2s; 
        }
        details[open] summary::before { transform: rotate(90deg); }
        details > p:first-of-type { margin-top: 12px; }
        
        /* ================= 滚动条美化 (Web) ================= */
        ::-webkit-scrollbar {
            width: 8px;      /* 垂直滚动条宽度 */
            height: 8px;     /* 水平滚动条高度 */
        }
        ::-webkit-scrollbar-track {
            background: transparent; /* 轨道背景透明 */
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: #4B5263; /* 滚动条主色，与你的按钮悬停色一致 */
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #5C6370; /* 鼠标悬停时的颜色 */
        }
        /* 隐藏滚动条两端的上下箭头 */
        ::-webkit-scrollbar-button {
            display: none;
        }

    </style>
</head>
<body>
    <div id="chat">
        <div class="msg-header sys-header">[系统] AI 助手初始化完成。按 Alt+Z 唤醒。</div>
    </div>
    
    <script>
        const chat = document.getElementById('chat');
        let currentAiNode = null;

        function appendUserMsg(text) {
            chat.insertAdjacentHTML('beforeend', `<div class="msg-header user-header">[你]</div><div>${text}</div>`);
            scrollToBottom();
        }

        function appendSysMsg(text) {
            chat.insertAdjacentHTML('beforeend', `<div class="msg-header sys-header">[系统] ${text}</div>`);
            scrollToBottom();
        }

        function startAiMsg() {
            let div = document.createElement('div');
            div.innerHTML = `<div class="msg-header ai-header">[${AI_NAME}]</div><div class="ai-content"></div>`;
            chat.appendChild(div);
            currentAiNode = div.querySelector('.ai-content');
            scrollToBottom();
        }

        function updateAiMsg(markdownText) {
            if (!currentAiNode) return;
            
            // 渲染 Markdown
            currentAiNode.innerHTML = marked.parse(markdownText);
            
            // 渲染 LaTeX，并禁用 strict 警告
            renderMathInElement(currentAiNode, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\\\(', right: '\\\\)', display: false},
                    {left: '\\\\[', right: '\\\\]', display: true}
                ],
                throwOnError: false,
                strict: false  // [修复] 关闭 KaTeX 的严格模式，彻底消除中文警告
            });
            scrollToBottom();
        }

        function scrollToBottom() {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""
HTML_TEMPLATE = Template(HTML_TEMPLATE)

# =======================================================
# 2. 主悬浮窗界面
# =======================================================
class FloatingWindow(QMainWindow):
    hotkey_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.hotkey_signal.connect(self.toggle_window)
        self.is_settings_open = False 
        
        self.initUI()
        self.initTray()
        self.initHotkey()
        
        self.ai_thread = AIWorkerThread()
        self.ai_thread.start_ai_signal.connect(self.on_start_ai)
        self.ai_thread.update_ai_signal.connect(self.on_update_ai)
        self.ai_thread.sys_msg_signal.connect(self.on_sys_msg)
        self.ai_thread.finished_signal.connect(self.on_ai_finished)
        self.ai_thread.start()

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.trigger_heartbeat)
        self.heartbeat_timer.start(600000) 

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("""
            QWidget { background-color: rgba(40, 44, 52, 240); border-radius: 24px; }
            QPushButton {
                background-color: #3B4048; color: #ABB2BF; border: 3px solid #5C6370;
                border-radius: 12px; padding: 12px 24px; font-family: "Microsoft YaHei"; font-size: 28px;
            }
            QPushButton:hover { background-color: #4B5263; color: #FFFFFF; }
            QPushButton:pressed { background-color: #282C34; }
            QPushButton#sendBtn { background-color: #61AFEF; color: #282C34; font-weight: bold; border: none; }
            QPushButton#sendBtn:hover { background-color: #56B6C2; }
        """)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # [新增] 初始化待发送文件列表
        self.pending_files = []

        self.chat_display = QWebEngineView()
        self.chat_display.setFocusPolicy(Qt.NoFocus)
        self.chat_display.page().setBackgroundColor(QColor(0, 0, 0, 0)) 

        final_html = HTML_TEMPLATE.safe_substitute(
            base_font_size="28px",
            sys_color="#61AFEF",
            AI_NAME=config.AI_NAME,
        )
        self.chat_display.setHtml(final_html)

        # [新增] 附件展示区
        self.attachment_panel = QWidget()
        self.attachment_panel.setFixedHeight(100)
        self.attachment_panel.hide() # 没附件时隐藏
        self.attachment_layout = QHBoxLayout(self.attachment_panel)
        self.attachment_layout.setContentsMargins(0, 0, 0, 0)
        self.attachment_layout.setSpacing(10)
        self.attachment_layout.setAlignment(Qt.AlignLeft)

        self.input_field = ChatInputEdit()
        self.input_field.setFixedHeight(150) 
        self.input_field.send_signal.connect(self.handle_send)

        # 绑定文件添加信号
        self.input_field.file_added_signal.connect(self.add_attachment)

        btn_layout = QHBoxLayout()
        
        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.history_btn = QPushButton("📜 历史")
        self.history_btn.clicked.connect(self.open_history)
        
        # [新增] 文件上传按钮
        self.file_btn = QPushButton("📎 文件")
        self.file_btn.clicked.connect(self.open_file_dialog)
        
        self.clear_btn = QPushButton("🗑 清空上下文")
        self.clear_btn.clicked.connect(self.handle_clear)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn") 
        self.send_btn.setFixedWidth(150)
        self.send_btn.clicked.connect(self.handle_send)

        btn_layout.addWidget(self.settings_btn)
        btn_layout.addWidget(self.history_btn)
        btn_layout.addWidget(self.file_btn) # 添加到布局
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.send_btn)

        layout.addWidget(self.chat_display)
        layout.addWidget(self.attachment_panel) # 附件栏放在输入框上方
        layout.addWidget(self.input_field)
        layout.addLayout(btn_layout)

        self.setFixedSize(1600, 1200)
        self.hide()
        # self.apply_acrylic_blur()

    def apply_acrylic_blur(self):
        """为 Windows 10/11 启用 Acrylic 毛玻璃效果（修正版）"""
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            user32 = ctypes.windll.user32

            class ACCENTPOLICY(ctypes.Structure):
                _fields_ = [
                    ("AccentState", ctypes.c_uint),
                    ("AccentFlags", ctypes.c_uint),
                    ("GradientColor", ctypes.c_uint),
                    ("AnimationId", ctypes.c_uint),
                ]

            class WINCOMPATTRDATA(ctypes.Structure):
                _fields_ = [
                    ("Attribute", ctypes.c_int),
                    ("Data", ctypes.POINTER(ctypes.c_void_p)),
                    ("Size", ctypes.c_size_t),
                ]

            ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
            WCA_ACCENT_POLICY = 19

            accent = ACCENTPOLICY()
            accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
            
            # 关键修复：添加 0x80 标志（启用透明混合）
            accent.AccentFlags = 0x20 | 0x40 | 0x80
            
            # 设置 GradientColor：高位是透明度 (0x00~0xFF)，低24位是 RGB 颜色
            # 0x282C34 是你窗口背景的深色，0x32 是半透明度（约 50%），可根据喜好调整
            bg_color = 0x282C34          # 你的窗口主色 (#282C34)
            alpha = 0x00                 # 50% 透明度 (0x00=全透明, 0xFF=不透明)
            accent.GradientColor = (alpha << 24) | bg_color
            
            accent.AnimationId = 0

            data = WINCOMPATTRDATA()
            data.Attribute = WCA_ACCENT_POLICY
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_void_p))
            data.Size = ctypes.sizeof(accent)

            user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        except Exception as e:
            print(f"启用毛玻璃失败: {e}")

    # ================= 附件管理逻辑 =================
    def open_file_dialog(self):
        # 允许选择任意文件
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "All Files (*)")
        for path in file_paths:
            self.add_attachment(path)

    def add_attachment(self, file_path):
        if file_path not in self.pending_files:
            self.pending_files.append(file_path)
            self.update_attachment_ui()

    def remove_attachment(self, file_path):
        if file_path in self.pending_files:
            self.pending_files.remove(file_path)
            self.update_attachment_ui()

    def update_attachment_ui(self):
        # 清空当前UI
        for i in reversed(range(self.attachment_layout.count())): 
            widget = self.attachment_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if not self.pending_files:
            self.attachment_panel.hide()
            return

        self.attachment_panel.show()
        # 重新生成附件卡片
        for path in self.pending_files:
            filename = os.path.basename(path)
            
            tag_widget = QWidget()
            tag_widget.setStyleSheet("""
                QWidget { background-color: #3E4451; border-radius: 12px; }
                QLabel { color: #ABB2BF; font-size: 28px; padding: 4px; }
                QPushButton { background: transparent; color: #E06C75; border: none; font-size: 28px; font-weight: bold; }
                QPushButton:hover { color: #FF0000; }
            """)
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(8, 2, 8, 2)
            
            # 文件名截断防过长
            display_name = filename if len(filename) < 15 else filename[:12] + "..."
            label = QLabel(f"📎 {display_name}")
            
            close_btn = QPushButton("×")
            close_btn.setFixedSize(40, 40)
            close_btn.clicked.connect(lambda checked, p=path: self.remove_attachment(p))
            
            tag_layout.addWidget(label)
            tag_layout.addWidget(close_btn)
            self.attachment_layout.addWidget(tag_widget)
            
        self.attachment_layout.addStretch()

    # ================= 发送逻辑大改造 =================
    def handle_send(self):
        text = self.input_field.toPlainText().strip()
        
        # 既没有文字也没有文件，直接返回
        if not text and not self.pending_files: 
            return

        # 1. UI 前端回显：展示发送的内容和附件名
        display_text = text.replace('\n', '<br>')
        if self.pending_files:
            file_names = [os.path.basename(p) for p in self.pending_files]
            display_text = f"<span style='color:#61AFEF;'>[上传了 {len(file_names)} 个文件: {', '.join(file_names)}]</span><br>" + display_text
            
        self.chat_display.page().runJavaScript(f"appendUserMsg({json.dumps(display_text)});")
        
        # 2. 构建多模态最终输入载荷 (Payload)
        final_payload = []
        
        # 处理文件解析
        for file_path in self.pending_files:
            try:
                file_data = read_file_content(file_path)
                
                if isinstance(file_data, str):
                    # 如果解析出来是纯文本 (比如 txt, md)
                    final_payload.append({
                        "type": "text", 
                        "text": f"--- 文件内容开始 ({os.path.basename(file_path)}) ---\n{file_data}\n--- 文件内容结束 ---"
                    })
                elif isinstance(file_data, list):
                    # 如果解析出来已经是图片/多模态的 list，直接 extend 展开
                    final_payload.extend(file_data)
                    
            except Exception as e:
                logger.error(f"解析文件失败: {file_path}, 错误: {e}")
                self.on_sys_msg(f"警告：读取文件 {os.path.basename(file_path)} 失败。")

        # 将用户输入的文字放在最后 (更符合大模型的指令遵循习惯)
        if text:
            final_payload.append({"type": "text", "text": text})
        
        # 3. 清理状态
        self.input_field.clear()
        self.pending_files.clear()
        self.update_attachment_ui()
        self.set_ui_enabled(False)
        
        # 4. 如果没有文件，退化为纯文本以兼容传统 API；否则发送组装好的 list
        content_to_send = final_payload if len(final_payload) > 1 else (text if text else final_payload)
        print(content_to_send)
        event_queue.put({"type": "user_input", "content": content_to_send})

    def handle_clear(self):
        self.set_ui_enabled(False)
        event_queue.put({"type": "command", "content": "clear"})

    def open_settings(self):
        self.is_settings_open = True
        dialog = SettingsDialog(self)
        dialog.exec_()
        self.is_settings_open = False

    def open_history(self):
        self.is_settings_open = True  # 借用这个 Flag，防止弹窗时主界面消失
        dialog = HistoryDialog(self)
        dialog.exec_()
        self.is_settings_open = False

    def set_ui_enabled(self, state):
        self.input_field.setEnabled(state)
        self.send_btn.setEnabled(state)
        self.clear_btn.setEnabled(state)
        if not state:
            self.input_field.setPlaceholderText("AI 正在处理中...")
            self.send_btn.setText("处理中...")
        else:
            self.input_field.setPlaceholderText("输入你的问题...\n[Enter] 发送 | [Ctrl + Enter] 换行")
            self.send_btn.setText("发送")

    def on_sys_msg(self, text):
        self.chat_display.page().runJavaScript(f"appendSysMsg({json.dumps(text)});")

    def on_start_ai(self):
        self.chat_display.page().runJavaScript("startAiMsg();")

    def on_update_ai(self, accumulated_text):
        text = accumulated_text
        
        # 寻找所有的 [回答] 标签位置
        answer_indices = [m.start() for m in re.finditer(r'\[回答\]', text)]
        
        if not answer_indices:
            # 根本没有 [回答] -> 说明当前全程都在过程（思考/调用工具阶段）
            is_final_answering = False
            process_text = text
            answer_text = ""
        else:
            last_ans_idx = answer_indices[-1]
            after_ans_text = text[last_ans_idx + len('[回答]'):]
            
            # 检查在最后一个 [回答] 之后，是否还有其他的系统级过程标签
            # 如果还有，说明最后的 [回答] 只是大模型在调用工具前输出的中间对话，不是最终结果
            if re.search(r'\[(?:思考|模型决定调用工具|执行工具|工具返回|工具执行完毕，大模型继续生成\.\.\.)\]', after_ans_text):
                is_final_answering = False
                process_text = text  # 所有内容都算作过程
                answer_text = ""
            else:
                # 最后一个 [回答] 后不再有工具和思考标签，说明真正进入了最终的输出阶段
                is_final_answering = True
                process_text = text[:last_ans_idx].strip()
                answer_text = after_ans_text.strip()
                
        # 优化显示：把过程文本里的标签加上 Markdown 粗体，让折叠框里的内容更美观易读
        if process_text:
            process_text = re.sub(r'\[(思考|模型决定调用工具|执行工具|工具返回|工具执行完毕，大模型继续生成\.\.\.)\]', r'**[\1]**', process_text)
            # 中间废弃的 [回答] 改名以防误解
            process_text = re.sub(r'\[(回答)\]', r'**[中间输出]**', process_text)

        # 构建最终注入到前端进行 Markdown 渲染的 HTML 字符串
        final_html = ""
        
        if process_text:
            if is_final_answering:
                final_html += f'<details><summary>⚙️ 思考与工具调用 （已完成）</summary>\n\n{process_text}\n\n</details>\n\n'
            else:
                final_html += f'<details open><summary>⚙️ 正在思考 / 执行工具...</summary>\n\n{process_text}\n\n</details>\n\n'
                
        final_html += answer_text
        
        # 发送给 WebEngine 渲染
        self.chat_display.page().runJavaScript(f"updateAiMsg({json.dumps(final_html)});")

    def on_ai_finished(self):
        self.set_ui_enabled(True)
        self.input_field.setFocus()

    def trigger_heartbeat(self):
        event_queue.put({"type": "heart_beat"})

    def initTray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        icon = QIcon("artificial-intelligence.png") 
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()
        show_action = QAction("显示窗口 (Alt+Z)", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("完全退出", self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def initHotkey(self):
        def on_activate():
            self.hotkey_signal.emit()
        keyboard.add_hotkey('alt+z', on_activate, suppress=True)
        
    def toggle_window(self):
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self.show_window()

    def show_window(self):
        self.showNormal() 
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and not self.is_settings_open:
                self.hide()
        super().changeEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = FloatingWindow()
    window.show_window() 
    
    sys.exit(app.exec_())