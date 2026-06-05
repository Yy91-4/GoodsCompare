import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fetchers.base import BaseFetcher


class StubFetcher(BaseFetcher):
    def build_search_url(self, query):
        return f"https://stub.example.com/search?q={query}"

    def parse_results(self, html):
        return {
            'status': 'ok',
            'product_name': '测试商品',
            'price': 9.99,
            'shop': '测试店铺',
            'url': 'https://stub.example.com/item/1'
        }


class TestCaptchaDetection:
    def test_detects_chinese_captcha(self):
        fetcher = StubFetcher()
        assert fetcher._is_captcha('<html>请输入验证码</html>') is True
        assert fetcher._is_captcha('<html>滑块验证</html>') is True
        assert fetcher._is_captcha('<html>人机验证</html>') is True

    def test_normal_page_not_captcha(self):
        fetcher = StubFetcher()
        assert fetcher._is_captcha('<html>可口可乐 价格 49.90</html>') is False

    def test_english_captcha_indicators(self):
        fetcher = StubFetcher()
        assert fetcher._is_captcha('<html>captcha required</html>') is True


class TestBuildSearchUrl:
    def test_build_url_encodes_query(self):
        fetcher = StubFetcher()
        url = fetcher.build_search_url('可口可乐')
        assert '可口可乐' in url


from unittest.mock import patch, MagicMock
from fetchers.taobao import TaobaoFetcher
from fetchers.meituan import MeituanFetcher
from fetchers.jd import JDFetcher


TAOBAO_HTML = '''
<html>
<body>
<div class="item">
  <a href="/item/123.html">
    <span class="title">可口可乐 330ml x 24罐</span>
    <span class="price">49.90</span>
    <span class="shop">天猫超市</span>
  </a>
</div>
</body>
</html>
'''

MEITUAN_HTML = '''
<html>
<body>
<div class="poi-item">
  <a href="/poi/456">
    <div class="poi-name">可口可乐</div>
    <div class="price">52.00</div>
    <div class="shop-name">XX便利店</div>
  </a>
</div>
</body>
</html>
'''

JD_HTML = '''
<html>
<body>
<div class="gl-item">
  <div class="p-name">可口可乐 330ml x 24罐</div>
  <div class="p-price">50.50</div>
  <div class="p-shop">京东自营</div>
  <a href="/item/789.html" class="p-link">商品链接</a>
</div>
</body>
</html>
'''

CAPTCHA_HTML = '<html><body>请输入验证码</body></html>'


class TestTaobaoFetcher:
    def test_build_search_url(self):
        f = TaobaoFetcher()
        url = f.build_search_url('可乐')
        assert 'm.taobao.com' in url
        assert '可乐' in url

    def test_parse_results(self):
        f = TaobaoFetcher()
        result = f.parse_results(TAOBAO_HTML)
        assert result['status'] == 'ok'
        assert result['product_name'] == '可口可乐 330ml x 24罐'
        assert result['price'] == 49.90
        assert result['shop'] == '天猫超市'
        assert result['url'] == 'https://m.taobao.com/item/123.html'

    def test_parse_no_results(self):
        f = TaobaoFetcher()
        result = f.parse_results('<html></html>')
        assert result['status'] == 'no_result'

    @patch('fetchers.base.requests.Session.get')
    def test_search_captcha_detected(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = CAPTCHA_HTML
        mock_resp.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_resp

        f = TaobaoFetcher()
        result = f.search('可乐')
        assert result['status'] == 'captcha'
        assert result['message'] == '需要完成验证码'


class TestMeituanFetcher:
    def test_build_search_url(self):
        f = MeituanFetcher()
        url = f.build_search_url('可乐')
        assert 'i.meituan.com' in url

    def test_parse_results(self):
        f = MeituanFetcher()
        result = f.parse_results(MEITUAN_HTML)
        assert result['status'] == 'ok'
        assert result['price'] == 52.00


class TestJDFetcher:
    def test_build_search_url(self):
        f = JDFetcher()
        url = f.build_search_url('可乐')
        assert 'm.jd.com' in url

    def test_parse_results(self):
        f = JDFetcher()
        result = f.parse_results(JD_HTML)
        assert result['status'] == 'ok'
        assert result['price'] == 50.50
        assert result['shop'] == '京东自营'
