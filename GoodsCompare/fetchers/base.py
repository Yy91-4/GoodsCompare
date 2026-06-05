import requests
from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    TIMEOUT = 10

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Linux; Android 14; Pixel 8) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Mobile Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })

    @abstractmethod
    def build_search_url(self, query):
        pass

    @abstractmethod
    def parse_results(self, html):
        pass

    def search(self, query):
        url = self.build_search_url(query)
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT)
            resp.encoding = resp.apparent_encoding
            if self._is_captcha(resp.text):
                return {
                    'status': 'captcha',
                    'captcha_url': url,
                    'message': '需要完成验证码'
                }
            return self.parse_results(resp.text)
        except requests.RequestException as e:
            return {
                'status': 'error',
                'message': f'请求失败: {str(e)}'
            }

    def _is_captcha(self, html):
        indicators = [
            '验证码', '滑块验证', '请完成安全验证',
            '人机验证', '图形验证', '安全验证',
            'captcha', 'recaptcha', 'verify',
        ]
        html_lower = html.lower()
        return any(ind.lower() in html_lower for ind in indicators)
