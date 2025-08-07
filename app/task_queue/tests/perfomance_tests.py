import time
import unittest
from memory_profiler import memory_usage
from task_queue.node import TaskNode
from task_queue.queue import TaskQueue

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        for i in range(1, 10000001):
            task = TaskNode(i, 10)
            self.queue.add_task(task)

    # noinspection PyMethodMayBeStatic
    def measure_performance(self, func, *args, **kwargs):
        start_memory = memory_usage()[0]
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        end_memory = memory_usage()[0]
        elapsed_time = end_time - start_time
        used_memory = end_memory - start_memory
        print(f"{func.__name__}: Time elapsed: {elapsed_time} seconds, Memory used: {used_memory} MiB")

    def test_performance(self):
        self.measure_performance(self.get_first_100_tasks)
        self.measure_performance(self.get_all_tasks)
        self.measure_performance(self.check_existence_of_100_tasks)
        self.measure_performance(self.modify_first_100_tasks)
        self.measure_performance(self.add_100_tasks_to_start)
        self.measure_performance(self.add_100_tasks_to_end)
        self.measure_performance(self.remove_100_tasks_from_end)
        self.measure_performance(self.remove_100_tasks_from_10_to_110)
        self.measure_performance(self.move_100_tasks_from_start_to_end)
        self.measure_performance(self.move_100_tasks_from_end_to_start)
        self.measure_performance(self.move_100_tasks_from_middle_to_middle)


    def modify_first_100_tasks(self):
        for i in range(1, 101):
            task = self.queue.get_task(i)
            task.id += 1000
            self.queue.update_task(task)

    def add_100_tasks_to_start(self):
        for i in range(10000001, 10000101):
            task = TaskNode(i, 10)
            self.queue.add_task(task, None)

    def add_100_tasks_to_end(self):
        for i in range(10000101, 10000201):
            task = TaskNode(i, 10)
            self.queue.add_task(task)

    def remove_100_tasks_from_end(self):
        for _ in range(100):
            self.queue.delete_task(self.queue.latest_task)

    def remove_100_tasks_from_10_to_110(self):
        for i in range(10, 111):
            task = self.queue.get_task(i)
            self.queue.delete_task(task)

    def move_100_tasks_from_start_to_end(self):
        for _ in range(100):
            task = self.queue.first_task
            self.queue.move_task(task, self.queue.latest_task)

    def move_100_tasks_from_end_to_start(self):
        for _ in range(100):
            task = self.queue.latest_task
            self.queue.move_task(task, None)

    def move_100_tasks_from_middle_to_middle(self):
        for i in range(500000, 500100):
            task = self.queue.get_task(i)
            self.queue.move_task(task, self.queue.get_task(999999 - i))

    def get_first_100_tasks(self):
        list(self.queue.get_tasks(to_task=self.queue.get_task(100)))

    def get_all_tasks(self):
        list(self.queue.get_tasks())

    def check_existence_of_100_tasks(self):
        for i in range(3000, 4001):
            assert self.queue.task_exists(i)

if __name__ == "__main__":
    unittest.main()
