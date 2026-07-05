"""
Flask 手机版 — Web API + 页面渲染
复用现有 data/fetcher, utils/calculator, data/storage 模块
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
import pandas as pd

from data.fetcher import get_stock_data, search_stock
from data.storage import save_record, get_all_records, delete_record
from utils.calculator import (
    calc_return_rate, calc_daily_summary, calc_interval_return,
    find_breakeven_date,
)

app = Flask(__name__)

# ---- 页面路由 ----

@app.route('/')
def page_return():
    """功能一：收益率查询"""
    return render_template('return.html')


@app.route('/recovery')
def page_recovery():
    """功能二：回本计算器"""
    return render_template('recovery.html')


@app.route('/records')
def page_records():
    """功能三：我的记录"""
    return render_template('records.html')


# ---- API 路由 ----

@app.route('/api/search')
def api_search():
    """搜索股票"""
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': '请输入搜索关键词'})

    try:
        results = search_stock(keyword)
        if not results:
            return jsonify({'success': False, 'message': f'未找到与「{keyword}」相关的股票'})
        return jsonify({
            'success': True,
            'results': [{'code': code, 'name': name} for code, name in results]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/query', methods=['POST'])
def api_query():
    """查询股票数据，返回收益率 + 每日明细"""
    data = request.get_json()
    stock_code = data.get('stock_code', '').strip()
    start_date = data.get('start_date', '').strip()
    end_date = data.get('end_date', '').strip()

    if not all([stock_code, start_date, end_date]):
        return jsonify({'success': False, 'message': '请填写完整的查询条件'})

    try:
        df = get_stock_data(stock_code, start_date, end_date)

        # 收益率序列（用于图表）
        ret = calc_return_rate(df)
        date_labels = [str(d)[:10] for d in df['date']]
        return_rates = [round(v, 2) for v in ret.values.tolist()]

        # 每日明细（用于表格）
        summary = calc_daily_summary(df)
        daily_data = []
        for _, row in summary.iterrows():
            daily_data.append({
                'date': row['日期'],
                'open': round(float(row['开盘价']), 2),
                'close': round(float(row['收盘价']), 2),
                'change': round(float(row['涨跌幅(%)']), 2),
            })

        # 区间涨跌幅
        total_return = calc_interval_return(df)

        return jsonify({
            'success': True,
            'stock_code': stock_code,
            'start_date': start_date,
            'end_date': end_date,
            'total_return': total_return,
            'date_labels': date_labels,
            'return_rates': return_rates,
            'daily_data': daily_data,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/recovery', methods=['POST'])
def api_recovery():
    """回本计算"""
    data = request.get_json()
    stock_code = data.get('stock_code', '').strip()
    buy_date = data.get('buy_date', '').strip()
    buy_price_str = data.get('buy_price', '').strip()

    if not all([stock_code, buy_date, buy_price_str]):
        return jsonify({'success': False, 'message': '请填写完整的计算条件'})

    try:
        buy_price = float(buy_price_str)
    except ValueError:
        return jsonify({'success': False, 'message': '买入价格格式不正确'})

    try:
        import datetime
        today = datetime.date.today()
        end_date = today.strftime('%Y%m%d')
        start_date = buy_date

        df = get_stock_data(stock_code, start_date, end_date)
        result = find_breakeven_date(df, buy_date, buy_price)

        # 价格走势数据（用于图表）
        dates = [str(d)[:10] for d in df['date']]
        closes = [round(float(c), 2) for c in df['close'].tolist()]

        return jsonify({
            'success': True,
            'result': result,
            'chart_dates': dates,
            'chart_closes': closes,
            'buy_price': buy_price,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/save', methods=['POST'])
def api_save():
    """保存查询记录"""
    data = request.get_json()
    stock_code = data.get('stock_code', '').strip()
    stock_name = data.get('stock_name', stock_code)
    start_date = data.get('start_date', '').strip()
    end_date = data.get('end_date', '').strip()
    return_pct = float(data.get('return_pct', 0))

    if not all([stock_code, start_date, end_date]):
        return jsonify({'success': False, 'message': '缺少保存所需的参数'})

    try:
        record_id = save_record(
            stock_code=stock_code,
            stock_name=stock_name,
            start_date=start_date,
            end_date=end_date,
            return_pct=return_pct,
        )
        return jsonify({'success': True, 'record_id': record_id, 'message': '保存成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/records/list')
def api_records_list():
    """获取所有记录"""
    try:
        records = get_all_records()
        result = []
        for rec in records:
            result.append({
                'id': rec['id'],
                'stock_code': rec['stock_code'],
                'stock_name': rec['stock_name'],
                'start_date': rec['start_date'],
                'end_date': rec['end_date'],
                'return_pct': round(rec['return_pct'], 2),
                'category_year': rec['category_year'],
                'category_month': rec['category_month'],
                'created_at': rec['created_at'],
            })
        return jsonify({'success': True, 'records': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/records/delete', methods=['POST'])
def api_records_delete():
    """删除记录"""
    data = request.get_json()
    record_id = data.get('id')
    if not record_id:
        return jsonify({'success': False, 'message': '缺少记录ID'})

    try:
        ok = delete_record(int(record_id))
        if ok:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ---- 启动入口 ----

if __name__ == '__main__':
    # host='0.0.0.0' 允许局域网内其他设备（手机）访问
    app.run(host='0.0.0.0', port=5000, debug=True)
