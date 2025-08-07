from server import opcodes
from server.tests.base import BaseTcpServerTest
from task_queue.manager import QueueManager
from task_queue.node import TaskNode


# noinspection DuplicatedCode
class TestTaskGetRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.queue2 = QueueManager.create_queue(2)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue2.add_task(self.task2)

    def test_get_task(self):
        """
        CMSG_TASK_GET:employer_id:task_id
        SMSG_TASK:task_id:result(bool, 1):prev_id:nest_id:duration:done_date
        """
        self.client.write_opcode(opcodes.CMSG_TASK_GET)
        self.client.write_int(1)
        self.client.write_int(1)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK)

        result = self.client.read_bool()
        self.assertTrue(result)

        prev_id = self.client.read_int()
        self.assertEqual(prev_id, 0)

        next_id = self.client.read_int()
        self.assertEqual(next_id, 0)

        duration = self.client.read_float()
        self.assertEqual(duration, 10)

        done_date = self.client.read_float()
        self.assertEqual(done_date, 0)

    def test_get_task_not_found(self):
        """
        CMSG_TASK_GET:employer_id:task_id
        SMSG_TASK:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_GET)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')

    def test_get_task_invalid_queue(self):
        """
        CMSG_TASK_GET:employer_id:task_id
        SMSG_TASK:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_GET)
        self.client.write_int(1)
        self.client.write_int(2)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')


# noinspection DuplicatedCode
class TestTaskAddRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)

    def test_add_task(self):
        """
        CMSG_TASK_ADD:employer_id:task_id:duration:done_date
        SMSG_TASK_ADD:task_id:result(bool, 1)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_ADD)
        self.client.write_int(1) # queue_id
        self.client.write_int(3) # task_id
        self.client.write_float(10)
        self.client.write_float(0)
        self.client.write_int(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_ADD)

        result = self.client.read_bool()
        self.assertTrue(result)

    def test_add_task_invalid_queue(self):
        """
        CMSG_TASK_ADD:employer_id:task_id:duration:done_date
        SMSG_TASK_ADD:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_ADD)
        self.client.write_int(2) # queue_id
        self.client.write_int(3) # task_id
        self.client.write_float(10)
        self.client.write_float(0)
        self.client.write_int(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_ADD)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')

    def test_add_task_prev_task(self):
        """
        CMSG_TASK_ADD:employer_id:task_id:duration:done_date
        SMSG_TASK_ADD:task_id:result(bool, 1)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_ADD)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.write_float(10)
        self.client.write_float(0)
        self.client.write_int(1)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_ADD)

        result = self.client.read_bool()
        self.assertTrue(result)

        tasks = list(self.queue1.get_tasks())
        self.assertEqual([task.id for task in tasks], [1, 3, 2])

    def test_add_task_invalid_prev_task(self):
        """
        CMSG_TASK_ADD:employer_id:task_id:duration:done_date
        SMSG_TASK_ADD:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_ADD)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.write_float(10)
        self.client.write_float(0)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_ADD)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, "'prev_task_id' is invalid. May be the task not in the queue.")


# noinspection DuplicatedCode
class TestTaskDeleteRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)

    def test_delete_task(self):
        """
        CMSG_TASK_DELETE:employer_id:task_id
        SMSG_TASK_DELETE:task_id:result(bool, 1)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_DELETE)
        self.client.write_int(1)
        self.client.write_int(2)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_DELETE)

        result = self.client.read_bool()
        self.assertTrue(result)

        tasks = list(self.queue1.get_tasks())
        self.assertEqual([task.id for task in tasks], [1])

    def test_delete_task_not_found(self):
        """
        CMSG_TASK_DELETE:employer_id:task_id
        SMSG_TASK_DELETE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_DELETE)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_DELETE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')

    def test_delete_task_invalid_queue(self):
        """
        CMSG_TASK_DELETE:employer_id:task_id
        SMSG_TASK_DELETE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_DELETE)
        self.client.write_int(2)
        self.client.write_int(2)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_DELETE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')


# noinspection DuplicatedCode
class TestTaskUpdateRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)

    def test_update_task(self):
        """
        CMSG_TASK_UPDATE:employer_id:task_id:duration:done_date
        SMSG_TASK_UPDATE:task_id:result(bool, 1)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_UPDATE)
        self.client.write_int(1)
        self.client.write_int(2)
        self.client.write_float(20)
        self.client.write_float(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_UPDATE)

        result = self.client.read_bool()
        self.assertTrue(result)

        task = self.queue1.get_task(2)
        self.assertEqual(task.duration, 20)

    def test_update_task_not_found(self):
        """
        CMSG_TASK_UPDATE:employer_id:task_id:duration:done_date
        SMSG_TASK_UPDATE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_UPDATE)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.write_float(20)
        self.client.write_float(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_UPDATE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')

    def test_update_task_invalid_queue(self):
        """
        CMSG_TASK_UPDATE:employer_id:task_id:duration:done_date
        SMSG_TASK_UPDATE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_UPDATE)
        self.client.write_int(2)
        self.client.write_int(2)
        self.client.write_float(20)
        self.client.write_float(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_UPDATE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')


# noinspection DuplicatedCode
class TestTaskListRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)
        self.task3 = TaskNode(3, 10)
        self.queue1.add_task(self.task3)

    def test_list_tasks(self):
        """
        CMSG_TASK_LIST:employer_id:from_task_id:to_task_id
        SMSG_TASK_LIST:result(bool, 1):[task_id:duration:done_date]:0
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LIST)
        self.client.write_int(1)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LIST)

        result = self.client.read_bool()
        self.assertTrue(result)

        tasks = []
        while True:
            task_id = self.client.read_int()
            if task_id == 0:
                break
            duration = self.client.read_float()
            done_date = self.client.read_float()
            tasks.append((task_id, duration, done_date))

        self.assertEqual(tasks, [(1, 10, 0), (2, 10, 0), (3, 10, 0)])

    def test_list_all_tasks(self):
        """
        CMSG_TASK_LIST:employer_id:from_task_id:to_task_id
        SMSG_TASK_LIST:result(bool, 1):[task_id:duration:done_date]:0
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LIST)
        self.client.write_int(1)
        self.client.write_int(0)
        self.client.write_int(0)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LIST)

        result = self.client.read_bool()
        self.assertTrue(result)

        tasks = []
        while True:
            task_id = self.client.read_int()
            if task_id == 0:
                break
            duration = self.client.read_float()
            done_date = self.client.read_float()
            tasks.append((task_id, duration, done_date))

        self.assertEqual(tasks, [(1, 10, 0), (2, 10, 0), (3, 10, 0)])

    def test_list_tasks_not_found(self):
        """
        CMSG_TASK_LIST:employer_id:from_task_id:to_task_id
        SMSG_TASK_LIST:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LIST)
        self.client.write_int(1)
        self.client.write_int(4)
        self.client.write_int(5)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LIST)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, "'from_task_id' is invalid. May be the task not in the queue.")

    def test_list_tasks_invalid_queue(self):
        """
        CMSG_TASK_LIST:employer_id:from_task_id:to_task_id
        SMSG_TASK_LIST:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LIST)
        self.client.write_int(2)
        self.client.write_int(1)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LIST)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')

    def test_list_tasks_invalid_from_task(self):
        """
        CMSG_TASK_LIST:employer_id:from_task_id:to_task_id
        SMSG_TASK_LIST:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LIST)
        self.client.write_int(1)
        self.client.write_int(4)
        self.client.write_int(3)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LIST)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, "'from_task_id' is invalid. May be the task not in the queue.")


# noinspection DuplicatedCode
class TestTaskMoveRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)
        self.task3 = TaskNode(3, 10)
        self.queue1.add_task(self.task3)
        self.task4 = TaskNode(4, 10)
        self.queue1.add_task(self.task4)

    def test_move_task(self):
        """
        CMSG_TASK_MOVE:employer_id:task_id:prev_task_id
        SMSG_TASK_MOVE:task_id:result(bool, 1)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.client.write_int(1)
        self.client.write_int(2)
        self.client.write_int(4)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_MOVE)

        result = self.client.read_bool()
        self.assertTrue(result)

        tasks = list(self.queue1.get_tasks())
        self.assertEqual([task.id for task in tasks], [1, 3, 4, 2])

    def test_move_task_not_found(self):
        """
        CMSG_TASK_MOVE:employer_id:task_id:prev_task_id
        SMSG_TASK_MOVE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.client.write_int(1)
        self.client.write_int(5)
        self.client.write_int(4)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_MOVE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')

    def test_move_task_invalid_queue(self):
        """
        CMSG_TASK_MOVE:employer_id:task_id:prev_task_id
        SMSG_TASK_MOVE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.client.write_int(2)
        self.client.write_int(2)
        self.client.write_int(4)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_MOVE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')

    def test_move_task_invalid_prev_task(self):
        """
        CMSG_TASK_MOVE:employer_id:task_id:prev_task_id
        SMSG_TASK_MOVE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.client.write_int(1)
        self.client.write_int(2)
        self.client.write_int(5)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_MOVE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, "'prev_task_id' is invalid. May be the task not in the queue.")

    def test_move_task_invalid_task(self):
        """
        CMSG_TASK_MOVE:employer_id:task_id:prev_task_id
        SMSG_TASK_MOVE:task_id:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.client.write_int(1)
        self.client.write_int(5)
        self.client.write_int(4)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_MOVE)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'Task not found.')


# noinspection DuplicatedCode
class TestFirstAndLatestTaskRequestHandler(BaseTcpServerTest):
    def setUp(self):
        super().setUp()
        self.queue1 = QueueManager.create_queue(1)
        self.task1 = TaskNode(1, 10)
        self.queue1.add_task(self.task1)
        self.task2 = TaskNode(2, 10)
        self.queue1.add_task(self.task2)
        self.task3 = TaskNode(3, 10)
        self.queue1.add_task(self.task3)

    def test_first_task(self):
        """
        CMSG_FIRST_TASK:employer_id
        SMSG_FIRST_TASK:task_id:result(bool, 1):task_id
        """
        self.client.write_opcode(opcodes.CMSG_TASK_FIRST)
        self.client.write_int(1)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_FIRST)

        result = self.client.read_bool()
        self.assertTrue(result)

        task_id = self.client.read_int()
        self.assertEqual(task_id, 1)


    def test_first_task_not_found(self):
        """
        CMSG_FIRST_TASK:employer_id
        SMSG_FIRST_TASK:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_FIRST)
        self.client.write_int(2)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_FIRST)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')

    def test_latest_task(self):
        """
        CMSG_LATEST_TASK:employer_id
        SMSG_LATEST_TASK:result(bool, 1):task_id
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LATEST)
        self.client.write_int(1)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LATEST)

        result = self.client.read_bool()
        self.assertTrue(result)

        task_id = self.client.read_int()
        self.assertEqual(task_id, 3)

    def test_latest_task_not_found(self):
        """
        CMSG_LATEST_TASK:employer_id
        SMSG_LATEST_TASK:result(bool, 0):error(string)
        """
        self.client.write_opcode(opcodes.CMSG_TASK_LATEST)
        self.client.write_int(2)
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_TASK_LATEST)

        result = self.client.read_bool()
        self.assertFalse(result)

        error = self.client.read_string()
        self.assertEqual(error, 'No queue for employer_id 2')
