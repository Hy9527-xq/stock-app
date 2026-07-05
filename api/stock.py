"""
Vercel Serverless Function — 代理新浪财经 API
绕过 CORS，并对数据做预处理
"""
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

SINA_KLINE_URL = (
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "CN_MarketData.getKLineData"
)


def fetch_kline(symbol: str, datalen: int = 300):
    """从新浪获取日K线数据"""
    params = urllib.parse.urlencode({
        'symbol': symbol,
        'scale': '240',       # 日线
        'ma': 'no',
        'datalen': str(datalen),
    })
    url = f"{SINA_KLINE_URL}?{params}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://finance.sina.com.cn/',
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data


def code_to_symbol(code: str) -> str:
    """纯数字代码 → 新浪格式"""
    code = code.strip()
    if code.startswith(('sh', 'sz', 'bj')):
        return code
    if code.startswith(('6', '9')):
        return f'sh{code}'
    elif code.startswith(('0', '2', '3')):
        return f'sz{code}'
    elif code.startswith('8'):
        return f'bj{code}'
    return f'sh{code}'


def calc_return_rates(rows):
    """计算累计收益率序列"""
    if not rows:
        return [], [], []
    base = float(rows[0]['close'])
    dates, rates, closes = [], [], []
    for r in rows:
        dates.append(r['day'])
        c = float(r['close'])
        closes.append(round(c, 2))
        rates.append(round((c / base - 1) * 100, 2))
    return dates, rates, closes


def calc_daily_table(rows):
    """生成每日明细表"""
    result = []
    prev_close = None
    for r in rows:
        o = float(r['open'])
        c = float(r['close'])
        if prev_close is not None:
            change = round((c - prev_close) / prev_close * 100, 2)
        else:
            change = round((c - o) / o * 100, 2)
        prev_close = c
        result.append({
            'date': r['day'],
            'open': round(o, 2),
            'close': round(c, 2),
            'change': change,
        })
    return result


def find_breakeven(rows, buy_price):
    """查找回本日期"""
    buy_price = float(buy_price)
    for i, r in enumerate(rows):
        close = float(r['close'])
        if close >= buy_price:
            return {
                'found': True,
                'breakeven_date': r['day'],
                'breakeven_close': round(close, 2),
                'days_waited': i,
            }
    last_close = float(rows[-1]['close']) if rows else 0
    return {
        'found': False,
        'breakeven_date': None,
        'breakeven_close': None,
        'days_waited': None,
        'last_close': round(last_close, 2),
        'loss_pct': round((last_close - buy_price) / buy_price * 100, 2) if buy_price else 0,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel Python Runtime handler"""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        action = parsed.path.rstrip('/').split('/')[-1]

        if action == 'query':
            self.handle_query(params)
        elif action == 'search':
            self.handle_search(params)
        else:
            self.send_json({'error': '未知操作'}, 400)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path.endswith('/query'):
            self.handle_query(body)
        elif parsed.path.endswith('/recovery'):
            self.handle_recovery(body)
        else:
            self.send_json({'error': '未知操作'}, 400)

    def handle_query(self, params):
        code = params.get('code', [''])[0] if isinstance(params, dict) else params.get('code', '')
        start = params.get('start', [''])[0] if isinstance(params, dict) else params.get('start', '')
        end = params.get('end', [''])[0] if isinstance(params, dict) else params.get('end', '')

        if not code:
            self.send_json({'success': False, 'message': '请输入股票代码'})
            return

        try:
            symbol = code_to_symbol(code)
            raw = fetch_kline(symbol, 500)

            # 按日期筛选
            if start or end:
                filtered = []
                for r in raw:
                    day = r['day']
                    if start and day < start: continue
                    if end and day > end: continue
                    filtered.append(r)
                raw = filtered

            if not raw:
                self.send_json({'success': False, 'message': '未找到数据，请检查股票代码和日期'})
                return

            dates, rates, closes = calc_return_rates(raw)
            table = calc_daily_table(raw)
            total_ret = rates[-1] if rates else 0

            self.send_json({
                'success': True,
                'date_labels': dates,
                'return_rates': rates,
                'daily_data': table,
                'total_return': total_ret,
            })

        except Exception as e:
            self.send_json({'success': False, 'message': f'获取数据失败: {str(e)}'})

    def handle_recovery(self, body):
        code = body.get('code', '')
        buy_date = body.get('buy_date', '')
        buy_price = body.get('buy_price', '')

        if not code or not buy_date or not buy_price:
            self.send_json({'success': False, 'message': '请填写完整信息'})
            return

        try:
            symbol = code_to_symbol(code)
            raw = fetch_kline(symbol, 500)

            # 筛选买入日期之后的数据
            filtered = [r for r in raw if r['day'] >= buy_date]
            if not filtered:
                self.send_json({'success': False, 'message': '买入日期超出数据范围'})
                return

            buy_day = filtered[0]
            buy_open = float(buy_day['open'])
            buy_close = float(buy_day['close'])
            buy_pct = round((buy_close - buy_open) / buy_open * 100, 2)
            bp = float(buy_price)

            result = find_breakeven(filtered, bp)
            result['buy_date'] = buy_day['day']
            result['buy_open'] = round(buy_open, 2)
            result['buy_close'] = round(buy_close, 2)
            result['buy_pct'] = buy_pct
            result['buy_price'] = bp
            result['message'] = (
                f"回本日期 {result['breakeven_date']}，等待 {result['days_waited']} 个交易日"
                if result['found'] else
                f"截至 {filtered[-1]['day']} 尚未回本，亏损 {result.get('loss_pct', 0):+.2f}%"
            )

            # 价格图表数据
            chart_dates = [r['day'] for r in filtered]
            chart_closes = [round(float(r['close']), 2) for r in filtered]

            self.send_json({
                'success': True,
                'result': result,
                'chart_dates': chart_dates,
                'chart_closes': chart_closes,
            })

        except Exception as e:
            self.send_json({'success': False, 'message': f'计算失败: {str(e)}'})

    def handle_search(self, params):
        # 搜索功能简化：让前端直接输代码
        self.send_json({'success': True, 'results': []})

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # 忽略 favicon 等请求的日志
    def log_message(self, format, *args):
        pass
