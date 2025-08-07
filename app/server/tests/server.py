import threading
import unittest

from server import opcodes
from server.server import TcpServer
from server.serverconfig import ServerConfig
from server.tests.base import BaseTcpServerTest


class TestTcpServer(BaseTcpServerTest):
    def setUp(self):
        self.config = ServerConfig()
        self.server = TcpServer('localhost', 9999, self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.start()
        self.create_session()

    def test_auth_ok(self):
        client = self.auth_session()
        self.assertIsNotNone(client)

    def test_auth_fail(self):
        self.client.write_opcode(opcodes.CMSG_AUTH_REQUEST)
        self.client.write_string("wrong_password")
        self.client.send()

        opcode = self.client.read_opcode()
        self.assertEqual(opcode, opcodes.SMSG_AUTH_RESPONSE)

        result = self.client.read_bool()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()