from flask import Flask, request, jsonify, send_from_directory
import threading
import os
from models import (
    init_db, get_or_create_product, add_price_record,
    get_price_trends_grouped, add_favorite, get_favorites,
    remove_favorite, add_search_history, get_search_history,
    get_all_product_names
)
from fetchers.taobao import TaobaoFetcher
from fetchers.meituan import MeituanFetcher
from fetchers.jd import JDFetcher

app = Flask(__name__, static_folder='static', static_url_path='')

fetchers = {
    'taobao': TaobaoFetcher(),
    'meituan': MeituanFetcher(),
    'jd': JDFetcher(),
}

PLATFORM_NAMES = {
    'taobao': '淘宝闪购',
    'meituan': '美团',
    'jd': '京东',
}


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': '请输入商品名'}), 400

    results = []
    lock = threading.Lock()

    def fetch_platform(platform_key, fetcher):
        try:
            result = fetcher.search(q)
        except Exception as e:
            result = {'status': 'error', 'message': str(e)}
        result['platform'] = PLATFORM_NAMES[platform_key]
        with lock:
            results.append(result)

    threads = []
    for key, f in fetchers.items():
        t = threading.Thread(target=fetch_platform, args=(key, f))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=15)

    for r in results:
        if r.get('status') == 'ok' and r.get('price', 0) > 0:
            product = get_or_create_product(r['product_name'], '')
            add_price_record(
                product['id'], r['platform'], r['price'],
                r.get('shop', ''), r.get('url', ''), 'auto'
            )

    add_search_history(q)

    results.sort(key=lambda x: x.get('price', float('inf')))
    return jsonify({'query': q, 'results': results})


@app.route('/api/price/manual', methods=['POST'])
def manual_price():
    data = request.get_json(force=True)
    if not data:
        return jsonify({'error': '请求体为空'}), 400

    product_name = data.get('product_name', '').strip()
    platform = data.get('platform', '').strip()
    price = data.get('price')

    if not product_name or not platform:
        return jsonify({'error': '缺少商品名或平台'}), 400
    if price is None:
        return jsonify({'error': '缺少价格'}), 400

    try:
        price = float(price)
    except (TypeError, ValueError):
        return jsonify({'error': '价格格式错误'}), 400

    product = get_or_create_product(product_name)
    add_price_record(product['id'], platform, price, source='manual')

    return jsonify({'ok': True})


@app.route('/api/favorites', methods=['GET'])
def list_favorites():
    return jsonify(get_favorites())


@app.route('/api/favorites/add', methods=['POST'])
def add_favorite_route():
    data = request.get_json(force=True)
    product_name = data.get('product_name', '').strip()
    platform = data.get('platform', '').strip()

    if not product_name or not platform:
        return jsonify({'error': '缺少商品名或平台'}), 400

    product = get_or_create_product(product_name)
    add_favorite(product['id'], platform)
    return jsonify({'ok': True})


@app.route('/api/favorites/<int:fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
    remove_favorite(fav_id)
    return jsonify({'ok': True})


@app.route('/api/trend')
def trend():
    product_name = request.args.get('product', '').strip()
    if not product_name:
        return jsonify({'error': '缺少商品名'}), 400
    data = get_price_trends_grouped(product_name)
    return jsonify(data)


@app.route('/api/history')
def history():
    return jsonify(get_search_history())


@app.route('/api/products')
def product_list():
    return jsonify(get_all_product_names())


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
