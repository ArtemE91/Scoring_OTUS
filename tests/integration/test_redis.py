import pytest
from pytest import fixture
import redis

from scoring import get_score, get_interests
from store import StorageRedis


@fixture
def storage_redis():
    return StorageRedis()


@fixture
def storage_set_name_value(storage_redis):
    storage_redis.set('key', 'value')
    yield storage_redis, 'key', 'value'
    storage_redis.delete('key')


@fixture
def storage_redis_offline_mock(monkeypatch):
    def mock_get_and_set_to_redis(*args, **kwargs):
        raise redis.exceptions.ConnectionError
    monkeypatch.setattr(redis.Redis, 'get', mock_get_and_set_to_redis)
    monkeypatch.setattr(redis.Redis, 'set', mock_get_and_set_to_redis)


def test_cache_set(storage_redis):
    assert storage_redis.cache_set('111', '222', 30) is True


def test_get(storage_set_name_value):
    storage_redis, name, value = storage_set_name_value
    assert storage_redis.get(name) == value
    assert storage_redis.cache_get(name) == value


def test_get_command_reconnect(storage_redis, storage_redis_offline_mock):
    with pytest.raises(redis.exceptions.ConnectionError):
        storage_redis.get("111")


def test_cached_set_reconnect(storage_redis, storage_redis_offline_mock):
    assert storage_redis.cache_get("111") is None


def test_cached_get_reconnect(storage_redis, storage_redis_offline_mock):
    assert storage_redis.cache_set("111", "222", 30) is None


def test_get_score_if_redis_offline(storage_redis, storage_redis_offline_mock):
    score = get_score(storage_redis, phone="79173456253", email="otus@mail.ru")
    assert score == 3.0


def test_get_interests_if_redis_offline(storage_redis, storage_redis_offline_mock):
    with pytest.raises(redis.exceptions.ConnectionError):
        get_interests(storage_redis, 1)

