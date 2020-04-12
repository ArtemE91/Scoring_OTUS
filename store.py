import redis
import logging
import functools
from redis.exceptions import ConnectionError, TimeoutError


def reconnect():
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                count_reconnect = getattr(args[0], 'retry_connection', None)
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                logging.info(str(e))
                while count_reconnect > 0:
                    try:
                        return func(*args, **kwargs)
                    except (ConnectionError, TimeoutError):
                        count_reconnect -= 1
                logging.error('Redis connection error')
                raise ConnectionError('Redis Connection error')
        return wrapped
    return decorator


class StorageRedis:

    def __init__(self, host='127.0.0.1', port=6379, retry_connection=3, timeout_connection=None):
        self.redis = redis.Redis(host=host, port=port, socket_timeout=timeout_connection)
        self.retry_connection = retry_connection

    def cache_get(self, key):
        try:
            return self.get(key)
        except (ConnectionError, TimeoutError) as e:
            logging.info(str(e))
            return None

    def cache_set(self, key, score, cached_time):
        try:
            return self.set(key, score, cached_time)
        except (ConnectionError, TimeoutError) as e:
            logging.info(str(e))
            return None

    @reconnect()
    def set(self, key, value, ex=None):
        return self.redis.set(name=key, value=value, ex=ex)

    @reconnect()
    def get(self, key):
        result = self.redis.get(key)
        return result.decode() if result else None

    @reconnect()
    def delete(self, key):
        self.redis.delete(key)
