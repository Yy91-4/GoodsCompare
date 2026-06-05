from bs4 import BeautifulSoup
from fetchers.base import BaseFetcher
from urllib.parse import quote, urljoin

BASE = 'https://m.taobao.com'


class TaobaoFetcher(BaseFetcher):
    def build_search_url(self, query):
        q = quote(query)
        return f'{BASE}/search.html?q={q}'

    def parse_results(self, html):
        soup = BeautifulSoup(html, 'lxml')
        item = soup.select_one('.item, [class*="search-item"], [class*="goods-item"]')
        if not item:
            return {'status': 'no_result', 'message': '未找到商品'}

        title_el = item.select_one('.title, [class*="title"], .name, [class*="name"]')
        price_el = item.select_one('.price, [class*="price"]')
        shop_el = item.select_one('.shop, [class*="shop"], .seller, [class*="seller"]')
        link_el = item.select_one('a[href]')

        title = title_el.get_text(strip=True) if title_el else '未知商品'
        price_text = price_el.get_text(strip=True) if price_el else '0'
        shop = shop_el.get_text(strip=True) if shop_el else ''
        href = link_el.get('href', '') if link_el else ''

        try:
            price = float(price_text.replace('¥', '').replace('￥', '').replace(',', '').strip())
        except ValueError:
            price = 0.0

        url = urljoin(BASE, href) if href and not href.startswith('http') else href

        return {
            'status': 'ok',
            'product_name': title,
            'price': price,
            'shop': shop,
            'url': url or f'{BASE}/search.html?q={quote(title)}',
        }
