import pytest
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import server
import models


@pytest.fixture
def app():
    models.DB_PATH = ':memory:'
    models.init_db()
    server.app.config['TESTING'] = True
    return server.app.test_client()


class TestSearchAPI:
    def test_search_empty_query(self, app):
        resp = app.get('/api/search')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data

    def test_search_whitespace_query(self, app):
        resp = app.get('/api/search?q=   ')
        assert resp.status_code == 400

    def test_search_stores_history(self, app):
        resp = app.get('/api/search?q=可乐')
        assert resp.status_code == 200
        history = models.get_search_history()
        assert any(h['query'] == '可乐' for h in history)

    def test_search_response_structure(self, app):
        resp = app.get('/api/search?q=测试')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'query' in data
        assert 'results' in data
        assert isinstance(data['results'], list)


class TestManualPrice:
    def test_manual_price_creates_record(self, app):
        resp = app.post('/api/price/manual',
                        data=json.dumps({'product_name': '可乐', 'platform': '京东', 'price': 50.50}),
                        content_type='application/json')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['ok'] is True
        trends = models.get_price_trends('可乐')
        assert len(trends) == 1
        assert trends[0]['source'] == 'manual'

    def test_manual_price_missing_fields(self, app):
        resp = app.post('/api/price/manual',
                        data=json.dumps({'product_name': '可乐'}),
                        content_type='application/json')
        assert resp.status_code == 400


class TestFavoritesAPI:
    def test_favorites_crud(self, app):
        pid = models.add_product('可乐')
        models.add_price_record(pid, 'taobao', 49.90, source='auto')

        resp = app.post('/api/favorites/add',
                        data=json.dumps({'product_name': '可乐', 'platform': 'taobao'}),
                        content_type='application/json')
        assert resp.status_code == 200

        resp = app.get('/api/favorites')
        assert resp.status_code == 200
        favs = json.loads(resp.data)
        assert len(favs) == 1
        assert favs[0]['name'] == '可乐'
        assert favs[0]['platform'] == 'taobao'

        fav_id = favs[0]['fav_id']
        resp = app.delete(f'/api/favorites/{fav_id}')
        assert resp.status_code == 200

        resp = app.get('/api/favorites')
        assert len(json.loads(resp.data)) == 0


class TestTrendAPI:
    def test_trend_returns_grouped_data(self, app):
        pid = models.add_product('可乐')
        models.add_price_record(pid, 'taobao', 49.90, source='auto')
        models.add_price_record(pid, 'meituan', 52.00, source='auto')

        resp = app.get('/api/trend?product=可乐')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['product_name'] == '可乐'
        assert len(data['labels']) > 0
        assert len(data['datasets']) == 2

    def test_trend_unknown_product(self, app):
        resp = app.get('/api/trend?product=不存在')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['datasets'] == []


class TestHistoryAPI:
    def test_history_returns_list(self, app):
        resp = app.get('/api/history')
        assert resp.status_code == 200
        assert isinstance(json.loads(resp.data), list)

    def test_product_list(self, app):
        models.add_product('可乐')
        models.add_product('薯片')
        resp = app.get('/api/products')
        assert resp.status_code == 200
        products = json.loads(resp.data)
        assert '可乐' in products
        assert '薯片' in products


class TestStaticFiles:
    def test_index_served(self, app):
        resp = app.get('/')
        assert resp.status_code == 200
        assert b'<!DOCTYPE html>' in resp.data or b'<html' in resp.data

    def test_css_served(self, app):
        resp = app.get('/style.css')
        assert resp.status_code == 200

    def test_js_served(self, app):
        resp = app.get('/app.js')
        assert resp.status_code == 200
