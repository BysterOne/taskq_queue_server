import logging
import threading
import time
from socket import socket

from utils.events import Event
from .handlers.exceptions import ServerException, DisconnectedException
from .handlers.protocol import Protocol
from .opcode_utils import opcodes_map
from .serverconfig import ServerConfig


class Session(Protocol):
    def __init__(self, addr, client_socket: socket, config: 'ServerConfig'):
        super().__init__(client_socket)
        self.addr = addr
        self.config = config
        self.logger = logging.getLogger("Session")
        self.on_connected = Event()
        self.on_disconnected = Event()
        self.is_authenticated = False
        self.lock = threading.Lock()
        self._read_buffer = b''


    def handle(self, client_socket):
        try:
            self.logger.info(f"Client {self.addr} connected")
            self.on_connected(self)
            while self.is_connected:
                self.lock.acquire(True, 1)
                start_time = time.time()
                opcode = self.read_opcode()
                self.logger.info(f"Received opcode {opcode} in {time.time() - start_time:.4f} seconds")

                start_time = time.time()
                if opcode not in opcodes_map:
                    self.logger.warning(f"Unknown opcode: {opcode}")
                    break

                handler = opcodes_map[opcode](self)
                handler.handle()
                self.logger.info(f"Opcode {opcode} handled in {time.time() - start_time:.4f} seconds")
                self.lock.release()
        except DisconnectedException:
            # произошел дисконнект, ничего делать не нужно
            pass
        except ConnectionResetError:
            pass
        except ServerException as exc:
            self.logger.exception(exc, exc_info=True)
        except Exception as exc:
            self.logger.exception(exc, exc_info=True)
        finally:
            client_socket.close()
            self.logger.info(f"Client {self.addr} disconnected")
            self.on_disconnected(self)
            if self.lock.locked():
                self.lock.release()
