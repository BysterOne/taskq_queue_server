
from task_queue.manager import QueueManager
from task_queue.node import TaskNode
from task_queue.queue import TaskQueue

from .. import opcodes
from ..opcode_utils import register
from .base_handler import BaseHandler


def is_authenticated(session):
    if not session.is_authenticated:
        raise ValueError("You must be authenticated to perform this action.")


class BaseTaskHandler(BaseHandler):
    return_opcode: int = 0
    permissions = [
        is_authenticated,
    ]
    def handle(self):
        try:
            self.check_permissions()
            employer_id = self.session.read_int()

            self.session.write_opcode(self.return_opcode)
            queue = QueueManager.get_queue(employer_id)
            self.execute_command(queue)
        except ValueError as e:
            self.session.flush_buffer()
            self.session.write_bool(False)
            self.session.write_string(str(e))
            self.session.send()


    def execute_command(self, queue):
        raise NotImplementedError

    def check_permissions(self):
        for permission in self.permissions:
            if permission(self.session) is False:
                return False

        return True

@register(opcodes.CMSG_TASK_GET)
class TaskGetRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK

    def execute_command(self, queue):
        task_id = self.session.read_int()

        task = queue.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")

        self.session.write_bool(True)
        self.session.write_int(task.prev.id if task.prev else 0)
        self.session.write_int(task.next.id if task.next else 0)
        self.session.write_float(task.duration)
        self.session.write_float(task.done_date if task.done_date else 0)
        self.session.send()

@register(opcodes.CMSG_TASK_ADD)
class TaskAddRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_ADD

    def execute_command(self, queue):
        task_id = self.session.read_int()
        duration = self.session.read_float()
        done_date = self.session.read_float()
        prev_task_id = self.session.read_int()

        prev_task = queue.get_task(prev_task_id)
        if prev_task is None and prev_task_id != 0:
            raise ValueError("'prev_task_id' is invalid. May be the task not in the queue.")

        task = TaskNode(task_id, duration, done_date)
        queue.add_task(task, prev_task)
        self.session.write_bool(True)
        self.session.send()


@register(opcodes.CMSG_TASK_DELETE)
class TaskDeleteRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_DELETE

    def execute_command(self, queue):
        task_id = self.session.read_int()

        task = queue.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")

        next_task = queue.delete_task(task)

        self.session.write_bool(True)
        self.session.write_int(next_task.id if next_task else 0)
        self.session.send()


@register(opcodes.CMSG_TASK_UPDATE)
class TaskUpdateRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_UPDATE

    def execute_command(self, queue):
        task_id = self.session.read_int()
        duration = self.session.read_float()
        done_date = self.session.read_float()

        task = queue.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")
        task.duration = duration
        task.done_date = done_date

        self.session.write_bool(True)
        self.session.send()


@register(opcodes.CMSG_TASK_LIST)
class TaskListRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_LIST

    def execute_command(self, queue):
        from_task_id = self.session.read_int()
        to_task_id = self.session.read_int()

        from_task = queue.get_task(from_task_id)
        if from_task is None and from_task_id != 0:
            raise ValueError("'from_task_id' is invalid. May be the task not in the queue.")

        to_task = queue.get_task(to_task_id)
        if to_task is None and to_task_id != 0:
            raise ValueError("'to_task_id' is invalid. May be the task not in the queue.")

        self.session.write_bool(True)
        for task in queue.get_tasks(from_task, to_task):
            self.session.write_int(task.id)
            self.session.write_float(task.duration)
            self.session.write_float(task.done_date if task.done_date else 0)

        self.session.write_int(0)
        self.session.send()


@register(opcodes.CMSG_TASK_MOVE)
class TaskMoveRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_MOVE

    def execute_command(self, queue):
        task_id = self.session.read_int()
        prev_task_id = self.session.read_int()

        task = queue.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")

        prev_task = queue.get_task(prev_task_id)
        if prev_task is None and prev_task_id != 0:
            raise ValueError("'prev_task_id' is invalid. May be the task not in the queue.")

        queue.move_task(task, prev_task)
        self.session.write_bool(True)
        self.session.send()


@register(opcodes.CMSG_TASK_FIRST)
class TaskFirstRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_FIRST

    def execute_command(self, queue: TaskQueue):
        task = queue.first_task
        self.session.write_bool(True)
        self.session.write_int(task.id if task else 0)
        self.session.send()


@register(opcodes.CMSG_TASK_LATEST)
class TaskLatestRequestHandler(BaseTaskHandler):
    return_opcode = opcodes.SMSG_TASK_LATEST

    def execute_command(self, queue: TaskQueue):
        task = queue.latest_task
        self.session.write_bool(True)
        self.session.write_int(task.id if task else 0)
        self.session.send()
