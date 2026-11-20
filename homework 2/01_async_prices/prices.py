"""Сравнение цен: по очереди, конкурентно, с таймаутом и с лимитом запросов.

Для сравнения оставила все варианты, чтобы было видно разницу во времени.
"""

import asyncio

# "База" магазинов: цена и время ответа API в секундах. НЕ менять.
PRICES: dict[str, int] = {"ozon": 990, "wb": 950, "yandex": 1100, "slow_shop": 900}
DELAYS: dict[str, float] = {"ozon": 0.3, "wb": 0.2, "yandex": 0.4, "slow_shop": 5.0}


async def fetch_price(shop: str) -> int:
    """Имитирует запрос к API магазина. НЕ менять.

    Неизвестный магазин отвечает за 0.1 с и возвращает цену 1000.
    """
    await asyncio.sleep(DELAYS.get(shop, 0.1))
    return PRICES.get(shop, 1000)


# 1.1. Запросы по очереди


async def get_prices_sequential(shops: list[str]) -> list[int]:
    """Ждём ответ одного магазина и только потом идём к следующему."""
    prices = []
    for shop in shops:
        prices.append(await fetch_price(shop))
    return prices


# 1.2. Конкурентные запросы


async def get_prices_concurrent(shops: list[str]) -> list[int]:
    """Запускаем запросы вместе. gather сохраняет исходный порядок магазинов."""
    return await asyncio.gather(*(fetch_price(shop) for shop in shops))


# 1.3. Таймаут для каждого магазина


async def get_price_or_none(shop: str, timeout: float = 1.0) -> int | None:
    """Возвращаем None, если магазин не успел ответить за timeout секунд."""
    try:
        return await asyncio.wait_for(fetch_price(shop), timeout=timeout)
    except TimeoutError:
        return None


async def get_prices_with_timeout(shops: list[str], timeout: float = 1.0) -> list[int | None]:
    """Собираем цены вместе, но не ждём медленные магазины дольше таймаута."""
    return await asyncio.gather(*(get_price_or_none(shop, timeout) for shop in shops))


# 1.4. Ограничение числа запросов


async def get_prices_limited(shops: list[str], limit: int = 3) -> list[int]:
    """Не больше limit запросов одновременно, остальные ждут своей очереди."""
    if limit < 1:
        raise ValueError("limit должен быть >= 1")

    # Семафор общий для всех магазинов в этом вызове.
    semaphore = asyncio.Semaphore(limit)

    async def fetch_limited(shop: str) -> int:
        async with semaphore:
            return await fetch_price(shop)

    return await asyncio.gather(*(fetch_limited(shop) for shop in shops))


if __name__ == "__main__":
    import time

    async def main() -> None:
        shops = ["ozon", "wb", "yandex"]
        for fn in (get_prices_sequential, get_prices_concurrent):
            start = time.perf_counter()
            result = await fn(shops)
            print(f"{fn.__name__:25} {time.perf_counter() - start:.2f}s  {result}")

        start = time.perf_counter()
        result_with_timeout = await get_prices_with_timeout(shops + ["slow_shop"])
        print(f"{'get_prices_with_timeout':25} {time.perf_counter() - start:.2f}s  {result_with_timeout}")

    asyncio.run(main())
