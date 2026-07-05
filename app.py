"""
主窗口 + 导航框架 — 蓝白配色，左侧导航，右侧内容区
"""
import customtkinter as ctk
from typing import Optional


# ---- 设计规范常量 ----
SIDEBAR_BG = "#1B2838"       # 深蓝（左侧导航背景）
SIDEBAR_WIDTH = 200           # 导航栏宽度
CONTENT_BG = "#F5F7FA"       # 浅灰白（内容区背景）
CARD_BG = "#FFFFFF"          # 纯白（卡片背景）
ACCENT_BLUE = "#2E86DE"      # 蓝色（按钮、强调）
ACCENT_HOVER = "#1E6FBF"     # 深蓝（悬停态）
TEXT_PRIMARY = "#2C3E50"     # 深灰蓝（主文字）
TEXT_SECONDARY = "#7F8C8D"   # 灰色（辅助文字）
BORDER_COLOR = "#E0E4E8"     # 浅灰（边框）
SUCCESS_GREEN = "#27AE60"    # 绿色（正收益）
DANGER_RED = "#E74C3C"       # 红色（负收益、删除）
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
MIN_WIDTH = 900
MIN_HEIGHT = 600


class App(ctk.CTk):
    """主应用程序"""

    def __init__(self):
        super().__init__()

        # 窗口基本设置
        self.title("股票分析软件")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # 主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 全局网格布局（1行2列）
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- 左侧导航栏 ----
        self._build_sidebar()

        # ---- 右侧内容区 ----
        self._content_frame = ctk.CTkFrame(self, fg_color=CONTENT_BG, corner_radius=0)
        self._content_frame.grid(row=0, column=1, sticky="nsew")
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

        # 页面引用（延迟导入，避免循环依赖）
        self._pages = {}
        self._current_page = None

        # 默认显示功能一
        self._show_page("return")

    def _build_sidebar(self):
        """构建左侧导航栏"""
        sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, fg_color=SIDEBAR_BG,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        # Logo / 标题
        ctk.CTkLabel(
            sidebar, text="📈 股票分析",
            font=("Microsoft YaHei", 18, "bold"),
            text_color="#FFFFFF",
        ).pack(pady=(30, 40))

        # 导航按钮
        self._nav_buttons = {}
        nav_items = [
            ("return", "📊  收益率查询"),
            ("recovery", "💰  回本计算"),
            ("records", "📁  我的记录"),
        ]

        self._nav_indicator = ctk.CTkFrame(
            sidebar, width=4, height=44, fg_color=ACCENT_BLUE
        )

        for page_key, label in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=("Microsoft YaHei", 14),
                fg_color="transparent",
                text_color="#FFFFFF",
                hover_color="rgba(255,255,255,0.1)",
                anchor="w",
                height=44,
                corner_radius=0,
                command=lambda k=page_key: self._show_page(k),
            )
            btn.pack(fill="x", padx=0, pady=2)
            self._nav_buttons[page_key] = btn

    def _show_page(self, page_key: str):
        """切换页面"""
        # 更新导航按钮样式
        for key, btn in self._nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=ACCENT_BLUE, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#FFFFFF")

        # 移除旧页面
        if self._current_page:
            self._current_page.pack_forget()

        # 创建/显示新页面（延迟导入）
        if page_key not in self._pages:
            if page_key == "return":
                from ui.page_return import ReturnPage
                self._pages[page_key] = ReturnPage(self._content_frame, self)
            elif page_key == "recovery":
                from ui.page_recovery import RecoveryPage
                self._pages[page_key] = RecoveryPage(self._content_frame, self)
            elif page_key == "records":
                from ui.page_records import RecordsPage
                self._pages[page_key] = RecordsPage(self._content_frame, self)

        page = self._pages[page_key]
        page.pack(fill="both", expand=True)
        self._current_page = page

    def navigate_to_return(self, stock_code: str = "", start_date: str = "",
                           end_date: str = ""):
        """跳转到功能一页面，可选回显查询条件"""
        self._show_page("return")
        page = self._pages.get("return")
        if page and stock_code:
            page.restore_query(stock_code, start_date, end_date)
