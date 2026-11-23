import os
import sqlite3
from contextlib import closing

import pytest

from records import RecordStore, validate


@pytest.fixture(params=["sqlite", "mysql"])
def store(request):
    if request.param == "mysql":
        if not os.getenv("TEST_MYSQL"):
            pytest.skip("Set TEST_MYSQL=1 with an isolated demo database")
        from mysql.connector import connect
        connection = connect(host="127.0.0.1", port=3307, user="portfolio",
                             password=os.environ["DB_PASSWORD"], database="portfolio")
        parameter = "%s"
    else:
        connection = sqlite3.connect(":memory:")
        connection.execute(
            "CREATE TABLE records (id INTEGER PRIMARY KEY, name TEXT, category TEXT, status TEXT)"
        )
        parameter = "?"
    with closing(connection):
        yield RecordStore(connection, parameter)


def test_crud_and_search(store):
    original = {"name": "QA demo ' record", "category": "application", "status": "active"}
    assert store.add(original) == 1
    record = store.search(original["name"])[-1]
    record_id = record["id"]
    try:
        assert store.get(record_id) == {"id": record_id, **original}
        assert store.update(record_id, {**original, "status": "archived"}) == 1
        assert store.get(record_id)["status"] == "archived"
    finally:
        assert store.delete(record_id) == 1
    assert store.get(record_id) is None


@pytest.mark.parametrize("payload", [{}, [], {"name": "", "category": "app", "status": "draft"},
                                     {"name": "Demo", "category": "app", "status": "unknown"}])
def test_invalid_payload(payload):
    with pytest.raises(ValueError):
        validate(payload)
