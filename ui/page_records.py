"""
功能三：我的记录页面（查看保存的查询记录，按年度/月度汇总，支持删除）
"""
import customtkinter as ctk
from tkinter import messagebox
from ui.components import SectionTitle
from data.storage import (
    get_all_records, get_records_by_year, get_records_by_month,
    delete_record, get_yearly_summary, get_monthly_summary,
)
import app as app_module


class RecordsPage(ctk.CTkFrame):
    """我的记录页面"""

    def __init__(self, master, app: 'app_module.App'):
        super().__init__(master, fg_color=app_module.CONTENT_BG, corner_radius=0)
        self._app = app
        self._view_mode = "all"  # all / year / month
        self._selected_year = None

        # 顶部留白
        ctk.CTkFrame(self, height=24, fg_color="transparent").pack(fill="x")

        # ---- 汇总切换 ----
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(0, 12))

        SectionTitle(toolbar, "📁 我的记录").pack(side="left", padx=(0, 20))

        self._view_btn_all = ctk.CTkButton(
            toolbar, text="全部", width=70, height=32,
            font=("Microsoft YaHei", 13),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=lambda: self._switch_view("all"),
        )
        self._view_btn_all.pack(side="left", padx=4)

        self._view_btn_year = ctk.CTkButton(
            toolbar, text="按年度", width=70, height=32,
            font=("Microsoft YaHei", 13),
            fg_color="transparent",
            text_color=app_module.ACCENT_BLUE,
            border_color=app_module.ACCENT_BLUE,
            border_width=1,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=lambda: self._switch_view("year"),
        )
        self._view_btn_year.pack(side="left", padx=4)

        self._refresh_btn = ctk.CTkButton(
            toolbar, text="⟳ 刷新", width=70, height=32,
            font=("Microsoft YaHei", 13),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=8,
            command=self._refresh,
        )
        self._refresh_btn.pack(side="right")

        # ---- 记录列表 ----
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=app_module.CARD_BG,
            label_text="暂无保存的记录",
            label_font=("Microsoft YaHei", 13),
        )
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # 首次加载
        self._refresh()

    def _switch_view(self, mode: str):
        """切换汇总视图"""
        self._view_mode = mode
        # 更新按钮样式
        for btn, m in [(self._view_btn_all, "all"), (self._view_btn_year, "year")]:
            if m == mode:
                btn.configure(fg_color=app_module.ACCENT_BLUE,
                              text_color="white",
                              border_width=0)
            else:
                btn.configure(fg_color="transparent",
                              text_color=app_module.ACCENT_BLUE,
                              border_width=1)
        self._refresh()

    def _refresh(self):
        """刷新记录列表"""
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        if self._view_mode == "all":
            records = get_all_records()
        elif self._view_mode == "year":
            records = get_all_records()
        else:
            records = get_all_records()

        if not records:
            self._list_frame.configure(label_text="暂无保存的记录")
            return

        self._list_frame.configure(label_text="")

        if self._view_mode == "all":
            self._render_all_view(records)
        elif self._view_mode == "year":
            self._render_yearly_view(records)

    def _render_all_view(self, records):
        """平铺视图：按时间倒序列出所有记录"""
        for rec in records:
            self._add_record_row(rec)

    def _render_yearly_view(self, records):
        """树形视图：年度 → 月份 → 记录"""
        # 按年度分组
        years = {}
        for rec in records:
            y = rec['category_year']
            m = rec['category_month']
            if y not in years:
                years[y] = {}
            if m not in years[y]:
                years[y][m] = []
            years[y][m].append(rec)

        for year in sorted(years.keys(), reverse=True):
            # 年度标题
            year_frame = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            year_frame.pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(
                year_frame,
                text=f"📁 {year}年",
                font=("Microsoft YaHei", 16, "bold"),
                text_color=app_module.TEXT_PRIMARY,
            ).pack(anchor="w", padx=8)

            for month in sorted(years[year].keys(), reverse=True):
                # 月份标题
                mon_frame = ctk.CTkFrame(self._list_frame, fg_color="transparent")
                mon_frame.pack(fill="x", pady=(4, 1))
                ctk.CTkLabel(
                    mon_frame,
                    text=f"    📅 {month}月  ({len(years[year][month])} 条)",
                    font=("Microsoft YaHei", 13),
                    text_color=app_module.TEXT_SECONDARY,
                ).pack(anchor="w", padx=8)

                # 记录行
                for rec in years[year][month]:
                    self._add_record_row(rec, indent=True)

    def _add_record_row(self, rec: dict, indent: bool = False):
        """添加一条记录行"""
        row = ctk.CTkFrame(self._list_frame, fg_color="white",
                           corner_radius=6)
        row.pack(fill="x", padx=(30 if indent else 4), pady=2)

        # 股票信息
        info_text = (
            f"{rec['stock_code']}"
            f"  |  {rec['start_date'][:4]}.{rec['start_date'][4:6]}.{rec['start_date'][6:8]}"
            f" ~ {rec['end_date'][:4]}.{rec['end_date'][4:6]}.{rec['end_date'][6:8]}"
        )
        ctk.CTkLabel(
            row, text=info_text,
            font=("Microsoft YaHei", 13),
            text_color=app_module.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", padx=12, pady=6, fill="x", expand=True)

        # 收益率
        ret = rec['return_pct']
        color = app_module.SUCCESS_GREEN if ret >= 0 else app_module.DANGER_RED
        ctk.CTkLabel(
            row, text=f"{ret:+.2f}%",
            font=("Microsoft YaHei", 14, "bold"),
            text_color=color,
            width=80, anchor="center",
        ).pack(side="left", padx=4)

        # 查看按钮 → 跳转功能一
        ctk.CTkButton(
            row, text="查看", width=50, height=28,
            font=("Microsoft YaHei", 12),
            fg_color=app_module.ACCENT_BLUE,
            hover_color=app_module.ACCENT_HOVER,
            corner_radius=6,
            command=lambda r=rec: self._on_view(r),
        ).pack(side="left", padx=2)

        # 删除按钮
        ctk.CTkButton(
            row, text="🗑", width=36, height=28,
            font=("Microsoft YaHei", 12),
            fg_color=app_module.DANGER_RED,
            hover_color="#C0392B",
            corner_radius=6,
            command=lambda r=rec: self._on_delete(r['id']),
        ).pack(side="left", padx=(2, 8))

    def _on_view(self, rec: dict):
        """点击查看 → 跳转功能一回显"""
        self._app.navigate_to_return(
            stock_code=rec['stock_code'],
            start_date=rec['start_date'],
            end_date=rec['end_date'],
        )

    def _on_delete(self, record_id: int):
        """删除一条记录"""
        result = messagebox.askyesno(
            "确认删除",
            "确定要删除这条查询记录吗？\n此操作不可撤销。"
        )
        if result:
            delete_record(record_id)
            self._refresh()
