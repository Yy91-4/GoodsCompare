from bs4 import BeautifulSoup
from fetchers.base import BaseFetcher
from urllib.parse import quote, urljoin

BASE = 'https://i.meituan.com'


class MeituanFetcher(BaseFetcher):
    def build_search_url(self, query):
        q = quote(query)
        return f'{BASE}/s/{q}'

    def parse_results(self, html):
        soup = BeautifulSoup(html, 'lxml')
        item = soup.select_one('.poi-item, [class*="search-item"], [class*="list-item"]')
        if not item:
            return {'status': 'no_result', 'message': '未找到商品'}

        name_el = item.select_one('.poi-name, .name, [class*="title"]')
        price_el = item.select_one('.price, [class*="price"], .current-price')
        shop_el = item.select_one('.shop-name, .brand, [class*="shop"]')
        link_el = item.select_one('a[href]')

        title = name_el.get_text(strip=True) if name_el else '未知商品'
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
            'url': url or f'{BASE}/s/{quote(title)}',
        }
