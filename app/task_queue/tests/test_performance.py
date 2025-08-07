import time
import pytest
from task_queue.node import TaskNode
from task_queue.queue import TaskQueue

memory_usage = pytest.importorskip("memory_profiler").memory_usage


@pytest.fixture
def f_large_queue() -> TaskQueue:
    queue = TaskQueue()
    for i in range(1, 10000001):
        queue.add_task(TaskNode(i, 10))
    return queue


def measure_performance(queue: TaskQueue, func, *args) -> None:
    start_memory = memory_usage()[0]
    start_time = time.time()
    func(queue, *args)
    elapsed_time = time.time() - start_time
    used_memory = memory_usage()[0] - start_memory
    print(f"{func.__name__}: Time elapsed: {elapsed_time} seconds, Memory used: {used_memory} MiB")


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
    for i in range(10000001, 10000101):
        queue.add_task(TaskNode(i, 10), None)


def add_100_tasks_to_end(queue: TaskQueue) -> None:
    for i in range(10000101, 10000201):
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
    for i in range(500000, 500100):
        task = queue.get_task(i)
        queue.move_task(task, queue.get_task(999999 - i))


@pytest.mark.skip(reason="performance test")
def test_performance(f_large_queue: TaskQueue) -> None:
    measure_performance(f_large_queue, get_first_100_tasks)
    measure_performance(f_large_queue, get_all_tasks)
    measure_performance(f_large_queue, check_existence_of_100_tasks)
    measure_performance(f_large_queue, modify_first_100_tasks)
    measure_performance(f_large_queue, add_100_tasks_to_start)
    measure_performance(f_large_queue, add_100_tasks_to_end)
    measure_performance(f_large_queue, remove_100_tasks_from_end)
    measure_performance(f_large_queue, remove_100_tasks_from_10_to_110)
    measure_performance(f_large_queue, move_100_tasks_from_start_to_end)
    measure_performance(f_large_queue, move_100_tasks_from_end_to_start)
    measure_performance(f_large_queue, move_100_tasks_from_middle_to_middle)
