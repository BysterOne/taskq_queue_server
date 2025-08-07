import logging
import time

import pytest
import structlog
from structlog.testing import capture_logs

from task_queue.node import TaskNode
from task_queue.queue import TaskQueue

QUEUE_SIZE = 10_000

memory_usage = pytest.importorskip("memory_profiler").memory_usage

logging.basicConfig(format="%(message)s")
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)


@pytest.fixture
def f_large_queue() -> TaskQueue:
    queue = TaskQueue()
    for i in range(1, QUEUE_SIZE + 1):
        queue.add_task(TaskNode(i, 10))
    return queue


def measure_performance(queue: TaskQueue, func, *args) -> None:
    start_memory = memory_usage()[0]
    start_time = time.time()
    func(queue, *args)
    elapsed_time = time.time() - start_time
    used_memory = memory_usage()[0] - start_memory
    logger.info(
        "performance",
        function=func.__name__,
        elapsed_time=elapsed_time,
        used_memory=used_memory,
    )


def get_first_100_tasks(queue: TaskQueue) -> None:
    list(queue.get_tasks(to_task=queue.get_task(100)))


def get_all_tasks(queue: TaskQueue) -> None:
    list(queue.get_tasks())


def check_existence_of_100_tasks(queue: TaskQueue) -> None:
    for i in range(3000, 4001):
        assert queue.task_exists(i)


def modify_first_100_tasks(queue: TaskQueue) -> None:
    for i in range(1, 101):
        task = queue.get_task(i)
        task.id += 1000
        queue.update_task(task)


def add_100_tasks_to_start(queue: TaskQueue) -> None:
    for i in range(QUEUE_SIZE + 1, QUEUE_SIZE + 101):
        queue.add_task(TaskNode(i, 10), None)


def add_100_tasks_to_end(queue: TaskQueue) -> None:
    for i in range(QUEUE_SIZE + 101, QUEUE_SIZE + 201):
        queue.add_task(TaskNode(i, 10))


def remove_100_tasks_from_end(queue: TaskQueue) -> None:
    for _ in range(100):
        queue.delete_task(queue.latest_task)


def remove_100_tasks_from_10_to_110(queue: TaskQueue) -> None:
    for i in range(10, 111):
        task = queue.get_task(i)
        queue.delete_task(task)


def move_100_tasks_from_start_to_end(queue: TaskQueue) -> None:
    for _ in range(100):
        task = queue.first_task
        queue.move_task(task, queue.latest_task)


def move_100_tasks_from_end_to_start(queue: TaskQueue) -> None:
    for _ in range(100):
        task = queue.latest_task
        queue.move_task(task, None)


def move_100_tasks_from_middle_to_middle(queue: TaskQueue) -> None:
    start = QUEUE_SIZE // 2
    for i in range(start, start + 100):
        task = queue.get_task(i)
        queue.move_task(task, queue.get_task(QUEUE_SIZE - 1 - i))

PERFORMANCE_FUNCS = [
    get_first_100_tasks,
    get_all_tasks,
    check_existence_of_100_tasks,
    modify_first_100_tasks,
    add_100_tasks_to_start,
    add_100_tasks_to_end,
    remove_100_tasks_from_end,
    remove_100_tasks_from_10_to_110,
    move_100_tasks_from_start_to_end,
    move_100_tasks_from_end_to_start,
    move_100_tasks_from_middle_to_middle,
]


@pytest.mark.skip(reason="Performance tests are skipped by default")
def test_performance(f_large_queue: TaskQueue) -> None:
    with capture_logs() as logs:
        for func in PERFORMANCE_FUNCS:
            measure_performance(f_large_queue, func)
    count = sum("elapsed_time" in log for log in logs)
    assert count == len(PERFORMANCE_FUNCS)
