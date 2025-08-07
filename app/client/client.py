import socket
import threading
from functools import wraps

from app.server.handlers.protocol import Protocol
from server import opcodes
from dataclasses import dataclass


def synchronized(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return wrapper


@dataclass
class Task:
    next_id: int = 0
    prev_id: int = 0
    id: int = 0
    duration: float = 0
    done_date: float = 0


class Packet:
    def __init__(self, opcode, client):
        self.id = threading.get_ident()
        self.write_buffer = bytearray()
        self.read_buffer = bytearray()
        self.client = client

    def __enter__(self):
        # write opcode, id
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def write_int(self, value):
        self.client.write_int(value)

    def read_int(self):
        return self.client.read_int()

    def send(self):
        # send packet
        pass

class Client(Protocol):
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.is_authenticated = False
        self._lock = threading.RLock()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((addr, port))
        super().__init__(client_socket)

    def create_packet(self, opcode):
        return Packet(opcode, self)

    @synchronized
    def authenticate(self, password):
        self.write_opcode(opcodes.CMSG_AUTH_REQUEST)
        self.write_string(password)
        self.send()
        opcode = self.read_opcode()
        result = self.read_bool()
        if opcode != opcodes.SMSG_AUTH_RESPONSE:
            raise ValueError("Unknown auth response opcode")

        if result is not True:
            raise ValueError("Invalid password")

        self.is_authenticated = True

    @synchronized
    def get_task(self, employer_id, task_id) -> Task:
        self.write_opcode(opcodes.CMSG_TASK_GET)
        self.write_int(employer_id)
        self.write_int(task_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK:
            raise ValueError("Unknown task get response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

        task = Task()
        task.id = task_id
        task.prev_id = self.read_int()
        task.next_id = self.read_int()
        task.duration = self.read_float()
        task.done_date = self.read_float()
        return task

    @synchronized
    def add_task(self, employer_id, task_id, duration, done_date, prev_id=None):
        self.write_opcode(opcodes.CMSG_TASK_ADD)
        self.write_int(employer_id)
        self.write_int(task_id)
        self.write_float(duration)
        self.write_float(done_date)
        self.write_int(prev_id or 0)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_ADD:
            raise ValueError("Unknown task add response opcode")

        result = self.read_bool()
        if result is False:
            error_message = self.read_string()
            raise ValueError(error_message)

    @synchronized
    def delete_task(self, employer_id: int, task_id: int) -> int:
        """Delete task by task_id and return next task_id. If next task_id is 0, then task is last in the queue.
        :param employer_id:
        :param task_id:
        :return: next_task_id
        """
        self.write_opcode(opcodes.CMSG_TASK_DELETE)
        self.write_int(employer_id)
        self.write_int(task_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_DELETE:
            raise ValueError("Unknown task delete response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())
        return self.read_int()

    @synchronized
    def update_task(self, employer_id, task_id, duration, done_date):
        self.write_opcode(opcodes.CMSG_TASK_UPDATE)
        self.write_int(employer_id)
        self.write_int(task_id)
        self.write_float(duration)
        self.write_float(done_date)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_UPDATE:
            raise ValueError("Unknown task update response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

    @synchronized
    def get_task_list(self, employer_id: int, from_id: int = None, to_id: int = None) -> list[Task]:
        self.write_opcode(opcodes.CMSG_TASK_LIST)
        self.write_int(employer_id)
        self.write_int(from_id or 0)
        self.write_int(to_id or 0)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_LIST:
            raise ValueError("Unknown task list response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

        prev_task = None
        tasks = []
        while True:
            task_id = self.read_int()
            if task_id == 0:
                break

            task = Task()
            task.id = task_id
            task.duration = self.read_float()
            task.done_date = self.read_float()

            if prev_task is not None:
                prev_task.next_id = task.id
                task.prev_id = prev_task.id

            if prev_task is None:
                prev_task = task

            tasks.append(task)
        return tasks

    @synchronized
    def move_task(self, employer_id, task_id, prev_id):
        self.write_opcode(opcodes.CMSG_TASK_MOVE)
        self.write_int(employer_id)
        self.write_int(task_id)
        self.write_int(prev_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_MOVE:
            raise ValueError("Unknown task move response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

    @synchronized
    def get_first_task_id(self, employer_id):
        self.write_opcode(opcodes.CMSG_TASK_FIRST)
        self.write_int(employer_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_FIRST:
            raise ValueError("Unknown task first response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

        return self.read_int()

    @synchronized
    def get_first_task(self, employer_id):
        task_id = self.get_first_task_id(employer_id)
        return self.get_task(employer_id, task_id)

    @synchronized
    def get_latest_task_id(self, employer_id):
        self.write_opcode(opcodes.CMSG_TASK_LATEST)
        self.write_int(employer_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_TASK_LATEST:
            raise ValueError("Unknown task latest response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

        return self.read_int()

    @synchronized
    def get_latest_task(self, employer_id):
        task_id = self.get_latest_task_id(employer_id)
        return self.get_task(employer_id, task_id)

    @synchronized
    def create_queue(self, employer_id):
        self.write_opcode(opcodes.CMSG_QUEUE_CREATE_REQUEST)
        self.write_int(employer_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_QUEUE_CREATE_RESPONSE:
            raise ValueError("Unknown queue create response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())

    @synchronized
    def delete_queue(self, employer_id):
        self.write_opcode(opcodes.CMSG_QUEUE_DELETE_REQUEST)
        self.write_int(employer_id)
        self.send()

        opcode = self.read_opcode()
        if opcode != opcodes.SMSG_QUEUE_DELETE_RESPONSE:
            raise ValueError("Unknown queue delete response opcode")

        result = self.read_bool()
        if result is False:
            raise ValueError(self.read_string())
