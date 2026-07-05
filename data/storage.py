"""
本地存储层 — SQLite 数据库操作
保存、查询、删除用户的查询记录，按年度/月度汇总
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# 数据库文件路径（在 data 目录下）
DB_PATH = os.path.join(os.path.dirname(__file__), 'records.db')


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建目录和表）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果支持列名访问
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code      TEXT    NOT NULL,   -- 股票代码，如 '600519'
            stock_name      TEXT    DEFAULT '',  -- 股票名称，如 '贵州茅台'
            start_date      TEXT    NOT NULL,   -- 查询起始日期 'YYYYMMDD'
            end_date        TEXT    NOT NULL,   -- 查询结束日期 'YYYYMMDD'
            return_pct      REAL    DEFAULT 0,   -- 区间涨跌幅(%)
            category_year   INTEGER NOT NULL,   -- 归类年度（取自 start_date）
            category_month  INTEGER NOT NULL,   -- 归类月份（取自 start_date）
            created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()


def save_record(
    stock_code: str,
    stock_name: str,
    start_date: str,
    end_date: str,
    return_pct: float
) -> int:
    """
    保存一条查询记录

    返回:
        新记录的 ID
    """
    # 从起始日期提取年度和月份
    start_date = start_date.replace('-', '')[:8]
    category_year = int(start_date[:4])
    category_month = int(start_date[4:6])

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO saved_records
            (stock_code, stock_name, start_date, end_date, return_pct,
             category_year, category_month)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (stock_code, stock_name, start_date, end_date, return_pct,
          category_year, category_month))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_all_records() -> List[Dict]:
    """获取所有保存的记录，按时间倒序"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM saved_records
        ORDER BY category_year DESC, category_month DESC, created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_records_by_year(year: int) -> List[Dict]:
    """按年度筛选记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM saved_records
        WHERE category_year = ?
        ORDER BY category_month DESC, created_at DESC
    ''', (year,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_records_by_month(year: int, month: int) -> List[Dict]:
    """按年度+月份筛选记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM saved_records
        WHERE category_year = ? AND category_month = ?
        ORDER BY created_at DESC
    ''', (year, month))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_record(record_id: int) -> bool:
    """
    删除一条记录

    返回:
        True 删除成功，False 记录不存在
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saved_records WHERE id = ?', (record_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_yearly_summary() -> List[Dict]:
    """按年度汇总：每年有多少条记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category_year, COUNT(*) as count
        FROM saved_records
        GROUP BY category_year
        ORDER BY category_year DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_monthly_summary(year: int) -> List[Dict]:
    """按月度汇总：某年各月有多少条记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category_month, COUNT(*) as count
        FROM saved_records
        WHERE category_year = ?
        GROUP BY category_month
        ORDER BY category_month DESC
    ''', (year,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_record_by_id(record_id: int) -> Optional[Dict]:
    """根据 ID 获取单条记录"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saved_records WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# 启动时自动初始化
init_db()
