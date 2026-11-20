"""LRU-кеш с ограничением размера и доступом из нескольких потоков.

Для порядка ключей взяла OrderedDict: давно использованные хранятся в начале.
Все обращения к хранилищу закрыла одним RLock.

Пример:
    cache: LRUCache[str, int] = LRUCache(capacity=100)
    cache.put("key", 42)
    val = cache.get("key")                 # 42
    miss = cache.get("no", default=-1)     # -1
    size = len(cache)
    "key" in cache                         # bool
"""

from collections import OrderedDict
import threading


class LRUCache[K, V]:
    """При переполнении убираем ключ, к которому дольше всего не обращались.

    Чтение через get и запись через put делают ключ самым свежим.
    Проверка через in порядок не меняет.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity должен быть >= 1")
        self._capacity = capacity
        self._data: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.RLock()

    @property
    def capacity(self) -> int:
        with self._lock:
            return self._capacity

    def put(self, key: K, value: V) -> None:
        # Запись, обновление порядка и вытеснение — одна операция под замком.
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            if len(self._data) > self._capacity:
                self._data.popitem(last=False)

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            if key not in self._data:
                return default
            self._data.move_to_end(key)
            return self._data[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: object) -> bool:
        with self._lock:
            return key in self._data
