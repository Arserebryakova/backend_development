"""Небольшой event loop на генераторах.

К планировщику с лекции добавила ожидание другой задачи через await_task.
Результаты сохраняются, чтобы можно было дождаться и уже завершённой задачи.
Ожидающие задачи убираются из очереди до получения результата.
"""

import time
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

Task = Generator[Any, Any, Any]

# Через yield задачи сообщают планировщику, чего ждут.


@dataclass
class Sleep:
    duration: float


@dataclass
class AwaitTask:
    tid: int


# Текущий планировщик нужен функциям create_task и run.

_current: "Scheduler | None" = None


class Scheduler:
    def __init__(self) -> None:
        # В очереди: id задачи, её генератор и значение для следующего send.
        self.ready: deque[tuple[int, Task, Any]] = deque()
        self.sleeping: list[tuple[float, int, Task]] = []
        self.results: dict[int, Any] = {}
        # id ожидаемой задачи -> все, кому нужно передать её результат.
        self.waiters: dict[int, list[tuple[int, Task]]] = {}
        self.next_id = 0

    def _new_tid(self) -> int:
        self.next_id += 1
        return self.next_id

    def create_task(self, coro: Task) -> int:
        tid = self._new_tid()
        self.ready.append((tid, coro, None))
        return tid

    def run(self, main: Task) -> None:
        global _current  # noqa: PLW0603  # запоминаем запущенный планировщик
        _current = self
        try:
            self.create_task(main)
            while self._has_work():
                self._wake_sleeping()
                if not self.ready:
                    self._idle_wait_or_deadlock()
                    continue
                self._step_one()
        finally:
            _current = None

    def _has_work(self) -> bool:
        return bool(self.ready or self.sleeping or self.waiters)

    def _wake_sleeping(self) -> None:
        now = time.monotonic()
        still: list[tuple[float, int, Task]] = []
        for wake_at, tid, task in self.sleeping:
            if wake_at <= now:
                self.ready.append((tid, task, None))
            else:
                still.append((wake_at, tid, task))
        self.sleeping = still

    def _idle_wait_or_deadlock(self) -> None:
        if self.sleeping:
            next_wake = min(w for w, _, _ in self.sleeping)
            # Здесь можно ждать: готовых задач нет. Так цикл не крутится впустую.
            time.sleep(max(0.0, next_wake - time.monotonic()))
        elif self.waiters:
            raise RuntimeError("deadlock: задачи ждут, но готовых и спящих задач нет")

    def _step_one(self) -> None:
        tid, task, value = self.ready.popleft()
        try:
            syscall = task.send(value)
        except StopIteration as e:
            self._finish_task(tid, e.value)
            return
        self._handle_syscall(tid, task, syscall)

    def _finish_task(self, tid: int, result: Any) -> None:  # noqa: ANN401
        self.results[tid] = result
        # Один результат могут ждать несколько задач — будим каждую.
        for waiter_tid, waiter in self.waiters.pop(tid, []):
            self.ready.append((waiter_tid, waiter, result))

    def _handle_syscall(self, tid: int, task: Task, syscall: Any) -> None:  # noqa: ANN401
        if isinstance(syscall, Sleep):
            self.sleeping.append((time.monotonic() + syscall.duration, tid, task))
        elif isinstance(syscall, AwaitTask):
            if syscall.tid in self.results:
                self.ready.append((tid, task, self.results[syscall.tid]))
            else:
                # Пока результата нет, задачу обратно в ready не ставим.
                self.waiters.setdefault(syscall.tid, []).append((tid, task))
        else:
            raise RuntimeError(f"unknown syscall: {syscall!r}")


# Функции для работы с планировщиком


def sleep(duration: float) -> Task:
    """Приостанавливаем задачу: yield from sleep(duration)."""
    yield Sleep(duration)


def create_task(coro: Task) -> int:
    """Добавляем генератор в очередь и возвращаем id задачи."""
    if _current is None:
        raise RuntimeError("нет running loop'а (вызывай из main через run())")  # noqa: RUF001
    return _current.create_task(coro)


def await_task(tid: int) -> Task:
    """Ждём задачу, а её результат получаем через send от планировщика."""
    return (yield AwaitTask(tid))


def run(main: Task) -> None:
    """Запускаем main и выполняем все созданные задачи до завершения."""
    Scheduler().run(main)
