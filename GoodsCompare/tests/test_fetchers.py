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
