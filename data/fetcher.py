"""
数据获取层 — 封装 akshare，提供股票数据查询和搜索功能
使用新浪财经 API（稳定、无需代理）
"""
import akshare as ak
import pandas as pd
from typing import Optional, Tuple, List


# ---- 内部工具 ----

def _code_to_symbol(code: str) -> str:
    """将纯数字代码转换为新浪格式（sh/sz 前缀）"""
    code = code.strip()
    if code.startswith(('sh', 'sz', 'bj')):
        return code  # 已经是带前缀的格式
    if code.startswith(('6', '9')):
        return f'sh{code}'
    elif code.startswith(('0', '2', '3')):
        return f'sz{code}'
    elif code.startswith('8'):
        return f'bj{code}'
    else:
        raise ValueError(f"无法识别的股票代码前缀: {code}")


# ---- 公开接口 ----

def get_stock_data(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取 A 股历史日 K 线数据（前复权）

    参数:
        code: 股票代码，如 '600519' 或 'sh600519'
        start_date: 起始日期，格式 'YYYYMMDD'，如 '20250101'
        end_date: 结束日期，格式 'YYYYMMDD'，如 '20250630'

    返回:
        pandas DataFrame，列名（英文）:
            date, open, high, low, close, volume, amount,
            outstanding_share, turnover

    异常:
        ValueError: 股票代码不存在或日期无效
        ConnectionError: 网络请求失败
    """
    try:
        symbol = _code_to_symbol(code)

        df = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'  # 前复权
        )

        # 检查返回数据是否有效
        if df is None or df.empty or 'date' not in df.columns:
            raise ValueError(
                f"未找到股票 {code} 在 {start_date} 至 {end_date} 期间的数据。\n"
                f"请确认：1) 股票代码正确  2) 日期在交易日内  3) 结束日期不早于起始日期"
            )

        return df

    except ValueError:
        raise
    except KeyError:
        raise ValueError(
            f"股票代码 '{code}' 似乎不存在，请检查后重试"
        )
    except Exception as e:
        import traceback
        error_msg = str(e)
        detail = traceback.format_exc()
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            raise ConnectionError(f"网络连接失败，请检查网络后重试\n\n详细信息：\n{detail}")
        else:
            raise RuntimeError(f"获取数据时出错：{error_msg}\n\n详细信息：\n{detail}")


def search_stock(keyword: str) -> List[Tuple[str, str]]:
    """
    根据关键词搜索股票代码和名称

    参数:
        keyword: 搜索关键词，如 '茅台' 或 '600519'

    返回:
        [(代码, 名称), ...] 列表，如 [('600519', '贵州茅台')]
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    results = []

    # 策略：使用新浪的股票列表接口（akshare 封装）
    try:
        # stock_info_a_code_name 下载全量 A 股列表
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            code_col = 'code' if 'code' in df.columns else df.columns[0]
            name_col = 'name' if 'name' in df.columns else df.columns[1]

            # 模糊匹配
            mask = (
                df[code_col].astype(str).str.contains(keyword, na=False) |
                df[name_col].astype(str).str.contains(keyword, na=False)
            )
            matched = df[mask]
            for _, row in matched.iterrows():
                results.append((str(row[code_col]), str(row[name_col])))
    except Exception:
        pass

    return results[:20]


def validate_stock_code(code: str) -> Tuple[bool, str]:
    """
    快速验证股票代码是否有效

    返回:
        (是否有效, 股票名称或错误信息)
    """
    code = code.strip()
    try:
        # 尝试获取最近一个交易日的数据
        symbol = _code_to_symbol(code)
        # 用最近日期尝试
        import datetime
        today = datetime.date.today()
        end_str = today.strftime('%Y%m%d')
        start_str = (today - datetime.timedelta(days=7)).strftime('%Y%m%d')

        df = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date=start_str,
            end_date=end_str,
            adjust='qfq'
        )
        if df is not None and not df.empty:
            return True, code  # 有效
        return False, f"未找到股票代码 {code}"
    except Exception as e:
        return False, str(e)
