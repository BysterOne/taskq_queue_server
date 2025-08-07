import time
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor

from client.client import Client
from server.server import TcpServer
from server.serverconfig import ServerConfig
from task_queue.manager import QueueManager


class BaseTestClient(unittest.TestCase):
    def setUp(self):
        QueueManager.clear()
        self.config = ServerConfig()
        self.server = TcpServer('localhost', 9999, self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.start()
        self.client = Client('localhost', 9999)
        self.client.authenticate(self.config.password)
        self.queue1 = QueueManager.create_queue(1)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        self.server_thread.join()
        QueueManager.clear()

class TestClientAuth(unittest.TestCase):
    def setUp(self):
        QueueManager.clear()
        self.config = ServerConfig()
        self.server = TcpServer('localhost', 9999, self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.start()
        self.client = Client('localhost', 9999)

    def tearDown(self):
        self.client.close()
        self.server.stop()
        self.server_thread.join()
        QueueManager.clear()

    def test_auth_ok(self):
        self.client.authenticate(self.config.password)
        self.assertTrue(self.client.is_authenticated)

    def test_auth_fail(self):
        with self.assertRaises(ValueError):
            self.client.authenticate('invalid_password')

class TestClientOperations(BaseTestClient):
    def test_get_task_ok(self):
        employer_id = 1
        task_id = 1
        duration = 68.0
        done_date = 162030.0
        self.client.add_task(employer_id, task_id, duration, done_date)
        task = self.client.get_task(employer_id, task_id)
        self.assertEqual(task.id, task_id)

    def test_get_task_fail(self):
        employer_id = 1
        invalid_task_id = 999
        with self.assertRaises(ValueError):
            self.client.get_task(employer_id, invalid_task_id)

    def test_add_task_ok(self):
        employer_id = 1
        task_id = 1
        duration = 60.0
        done_date = 162030.0
        self.client.add_task(employer_id, task_id, duration, done_date)

    def test_add_task_fail(self):
        employer_id = 1
        task_id = 1
        duration = 60.0
        done_date = 162030.0
        self.client.add_task(employer_id, task_id, duration, done_date)
        with self.assertRaises(ValueError):
            self.client.add_task(employer_id, task_id, duration, done_date)

    def test_delete_task_ok(self):
        employer_id = 1
        task_id = 1
        duration = 60.0
        done_date = 162030.0
        self.client.add_task(employer_id, task_id, duration, done_date)
        next_task_id = self.client.delete_task(employer_id, task_id)
        self.assertEqual(next_task_id, 0)

    def test_delete_task_fail(self):
        employer_id = 1
        invalid_task_id = 999
        with self.assertRaises(ValueError):
            self.client.delete_task(employer_id, invalid_task_id)

    def test_update_task_ok(self):
        employer_id = 1
        task_id = 1
        duration = 120.0
        done_date = 162040.0
        self.client.add_task(employer_id, task_id, 60.0, 162030.0)
        self.client.update_task(employer_id, task_id, duration, done_date)
        task = self.client.get_task(employer_id, 1)
        self.assertEqual(task.id, task_id)
        self.assertEqual(task.duration, duration)
        self.assertEqual(task.done_date, done_date)

    def test_update_task_fail(self):
        employer_id = 1
        invalid_task_id = 999
        duration = 120.0
        done_date = 162040.0
        with self.assertRaises(ValueError):
            self.client.update_task(employer_id, invalid_task_id, duration, done_date)

    def test_get_task_list_ok(self):
        employer_id = 1
        tasks = self.client.get_task_list(employer_id)
        self.assertIsInstance(tasks, list)

    def test_move_task_ok(self):
        employer_id = 1
        task1_id = 1
        task2_id = 2
        task3_id = 3

        start_time = time.time()
        # Adding tasks
        self.client.add_task(employer_id, task1_id, 60.0, 162030.0)
        self.client.add_task(employer_id, task2_id, 120.0, 162040.0)
        self.client.add_task(employer_id, task3_id, 180.0, 162050.0)
        print("time 1", time.time() - start_time)
        start_time = time.time()

        # Move from start to end
        self.client.move_task(employer_id, task1_id, task3_id)
        tasks = self.client.get_task_list(employer_id)
        self.assertEqual([task.id for task in tasks], [2, 3, 1])
        print("time 2", time.time() - start_time)
        start_time = time.time()

        # Move from end to middle
        self.client.move_task(employer_id, task1_id, task2_id)
        tasks = self.client.get_task_list(employer_id)
        self.assertEqual([task.id for task in tasks], [2, 1, 3])
        print("time 3", time.time() - start_time)
        start_time = time.time()

        # Move from middle to start
        self.client.move_task(employer_id, task1_id, 0)
        tasks = self.client.get_task_list(employer_id)
        self.assertEqual([task.id for task in tasks], [1, 2, 3])
        print("time 4", time.time() - start_time)
        start_time = time.time()

        # Move when only one task
        self.client.delete_task(employer_id, task2_id)
        self.client.delete_task(employer_id, task3_id)
        self.client.move_task(employer_id, task1_id, 0)
        tasks = self.client.get_task_list(employer_id)
        print("time 5", time.time() - start_time)

        self.assertEqual([task.id for task in tasks], [1])
        print("time 6", time.time() - start_time)

    def test_move_task_fail(self):
        employer_id = 1
        task_id = 1
        invalid_prev_id = 999
        self.client.add_task(employer_id, task_id, 60.0, 162030.0)
        with self.assertRaises(ValueError):
            self.client.move_task(employer_id, task_id, invalid_prev_id)

    def test_get_first_task_id_ok(self):
        employer_id = 1
        first_task_id = self.client.get_first_task_id(employer_id)
        self.assertIsInstance(first_task_id, int)

    def test_get_latest_task_id_ok(self):
        employer_id = 1
        latest_task_id = self.client.get_latest_task_id(employer_id)
        self.assertIsInstance(latest_task_id, int)

    def test_create_queue_ok(self):
        employer_id = 2
        self.client.create_queue(employer_id)

    def test_create_queue_fail(self):
        employer_id = 2
        self.client.create_queue(employer_id)
        with self.assertRaises(ValueError):
            self.client.create_queue(employer_id)

    def test_delete_queue_ok(self):
        employer_id = 2
        self.client.create_queue(employer_id)
        self.client.delete_queue(employer_id)

    def test_delete_queue_fail(self):
        employer_id = 2
        with self.assertRaises(ValueError):
            self.client.delete_queue(employer_id)


class TestMultithreadedClient(BaseTestClient):
    runner_id = 0
    def test_multithreaded(self):
        def worker(runner_id):
            thread_id = threading.get_ident()
            print(f"{thread_id=} started")
            print(f"{runner_id=} start")
            for i in range(1):
                task_id = runner_id * 100 + i
                self.client.add_task(1, task_id, 60.0, 162030.0)
                self.client.get_task(1, task_id)
                self.client.delete_task(1, task_id)
            print(f"{runner_id=} done")

        futures = []
        for i in range(2):
            futures.append(ThreadPoolExecutor(max_workers=1).submit(worker, i))

        print(f"{len(futures)=}")
        for future in futures:
            future.result()
        print("runned")


if __name__ == '__main__':
    unittest.main()
