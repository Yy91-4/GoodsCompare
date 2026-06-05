# tests/test_models.py
import pytest
import sqlite3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import models


@pytest.fixture
def db():
    test_db = os.path.join(os.path.dirname(__file__), '..', 'test_temp.db')
    models.DB_PATH = test_db
    models.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


class TestInitDB:
    def test_creates_all_tables(self, db):
        conn = models.get_db()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {t['name'] for t in tables}
        assert 'products' in names
        assert 'price_records' in names
        assert 'favorites' in names
        assert 'search_history' in names


class TestProducts:
    def test_add_product(self, db):
        pid = models.add_product('可口可乐', '330ml x 24罐')
        assert pid > 0

    def test_add_duplicate_product_returns_existing_id(self, db):
        pid1 = models.add_product('可口可乐', '330ml')
        pid2 = models.add_product('可口可乐', '330ml')
        assert pid1 == pid2

    def test_get_or_create_creates_new(self, db):
        p = models.get_or_create_product('雪碧', '500ml')
        assert p['name'] == '雪碧'

    def test_get_or_create_returns_existing(self, db):
        models.add_product('芬达', '330ml')
        p = models.get_or_create_product('芬达', '330ml')
        assert p['name'] == '芬达'
        assert p['spec'] == '330ml'


class TestPriceRecords:
    def test_add_price_record(self, db):
        pid = models.add_product('可乐')
        rid = models.add_price_record(pid, 'taobao', 49.90, '天猫超市',
                                       'https://example.com', 'auto')
        assert rid > 0

    def test_get_price_trends(self, db):
        pid = models.add_product('可乐')
        models.add_price_record(pid, 'taobao', 49.90, source='auto')
        models.add_price_record(pid, 'meituan', 52.00, source='auto')
        models.add_price_record(pid, 'taobao', 50.50, source='manual')

        trends = models.get_price_trends('可乐')
        assert len(trends) == 3
        assert trends[0]['price'] == 49.90


class TestFavorites:
    def test_add_and_list_favorites(self, db):
        pid = models.add_product('可乐')
        models.add_favorite(pid, 'taobao')
        models.add_favorite(pid, 'meituan')

        favs = models.get_favorites()
        assert len(favs) == 2

    def test_remove_favorite(self, db):
        pid = models.add_product('可乐')
        fid = models.add_favorite(pid, 'taobao')
        models.remove_favorite(fid)
        assert len(models.get_favorites()) == 0

    def test_duplicate_favorite_is_ignored(self, db):
        pid = models.add_product('可乐')
        models.add_favorite(pid, 'taobao')
        models.add_favorite(pid, 'taobao')
        assert len(models.get_favorites()) == 1


class TestSearchHistory:
    def test_add_and_list_history(self, db):
        models.add_search_history('可乐')
        models.add_search_history('薯片')
        h = models.get_search_history()
        assert len(h) == 2
        assert h[0]['query'] == '薯片'  # most recent first

    def test_get_search_history_distinct(self, db):
        models.add_search_history('可乐')
        models.add_search_history('可乐')
        h = models.get_search_history()
        assert len(h) == 1  # 去重
