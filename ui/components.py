"""
可复用 UI 组件 — 日期选择器、股票搜索框等
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Callable, Optional


class DatePicker(ctk.CTkFrame):
    """简单的日期选择器（年/月/日下拉框）"""

    def __init__(self, master, label: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_text = label
        now = datetime.now()

        # 标签
        if label:
            self._label = ctk.CTkLabel(self, text=label, font=("Microsoft YaHei", 14))
            self._label.pack(side="left", padx=(0, 6))

        # 年份下拉
        self._year_var = ctk.StringVar(value=str(now.year))
        years = [str(y) for y in range(now.year - 5, now.year + 1)]
        self._year_combo = ctk.CTkComboBox(
            self, values=years, variable=self._year_var,
            width=75, height=32, font=("Microsoft YaHei", 13)
        )
        self._year_combo.pack(side="left", padx=2)

        ctk.CTkLabel(self, text="年", font=("Microsoft YaHei", 13)).pack(side="left")

        # 月份下拉
        self._month_var = ctk.StringVar(value=str(now.month).zfill(2))
        months = [str(m).zfill(2) for m in range(1, 13)]
        self._month_combo = ctk.CTkComboBox(
            self, values=months, variable=self._month_var,
            width=55, height=32, font=("Microsoft YaHei", 13)
        )
        self._month_combo.pack(side="left", padx=2)

        ctk.CTkLabel(self, text="月", font=("Microsoft YaHei", 13)).pack(side="left")

        # 日期下拉
        self._day_var = ctk.StringVar(value=str(now.day).zfill(2))
        self._update_days()
        self._day_combo = ctk.CTkComboBox(
            self, values=self._days_list, variable=self._day_var,
            width=55, height=32, font=("Microsoft YaHei", 13)
        )
        self._day_combo.pack(side="left", padx=2)

        ctk.CTkLabel(self, text="日", font=("Microsoft YaHei", 13)).pack(side="left")

        # 绑定月份/年份变化事件
        self._year_combo.configure(command=self._on_change)
        self._month_combo.configure(command=self._on_change)

    def _update_days(self):
        """根据年月更新天数列表"""
        try:
            y = int(self._year_var.get())
            m = int(self._month_var.get())
            import calendar
            days = calendar.monthrange(y, m)[1]
            self._days_list = [str(d).zfill(2) for d in range(1, days + 1)]
        except (ValueError, ImportError):
            self._days_list = [str(d).zfill(2) for d in range(1, 31)]

    def _on_change(self, *args):
        """年月变化时更新天数"""
        self._update_days()
        current_day = self._day_var.get()
        if current_day not in self._days_list:
            self._day_var.set(self._days_list[-1])
        self._day_combo.configure(values=self._days_list)

    def get_date(self) -> str:
        """获取日期，格式 'YYYYMMDD'"""
        return f"{self._year_var.get()}{self._month_var.get()}{self._day_var.get()}"

    def set_date(self, date_str: str):
        """设置日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'"""
        date_str = date_str.replace('-', '')[:8]
        if len(date_str) >= 8:
            self._year_var.set(date_str[:4])
            self._month_var.set(date_str[4:6])
            self._update_days()
            day = date_str[6:8]
            if day in self._days_list:
                self._day_var.set(day)
            self._day_combo.configure(values=self._days_list)


class StockSearchBar(ctk.CTkFrame):
    """股票搜索输入框 + 查询按钮"""

    def __init__(self, master, on_search: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_search = on_search

        # 输入框
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="输入股票代码或名称，如 600519 或 贵州茅台",
            height=38,
            font=("Microsoft YaHei", 14),
            border_color="#E0E4E8",
            fg_color="#FFFFFF",
            text_color="#2C3E50",
            width=280,
        )
        self._entry.pack(side="left", padx=(0, 8))

        # 查询按钮
        self._btn = ctk.CTkButton(
            self,
            text=" 查询",
            width=80, height=38,
            font=("Microsoft YaHei", 14, "bold"),
            fg_color="#2E86DE",
            hover_color="#1E6FBF",
            corner_radius=8,
            command=self._on_click,
        )
        self._btn.pack(side="left")

        # 绑定回车键
        self._entry.bind("<Return>", lambda e: self._on_click())

    def _on_click(self):
        if self._on_search:
            self._on_search(self.get_text())

    def get_text(self) -> str:
        return self._entry.get().strip()

    def set_text(self, text: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, text)

    def set_state(self, state: str):
        """设置按钮状态 'normal' / 'disabled'"""
        self._btn.configure(state=state)


class SectionTitle(ctk.CTkLabel):
    """区块标题组件"""
    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master, text=text,
            font=("Microsoft YaHei", 16, "bold"),
            text_color="#1B2838",
            **kwargs
        )
