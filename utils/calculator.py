"""
计算逻辑模块 — 收益率计算、回本日期查找
"""
import pandas as pd
from typing import Tuple, Optional
from datetime import datetime


def calc_return_rate(df: pd.DataFrame) -> pd.Series:
    """
    计算累计收益率序列

    以查询区间第一天收盘价为基准，
    每日累计收益率 = (当日收盘价 / 基准价 - 1) × 100%

    参数:
        df: 股票历史数据 DataFrame，需包含 date, close 列

    返回:
        pandas Series，索引为 date，值为累计收益率(%)
    """
    if df is None or df.empty:
        return pd.Series(dtype=float)

    base_price = df.iloc[0]['close']
    if base_price <= 0:
        raise ValueError("基准价格无效（≤0）")

    return_rates = (df['close'] / base_price - 1) * 100
    return_rates.index = df['date']
    return return_rates


def calc_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    提取每日关键数据：日期、开盘价、收盘价、涨跌幅

    参数:
        df: 股票历史数据 DataFrame

    返回:
        DataFrame，包含 日期, 开盘价, 收盘价, 涨跌幅(%)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    summary = pd.DataFrame({
        '日期': pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d'),
        '开盘价': df['open'].round(2),
        '收盘价': df['close'].round(2),
    })

    # 计算每日涨跌幅（相对于前一日收盘）
    summary['涨跌幅(%)'] = (df['close'].pct_change() * 100).round(2)
    # 第一条记录的涨跌幅为当日相对开盘的涨跌
    if len(df) > 0:
        first_change = ((df.iloc[0]['close'] - df.iloc[0]['open']) / df.iloc[0]['open'] * 100)
        summary.iloc[0, summary.columns.get_loc('涨跌幅(%)')] = round(first_change, 2)

    return summary


def find_breakeven_date(
    df: pd.DataFrame,
    buy_date: str,
    buy_price: float
) -> dict:
    """
    查找回本日期

    从买入日期开始，逐日比较收盘价，找到第一个收盘价 ≥ 买入价的交易日

    参数:
        df: 股票历史数据 DataFrame，需包含 date, close, open 列
        buy_date: 买入日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'
        buy_price: 买入价格

    返回:
        dict:
        {
            'found': bool,              # 是否找到回本日期
            'buy_date': str,            # 买入日期
            'buy_price': float,         # 买入价格
            'buy_day_close': float,     # 买入当日收盘价
            'buy_day_pct': float,       # 买入当日涨跌幅(%)
            'breakeven_date': str|None, # 回本日期（如找到）
            'breakeven_close': float|None, # 回本当日收盘价
            'days_waited': int|None,    # 等待天数
            'current_loss_pct': float,  # 当前亏损幅度(%)（未回本时）
            'message': str,             # 结果说明
        }
    """
    # 标准化日期格式
    buy_date = buy_date.replace('-', '')[:8]

    # 确保数据中包含所需日期
    df = df.copy()
    df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d')

    # 找到买入日在数据中的位置
    buy_rows = df[df['date_str'] == buy_date]
    if buy_rows.empty:
        raise ValueError(
            f"买入日期 {buy_date[:4]}-{buy_date[4:6]}-{buy_date[6:8]} "
            f"不在数据范围内（数据范围：{df.iloc[0]['date']} ~ {df.iloc[-1]['date']}）\n"
            f"请注意：非交易日（周末/节假日）没有数据"
        )

    buy_idx = buy_rows.index[0]
    buy_day_close = df.loc[buy_idx, 'close']
    buy_day_open = df.loc[buy_idx, 'open']
    buy_day_pct = round((buy_day_close - buy_day_open) / buy_day_open * 100, 2)

    # 从买入日开始往后查找
    future_data = df.loc[buy_idx:]

    result = {
        'found': False,
        'buy_date': f"{buy_date[:4]}-{buy_date[4:6]}-{buy_date[6:8]}",
        'buy_price': round(buy_price, 2),
        'buy_day_close': round(buy_day_close, 2),
        'buy_day_pct': buy_day_pct,
        'breakeven_date': None,
        'breakeven_close': None,
        'days_waited': None,
        'current_loss_pct': round((float(buy_day_close) - buy_price) / buy_price * 100, 2),
        'message': '',
    }

    # 查找回本日期
    breakeven_rows = future_data[future_data['close'] >= buy_price]
    if not breakeven_rows.empty:
        breakeven_idx = breakeven_rows.index[0]
        breakeven_row = df.loc[breakeven_idx]
        days_waited = breakeven_idx - buy_idx

        result['found'] = True
        result['breakeven_date'] = str(breakeven_row['date'])[:10]
        result['breakeven_close'] = round(float(breakeven_row['close']), 2)
        result['days_waited'] = int(days_waited)
        result['message'] = (
            f"买入后第 {days_waited} 个交易日在 "
            f"{result['breakeven_date']} 回本，当日收盘价 ¥{result['breakeven_close']}"
        )
    else:
        # 未回本
        last_row = df.iloc[-1]
        last_close = float(last_row['close'])
        loss_pct = round((last_close - buy_price) / buy_price * 100, 2)
        result['current_loss_pct'] = loss_pct
        result['message'] = (
            f"截至 {str(last_row['date'])[:10]}，尚未回本。"
            f"当前收盘价 ¥{last_close:.2f}，"
            f"相比买入价亏损 {abs(loss_pct):.2f}%"
        )

    return result


def calc_interval_return(df: pd.DataFrame) -> float:
    """
    计算整个查询区间的涨跌幅（用于保存摘要）

    返回:
        区间涨跌幅(%)，如 +8.5 或 -2.1
    """
    if df is None or df.empty or len(df) < 2:
        return 0.0

    first_close = df.iloc[0]['close']
    last_close = df.iloc[-1]['close']
    if first_close <= 0:
        return 0.0

    return round((last_close - first_close) / first_close * 100, 2)
