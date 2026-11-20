"""Рассылка уведомлений пользователям.

Исправила ожидание ответа сервера, из-за которого письма уходили по одному.
"""

import asyncio
import time


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


async def render_template(user: str) -> str:
    """Собрать текст письма."""
    await asyncio.sleep(0.01)
    return f"Привет, {user}! У нас новые скидки."


async def send_email(user: str) -> str:
    """Отправить письмо одному пользователю (почтовый сервер отвечает ~0.5 с)."""
    text = await render_template(user)
    log(f"отправляю письмо {user}")
    # Заменила time.sleep: он блокировал весь поток event loop. Поэтому даже
    # с gather другие письма ждали окончания sleep и отправлялись по очереди.
    # await asyncio.sleep отдаёт управление, пока мы ждём ответ сервера.
    await asyncio.sleep(0.5)  # ждём ответа почтового сервера
    log(f"письмо {user} доставлено")
    return f"{user}: {len(text)} символов"


async def notify_all(users: list[str]) -> list[str]:
    """Разослать письма всем пользователям одновременно."""
    return await asyncio.gather(*(send_email(user) for user in users))


if __name__ == "__main__":
    start = time.perf_counter()
    results = asyncio.run(notify_all(["anna", "boris", "vera", "gleb"]))
    print(results)
    print(f"Всего: {time.perf_counter() - start:.2f}s (ожидаем ~0.5 с)")
