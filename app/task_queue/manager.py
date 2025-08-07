import threading

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
            queue = TaskQueue()
            cls._queues[employer_id] = queue
            return queue

    @classmethod
    def delete_queue(cls, employer_id: int):
        with cls._lock:
            if employer_id not in cls._queues:
                raise ValueError(f"No queue for employer_id {employer_id}")
            del cls._queues[employer_id]

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._queues.clear()
