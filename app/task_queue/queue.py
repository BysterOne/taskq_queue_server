import threading
from collections.abc import Callable, Iterator
from functools import wraps
from typing import Any

from .node import TaskNode
from .persistence import PersistenceManager


def synchronized(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            return fn(self, *args, **kwargs)
    return wrapper


class TaskIndex:
    _tasks: dict[int, TaskNode]

    def __init__(self) -> None:
        self._tasks = {}

    def get(self, task_id: int) -> TaskNode | None:
        return self._tasks.get(task_id, None)

    def set(self, task_id: int, task: TaskNode) -> None:
        self._tasks[task_id] = task

    def delete(self, task_id: int) -> None:
        del self._tasks[task_id]


class TaskQueue:
    _first: TaskNode | None = None
    _last: TaskNode | None = None
    _index: TaskIndex
    _lock: threading.Lock
    _employer_id: int | None

    def __init__(self, employer_id: int | None = None) -> None:
        self._index = TaskIndex()
        self._lock = threading.RLock()
        self._first = None
        self._last = None
        self._employer_id = employer_id

    @synchronized
    def add_task(self, task: TaskNode, prev_task: TaskNode | None = None, *, log: bool = True) -> None:
        if self._index.get(task.id) is not None:
            raise ValueError(f"Task with id {task.id} already exists in the queue")

        if prev_task and not self._index.get(prev_task.id):
            raise ValueError("prev_task is not in the queue")

        self._index.set(task.id, task)

        if not self._first:
            self._first = self._last = task
            if log and self._employer_id is not None:
                PersistenceManager.log(self._employer_id, {
                    'action': 'add',
                    'task': {'id': task.id, 'duration': task.duration, 'done_date': task.done_date},
                    'prev': None,
                })
            return

        if not prev_task:
            prev_task = self._last

        task.next = prev_task.next
        task.prev = prev_task

        if prev_task.next:
            prev_task.next.prev = task
        prev_task.next = task

        if prev_task is self._last:
            self._last = task

        if log and self._employer_id is not None:
            PersistenceManager.log(self._employer_id, {
                'action': 'add',
                'task': {'id': task.id, 'duration': task.duration, 'done_date': task.done_date},
                'prev': prev_task.id if prev_task else None,
            })

    @synchronized
    def get_task(self, task_id: int) -> TaskNode | None:
        return self._index.get(task_id)

    @synchronized
    def unlink_task(self, task: TaskNode) -> None:
        if not self.task_exists(task.id):
            raise ValueError(f"Task with id {task.id} does not exist in the queue")

        if task.prev:
            task.prev.next = task.next
        if task.next:
            task.next.prev = task.prev

        if task is self._first:
            self._first = task.next
        if task is self._last:
            self._last = task.prev

    @synchronized
    def delete_task(self, task: TaskNode) -> TaskNode | None:
        self.unlink_task(task)
        self._index.delete(task.id)
        if self._employer_id is not None:
            PersistenceManager.log(self._employer_id, {
                'action': 'delete',
                'task_id': task.id,
            })
        return task.next

    @synchronized
    def task_exists(self, task_id: int) -> bool:
        return self._index.get(task_id) is not None

    @synchronized
    def update_task(self, task: TaskNode) -> None:
        original = self.get_task(task.id)
        if original is None:
            raise ValueError(f"Task with id {task.id} does not exist in the queue")
        original.duration = task.duration
        original.done_date = task.done_date
        if self._employer_id is not None:
            PersistenceManager.log(self._employer_id, {
                'action': 'update',
                'task': {'id': task.id, 'duration': task.duration, 'done_date': task.done_date},
            })

    @synchronized
    def move_task(self, task: TaskNode, prev_task: TaskNode | None = None) -> None:
        self.unlink_task(task)

        if prev_task:
            task.link_after(prev_task)
            if prev_task is self._last:
                self._last = task
            if self._employer_id is not None:
                PersistenceManager.log(self._employer_id, {
                    'action': 'move',
                    'task_id': task.id,
                    'prev': prev_task.id if prev_task else None,
                })
            return

        # Если prev_task равен None, добавляем задачу в начало очереди
        task.next = self._first
        task.prev = None
        if self._first:
            self._first.prev = task
        self._first = task
        if self._employer_id is not None:
            PersistenceManager.log(self._employer_id, {
                'action': 'move',
                'task_id': task.id,
                'prev': prev_task.id if prev_task else None,
            })

    def get_tasks(self, from_task: TaskNode | None = None, to_task: TaskNode | None = None) -> Iterator[TaskNode]:
        with self._lock:
            current = from_task or self._first
            after = to_task.next if to_task else None
            while current and current is not after:
                yield current
                current = current.next

    @property
    def first_task(self) -> TaskNode | None:
        with self._lock:
            return self._first

    @property
    def latest_task(self) -> TaskNode | None:
        with self._lock:
            return self._last
