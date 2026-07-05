"""
功能二：回本计算器页面
"""
import customtkinter as ctk
import pandas as pd
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.components import DatePicker, SectionTitle
from data.fetcher import get_stock_data
from utils.calculator import find_breakeven_date
import app as app_module


class RecoveryPage(ctk.CTkFrame):
    """回本计算器页面"""

    def __init__(self, master, app: 'app_module.App'):
        super().__init__(master, fg_color=app_module.CONTENT_BG, corner_radius=0)
        self._app = app

        # 顶部留白
        ctk.CTkFrame(self, height=24, fg_color="transparent").pack(fill="x")

        # ---- 输入区域 ----
        input_card = ctk.CTkFrame(self, fg_color=app_module.CARD_BG,
                                  corner_radius=10)
        input_card.pack(fill="x", padx=24, pady=(0, 16))

        row1 = ctk.CTkFrame(input_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(16, 8))

        SectionTitle(row1, "股票").pack(side="left", padx=(0, 10))
        self._code_entry = ctk.CTkEntry(
            row1, placeholder_text="输入股票代码，如 600519",
            height=38, width=200,
            font=("Microsoft YaHei", 14),
            border_color=app_module.BORDER_COLOR,
            fg_color="#FFFFFF",
        )
        self._code_entry.pack(side="left", padx=(0, 20))

        SectionTitle(row1, "买入日期").pack(side="left", padx=(0, 10))
        self._date_picker = DatePicker(row1)
        self._date_picker.pack(side="left", padx=(0, 20))

        SectionTitle(row1, "买入价格").pack(side="left", padx=(0, 10))
        self._price_entry = ctk.CTkEntry(
            row1, placeholder_text="如 1400.00",
            height=38, width=100,
            font=("Microsoft YaHei", 14),
            border_color=app_module.BORDER_COLOR,
            fg_color="#FFFFFF",
        )
        self._price_entry.pack(side="left", padx=(0, 16))

        self._calc_btn = ctk.CTkButton(
            row1, text="计算",
            width=80, height=38,
            font=("Microsoft YaHei", 14, "bold"),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=self._on_calculate,
        )
        self._calc_btn.pack(side="left")

        # 状态提示
        self._status_label = ctk.CTkLabel(
            input_card, text="",
            font=("Microsoft YaHei", 12),
            text_color=app_module.TEXT_SECONDARY,
        )
        self._status_label.pack(padx=20, pady=(0, 16), anchor="w")

        # ---- 结果区 ----
        result_frame = ctk.CTkFrame(self, fg_color="transparent")
        result_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_columnconfigure(1, weight=1)

        # 左侧：结果卡片
        self._result_card = ctk.CTkFrame(result_frame, fg_color=app_module.CARD_BG,
                                         corner_radius=10)
        self._result_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        SectionTitle(self._result_card, "计算结果").pack(pady=(12, 8), padx=16)

        self._result_labels = {}
        fields = [
            ("买入成本", "¥ --"),
            ("买入当日收盘", "--"),
            ("当日涨跌", "--"),
            ("回本日期", "--"),
            ("等待天数", "--"),
            ("回本收盘价", "--"),
        ]
        for label, default in fields:
            row = ctk.CTkFrame(self._result_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=("Microsoft YaHei", 13),
                         text_color=app_module.TEXT_SECONDARY,
                         width=90, anchor="w").pack(side="left")
            val = ctk.CTkLabel(row, text=default,
                               font=("Microsoft YaHei", 15, "bold"),
                               text_color=app_module.TEXT_PRIMARY)
            val.pack(side="left")
            self._result_labels[label] = val

        # 右侧：图表
        self._chart_card = ctk.CTkFrame(result_frame, fg_color=app_module.CARD_BG,
                                        corner_radius=10)
        self._chart_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        SectionTitle(self._chart_card, "价格走势").pack(pady=(12, 0))
        self._chart_frame = ctk.CTkFrame(self._chart_card, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True, padx=8, pady=8)
        # 占位符
        ctk.CTkLabel(self._chart_frame, text="输入数据后点击「计算」查看走势图",
                     font=("Microsoft YaHei", 13),
                     text_color=app_module.TEXT_SECONDARY).pack(expand=True)

    def _on_calculate(self):
        code = self._code_entry.get().strip()
        price_str = self._price_entry.get().strip()
        buy_date = self._date_picker.get_date()

        if not code:
            self._set_status("请输入股票代码", app_module.DANGER_RED)
            return
        if not price_str:
            self._set_status("请输入买入价格", app_module.DANGER_RED)
            return
        try:
            buy_price = float(price_str)
        except ValueError:
            self._set_status("买入价格格式不正确，请输入数字", app_module.DANGER_RED)
            return

        self._set_status("正在计算...", app_module.ACCENT_BLUE)
        self._calc_btn.configure(state="disabled")

        def task():
            try:
                # 获取从买入日期到最近的数据
                import datetime
                today = datetime.date.today()
                end_str = today.strftime('%Y%m%d')
                # 确保查询范围包含买入日期
                start_str = buy_date

                df = get_stock_data(code, start_str, end_str)
                result = find_breakeven_date(df, buy_date, buy_price)
                self.after(0, lambda: self._show_result(result, df))
            except Exception as e:
                self.after(0, lambda: self._set_status(str(e), app_module.DANGER_RED))
                self.after(0, lambda: self._calc_btn.configure(state="normal"))

        threading.Thread(target=task, daemon=True).start()

    def _show_result(self, result: dict, df):
        self._calc_btn.configure(state="normal")

        # 更新结果卡片
        self._result_labels["买入成本"].configure(
            text=f"¥ {result['buy_price']:.2f}")
        self._result_labels["买入当日收盘"].configure(
            text=f"¥ {result['buy_day_close']:.2f}")

        pct = result['buy_day_pct']
        color = app_module.SUCCESS_GREEN if pct >= 0 else app_module.DANGER_RED
        self._result_labels["当日涨跌"].configure(
            text=f"{pct:+.2f}%", text_color=color)

        if result['found']:
            self._result_labels["回本日期"].configure(
                text=result['breakeven_date'],
                text_color=app_module.SUCCESS_GREEN)
            self._result_labels["等待天数"].configure(
                text=f"{result['days_waited']} 个交易日")
            self._result_labels["回本收盘价"].configure(
                text=f"¥ {result['breakeven_close']:.2f}",
                text_color=app_module.SUCCESS_GREEN)
            self._set_status(result['message'], app_module.SUCCESS_GREEN)
        else:
            self._result_labels["回本日期"].configure(
                text="尚未回本", text_color=app_module.DANGER_RED)
            self._result_labels["等待天数"].configure(text="--")
            self._result_labels["回本收盘价"].configure(text="--")
            self._set_status(result['message'], app_module.DANGER_RED)

        # 绘制价格走势图
        self._draw_chart(df, result)

    def _draw_chart(self, df, result: dict):
        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        # 转换为 datetime 对象，matplotlib 才能正确处理日期轴
        dates = pd.to_datetime(df['date']).tolist()
        closes = df['close'].tolist()

        ax.plot(dates, closes, color=app_module.ACCENT_BLUE, linewidth=1.2,
                label='收盘价')

        # 买入价格水平线
        ax.axhline(y=result['buy_price'], color=app_module.DANGER_RED,
                   linestyle='--', linewidth=0.8, alpha=0.7,
                   label=f"买入价 ¥{result['buy_price']:.2f}")

        # 标记买点
        buy_date_str = result['buy_date']  # 'YYYY-MM-DD'
        buy_dt = pd.to_datetime(buy_date_str)
        if buy_dt in dates:
            idx = dates.index(buy_dt)
            ax.scatter([dates[idx]], [closes[idx]], color=app_module.DANGER_RED,
                       s=80, zorder=5, marker='v', label='买入日')

        # 标记回本点
        if result['found'] and result['breakeven_date']:
            be_dt = pd.to_datetime(result['breakeven_date'])
            if be_dt in dates:
                idx = dates.index(be_dt)
                ax.scatter([dates[idx]], [closes[idx]],
                           color=app_module.SUCCESS_GREEN,
                           s=100, zorder=5, marker='o', label='回本日')

        ax.set_title("价格走势图", fontsize=12, fontfamily='Microsoft YaHei')
        ax.tick_params(axis='x', rotation=30, labelsize=8)
        ax.tick_params(axis='y', labelsize=9)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _set_status(self, text: str, color: str):
        self._status_label.configure(text=text, text_color=color)
