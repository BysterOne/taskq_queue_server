import threading
import unittest

from client.client import Client
from server import opcodes
from server.server import TcpServer
from server.serverconfig import ServerConfig
from task_queue.manager import QueueManager


class BaseTcpServerTest(unittest.TestCase):
    def setUp(self):
        QueueManager.clear()
        self.config = ServerConfig()
        self.server = TcpServer('localhost', 9999, self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.start()
        self.create_session()
        self.auth_session()

    def create_session(self):
        self.client = Client(self.server.host, self.server.port)

    def auth_session(self):
        self.client.write_opcode(opcodes.CMSG_AUTH_REQUEST)
        self.client.write_string(self.config.password)
        self.client.send()

        opcode = self.client.read_opcode()
        if opcode != opcodes.SMSG_AUTH_RESPONSE:
            return

        result = self.client.read_bool()
        if not result:
            return

        return self.client

    def tearDown(self):
        self.client.close()
        self.server.stop()
        self.server_thread.join()
        QueueManager.clear()
