"""
功能一：收益率查询页面
"""
import customtkinter as ctk
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.components import DatePicker, StockSearchBar, SectionTitle
from data.fetcher import get_stock_data
from data.storage import save_record
from utils.calculator import calc_return_rate, calc_daily_summary, calc_interval_return
import app as app_module


class ReturnPage(ctk.CTkFrame):
    """收益率查询页面"""

    def __init__(self, master, app: 'app_module.App'):
        super().__init__(master, fg_color=app_module.CONTENT_BG, corner_radius=0)
        self._app = app
        self._df = None  # 当前查询结果

        # 顶部留白
        ctk.CTkFrame(self, height=24, fg_color="transparent").pack(fill="x")

        # ---- 查询区域 ----
        query_frame = ctk.CTkFrame(self, fg_color=app_module.CARD_BG,
                                   corner_radius=10)
        query_frame.pack(fill="x", padx=24, pady=(0, 16))

        # 第一行：股票搜索
        row1 = ctk.CTkFrame(query_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(16, 8))
        SectionTitle(row1, "股票").pack(side="left", padx=(0, 12))
        self._search_bar = StockSearchBar(row1, on_search=self._on_query)
        self._search_bar.pack(side="left")

        # 第二行：日期范围 + 查询按钮
        row2 = ctk.CTkFrame(query_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(8, 8))
        SectionTitle(row2, "时间").pack(side="left", padx=(0, 10))
        self._start_picker = DatePicker(row2, label="起始")
        self._start_picker.pack(side="left", padx=(0, 16))
        self._end_picker = DatePicker(row2, label="结束")
        self._end_picker.pack(side="left", padx=(0, 16))

        self._query_btn = ctk.CTkButton(
            row2, text="查询",
            width=80, height=38,
            font=("Microsoft YaHei", 14, "bold"),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=self._on_query_click,
        )
        self._query_btn.pack(side="left")

        # 状态提示
        self._status_label = ctk.CTkLabel(
            query_frame, text="",
            font=("Microsoft YaHei", 12),
            text_color=app_module.TEXT_SECONDARY,
        )
        self._status_label.pack(padx=20, pady=(0, 16), anchor="w")

        # ---- 内容区域（图表 + 表格 左右分栏） ----
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        content_frame.grid_columnconfigure(0, weight=6)  # 图表占 60%
        content_frame.grid_columnconfigure(1, weight=4)  # 表格占 40%
        content_frame.grid_rowconfigure(0, weight=1)

        # 左侧：图表
        chart_card = ctk.CTkFrame(content_frame, fg_color=app_module.CARD_BG,
                                  corner_radius=10)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        SectionTitle(chart_card, "收益率曲线").pack(pady=(12, 0))
        self._chart_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # 右侧：表格
        table_card = ctk.CTkFrame(content_frame, fg_color=app_module.CARD_BG,
                                  corner_radius=10)
        table_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        SectionTitle(table_card, "每日数据").pack(pady=(12, 0))

        # 表格滚动区域
        self._table_frame = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent",
            label_text="请先查询一只股票",
            label_font=("Microsoft YaHei", 12),
        )
        self._table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- 底部：保存按钮 ----
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=24, pady=(0, 24))
        self._save_btn = ctk.CTkButton(
            bottom_frame, text="💾 保存此次查询",
            width=140, height=36,
            font=("Microsoft YaHei", 13),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=self._on_save,
            state="disabled",
        )
        self._save_btn.pack(side="left")

    # ---- 查询逻辑 ----

    def _on_query_click(self):
        keyword = self._search_bar.get_text()
        if not keyword:
            self._set_status("请输入股票代码或名称", "red")
            return
        self._on_query(keyword)

    def _on_query(self, keyword: str):
        """执行查询（在线程中）"""
        start = self._start_picker.get_date()
        end = self._end_picker.get_date()

        if start > end:
            self._set_status("起始日期不能晚于结束日期", "red")
            return

        self._set_status("正在获取数据...", app_module.ACCENT_BLUE)
        self._query_btn.configure(state="disabled")
        self._save_btn.configure(state="disabled")

        def task():
            try:
                df = get_stock_data(keyword, start, end)
                self._df = df
                self.after(0, lambda: self._render_data(df))
            except Exception as e:
                self.after(0, lambda: self._set_status(str(e), app_module.DANGER_RED))
                self.after(0, lambda: self._query_btn.configure(state="normal"))

        threading.Thread(target=task, daemon=True).start()

    def _render_data(self, df):
        """渲染图表和表格"""
        self._query_btn.configure(state="normal")
        self._save_btn.configure(state="normal")

        # 收益率曲线
        self._draw_chart(df)

        # 数据表格
        self._draw_table(df)

        # 状态
        total_ret = calc_interval_return(df)
        color = app_module.SUCCESS_GREEN if total_ret >= 0 else app_module.DANGER_RED
        self._set_status(
            f"查询完成 | 区间涨跌幅: {total_ret:+.2f}% | "
            f"共 {len(df)} 个交易日",
            color
        )

        self._search_bar.set_state("normal")

    def _draw_chart(self, df):
        """绘制收益率曲线"""
        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(6, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        ret = calc_return_rate(df)
        n = len(ret)
        # 用整数索引作为 X 轴位置，避免 matplotlib 日期解析的各种坑
        x = list(range(n))
        # 日期标签（字符串，只取 YYYY-MM-DD 部分）
        date_labels = [str(d)[:10] for d in df['date']]

        ax.plot(x, ret.values, color=app_module.ACCENT_BLUE, linewidth=1.5)
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.fill_between(x, 0, ret.values,
                        color=app_module.ACCENT_BLUE, alpha=0.1)

        # 设置 X 轴刻度：控制标签数量，避免重叠
        max_ticks = 12
        step = max(1, n // max_ticks)
        tick_positions = x[::step]
        tick_labels = [date_labels[i] for i in tick_positions]
        # 始终包含最后一个日期
        if tick_positions[-1] != n - 1:
            tick_positions.append(n - 1)
            tick_labels.append(date_labels[-1])

        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=30, ha='right', fontsize=8)

        ax.set_title("累计收益率 (%)", fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_xlabel("")
        ax.tick_params(axis='y', labelsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.5, n - 0.5)  # 左右留一点边距
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_table(self, df):
        """绘制数据表格"""
        for widget in self._table_frame.winfo_children():
            widget.destroy()

        summary = calc_daily_summary(df)

        # 表头
        header_frame = ctk.CTkFrame(self._table_frame, fg_color="#EBF0F7",
                                    corner_radius=4)
        header_frame.pack(fill="x", pady=(0, 2))
        for col, w in [("日期", 90), ("开盘价", 70), ("收盘价", 70), ("涨跌幅(%)", 70)]:
            ctk.CTkLabel(header_frame, text=col, width=w,
                         font=("Microsoft YaHei", 12, "bold"),
                         text_color=app_module.TEXT_PRIMARY,
                         anchor="center").pack(side="left", padx=1)

        # 数据行（最多显示 60 行）
        for i, (_, row) in enumerate(summary.iterrows()):
            if i >= 60:
                break
            row_frame = ctk.CTkFrame(self._table_frame, fg_color="white",
                                     corner_radius=2)
            row_frame.pack(fill="x")

            change = row['涨跌幅(%)']
            change_color = app_module.SUCCESS_GREEN if change >= 0 else app_module.DANGER_RED
            change_text = f"{change:+.2f}"

            cells = [
                (row['日期'], app_module.TEXT_PRIMARY),
                (f"{row['开盘价']:.2f}", app_module.TEXT_PRIMARY),
                (f"{row['收盘价']:.2f}", app_module.TEXT_PRIMARY),
                (change_text, change_color),
            ]
            for text, color in cells:
                ctk.CTkLabel(row_frame, text=text, width=70,
                             font=("Microsoft YaHei", 12),
                             text_color=color, anchor="center"
                             ).pack(side="left", padx=1)

    def _on_save(self):
        """保存此次查询"""
        if self._df is None:
            return

        keyword = self._search_bar.get_text()
        start = self._start_picker.get_date()
        end = self._end_picker.get_date()
        total_ret = calc_interval_return(self._df)

        try:
            record_id = save_record(
                stock_code=keyword,
                stock_name=keyword,  # 暂用代码代替，后续可优化为获取真实名称
                start_date=start,
                end_date=end,
                return_pct=total_ret,
            )
            self._set_status(f"已保存到「我的记录」（记录ID: {record_id}）",
                             app_module.SUCCESS_GREEN)
        except Exception as e:
            self._set_status(f"保存失败: {e}", app_module.DANGER_RED)

    def _set_status(self, text: str, color: str):
        self._status_label.configure(text=text, text_color=color)

    def restore_query(self, stock_code: str, start_date: str, end_date: str):
        """从「我的记录」回显查询条件"""
        self._search_bar.set_text(stock_code)
        self._start_picker.set_date(start_date)
        self._end_picker.set_date(end_date)
        # 自动执行查询
        self._on_query(stock_code)
