import unittest
from datetime import timedelta, datetime

from task_queue.node import TaskNode
from task_queue.queue import TaskQueue
from task_queue.manager import QueueManager

class TestAddTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)
        self.task3 = TaskNode(3, 10)

    def test_add_first_task(self):
        self.queue.add_task(self.task1)
        self.assertEqual(self.queue._first, self.task1)
        self.assertEqual(self.queue._last, self.task1)

    def test_add_task_without_prev(self):
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.assertEqual(self.queue._first, self.task1)
        self.assertEqual(self.queue._last, self.task2)
        self.assertEqual(self.task1.next, self.task2)
        self.assertEqual(self.task2.prev, self.task1)

    def test_add_task_with_prev(self):
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2, self.task1)
        self.assertEqual(self.queue._first, self.task1)
        self.assertEqual(self.queue._last, self.task2)
        self.assertEqual(self.task1.next, self.task2)
        self.assertEqual(self.task2.prev, self.task1)

    def test_add_task_with_invalid_prev(self):
        self.queue.add_task(self.task1)
        with self.assertRaises(ValueError):
            self.queue.add_task(self.task2, self.task3)

    def test_add_existing_task(self):
        self.queue.add_task(self.task1)
        with self.assertRaises(ValueError):
            self.queue.add_task(self.task1)


class TestGetTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)
        self.task3 = TaskNode(3, 10)

    def test_get_task_in_index(self):
        self.queue.add_task(self.task1)
        self.assertEqual(self.queue.get_task(1), self.task1)

    def test_get_task_not_in_index_but_in_queue(self):
        self.queue.add_task(self.task1)
        self.queue._index.delete(1)
        self.assertNotEqual(self.queue.get_task(1), self.task1)
        self.assertIsNone(self.queue.get_task(1))

    def test_get_task_not_in_index_and_not_in_queue(self):
        self.assertIsNone(self.queue.get_task(3))


class TestDelTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)
        self.task3 = TaskNode(3, 10)

    def test_del_task_at_start(self):
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.queue.delete_task(self.task1)
        self.assertEqual(self.queue._first, self.task2)
        self.assertIsNone(self.queue._first.prev)

    def test_del_task_in_middle(self):
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.queue.add_task(self.task3)
        self.queue.delete_task(self.task2)
        self.assertEqual(self.queue._first.next, self.task3)
        self.assertEqual(self.queue._last.prev, self.task1)

    def test_del_task_at_end(self):
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.queue.delete_task(self.task2)
        self.assertEqual(self.queue._last, self.task1)
        self.assertIsNone(self.queue._last.next)

    def test_del_task_not_in_queue(self):
        with self.assertRaises(ValueError):
            self.queue.delete_task(self.task3)


class TestUpdateTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)

    def test_update_task_in_queue(self):
        self.queue.add_task(self.task1)
        self.task1.duration = timedelta(hours=1).total_seconds()
        self.task1.done_date = datetime.now().timestamp()
        self.queue.update_task(self.task1)
        updated_task = self.queue.get_task(1)
        self.assertEqual(updated_task.duration, self.task1.duration)
        self.assertEqual(updated_task.done_date, self.task1.done_date)

    def test_update_task_not_in_queue(self):
        with self.assertRaises(ValueError):
            self.queue.update_task(self.task2)


class TestGetTasks(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)
        self.task3 = TaskNode(3, 10)
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.queue.add_task(self.task3)

    def test_get_all_tasks(self):
        tasks = list(self.queue.get_tasks())
        self.assertEqual(tasks, [self.task1, self.task2, self.task3])

    def test_get_tasks_from_task(self):
        tasks = list(self.queue.get_tasks(from_task=self.task2))
        self.assertEqual(tasks, [self.task2, self.task3])

    def test_get_tasks_to_task(self):
        tasks = list(self.queue.get_tasks(to_task=self.task2))
        self.assertEqual(tasks, [self.task1, self.task2])

    def test_get_tasks_from_task_to_task(self):
        tasks = list(self.queue.get_tasks(from_task=self.task1, to_task=self.task2))
        self.assertEqual(tasks, [self.task1, self.task2])


class TestMoveTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)
        self.task3 = TaskNode(3, 10)
        self.task4 = TaskNode(4, 10)
        self.queue.add_task(self.task1)
        self.queue.add_task(self.task2)
        self.queue.add_task(self.task3)
        self.queue.add_task(self.task4)

        self.task5 = TaskNode(5, 10)

    def test_move_task_from_start_to_middle(self):
        self.queue.move_task(self.task1, self.task2)
        self.assertEqual(list(self.queue.get_tasks()), [self.task2, self.task1, self.task3, self.task4])

    def test_move_task_from_end_to_start(self):
        self.queue.move_task(self.task4, None)
        self.assertEqual(list(self.queue.get_tasks()), [self.task4, self.task1, self.task2, self.task3])

    def test_move_task_from_middle_to_end(self):
        self.queue.move_task(self.task2, self.task4)
        self.assertEqual(list(self.queue.get_tasks()), [self.task1, self.task3, self.task4, self.task2])

    def test_move_task_from_middle_to_middle(self):
        self.queue.move_task(self.task2, self.task3)
        self.assertEqual(list(self.queue.get_tasks()), [self.task1, self.task3, self.task2, self.task4])

    def test_move_task_not_in_queue(self):
        with self.assertRaises(ValueError):
            self.queue.move_task(self.task5, self.task2)


class TestGetFirstAndLastTask(unittest.TestCase):
    def setUp(self):
        self.queue = TaskQueue()
        self.task1 = TaskNode(1, 10)
        self.task2 = TaskNode(2, 10)

    def test_get_first_task(self):
        # Test that getting the first task from an empty queue returns None
        self.assertIsNone(self.queue.first_task)

        # Test that getting the first task from a non-empty queue returns the first task
        self.queue.add_task(self.task1)
        self.assertEqual(self.queue.first_task, self.task1)

        # Test that getting the first task after adding another task still returns the first task
        self.queue.add_task(self.task2)
        self.assertEqual(self.queue.first_task, self.task1)

    def test_get_last_task(self):
        # Test that getting the last task from an empty queue returns None
        self.assertIsNone(self.queue.latest_task)

        # Test that getting the last task from a non-empty queue returns the last task
        self.queue.add_task(self.task1)
        self.assertEqual(self.queue.latest_task, self.task1)

        # Test that getting the last task after adding another task returns the new task
        self.queue.add_task(self.task2)
        self.assertEqual(self.queue.latest_task, self.task2)


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.queue_manager = QueueManager()

    def test_get_queue(self):
        # Test that getting a queue for a non-existent employer_id raises an error
        with self.assertRaises(ValueError):
            self.queue_manager.get_queue(1)

        # Test that getting a queue for an existing employer_id returns the existing queue
        self.queue_manager.create_queue(1)
        queue = self.queue_manager.get_queue(1)
        self.assertIsInstance(queue, TaskQueue)

    def test_create_queue(self):
        # Test that creating a queue for a new employer_id creates a new queue
        queue = self.queue_manager.create_queue(2)
        self.assertIsInstance(queue, TaskQueue)

        # Test that creating a queue for an existing employer_id raises an error
        with self.assertRaises(ValueError):
            self.queue_manager.create_queue(2)

    def test_delete_queue(self):
        # Test that deleting a queue for a non-existent employer_id raises an error
        with self.assertRaises(ValueError):
            self.queue_manager.delete_queue(3)

        # Test that deleting a queue for an existing employer_id removes the queue
        self.queue_manager.create_queue(3)
        self.queue_manager.delete_queue(3)

        with self.assertRaises(ValueError):
            self.queue_manager.get_queue(3)


if __name__ == '__main__':
    unittest.main()
