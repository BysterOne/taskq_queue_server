from typing import Optional


class TaskNode:
    prev: Optional['TaskNode'] = None
    next: Optional['TaskNode'] = None
    id: int
    duration: Optional[float] = None
    done_date: Optional[float] = None

    def __init__(self, task_id: int, duration: float, done_date: float | None = None) -> None:
        self.id = task_id
        self.duration = duration
        self.done_date = done_date if done_date else 0

    def link_after(self, after: 'TaskNode') -> None:
        # обновили связи на соседей у текущей задачи
        self.next = after.next
        self.prev = after

        # обновляем у соседей связи на текущую задачу
        if after.next:
            after.next.prev = self
        after.next = self
