import threading

from .node import TaskNode
from .persistence import PersistenceManager
from .queue import TaskQueue


class QueueManager:
    _queues: dict[int, TaskQueue] = {}
    _lock = threading.Lock()

    @classmethod
    def get_queue(cls, employer_id: int) -> TaskQueue:
        with cls._lock:
            queue = cls._queues.get(employer_id, None)
            if queue is None:
                raise ValueError(f"No queue for employer_id {employer_id}")
            return queue

    @classmethod
    def create_queue(cls, employer_id: int) -> TaskQueue:
        with cls._lock:
            if employer_id in cls._queues:
                raise ValueError(f"Queue for employer_id {employer_id} already exists")
            queue = TaskQueue(employer_id)
            tasks = PersistenceManager.recover(employer_id)
            prev = None
            for data in tasks:
                node = TaskNode(data['id'], data['duration'], data['done_date'])
                queue.add_task(node, prev_task=prev, log=False)
                prev = node
            cls._queues[employer_id] = queue
            return queue

    @classmethod
    def delete_queue(cls, employer_id: int) -> None:
        with cls._lock:
            if employer_id not in cls._queues:
                raise ValueError(f"No queue for employer_id {employer_id}")
            del cls._queues[employer_id]
            PersistenceManager.clear(employer_id)

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._queues.clear()
            PersistenceManager.clear()
