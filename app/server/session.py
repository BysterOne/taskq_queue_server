import threading
import time
from socket import socket

import structlog

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
        self.logger = structlog.get_logger("Session")
        self.on_connected = Event()
        self.on_disconnected = Event()
        self.is_authenticated = False
        self.lock = threading.Lock()
        self._read_buffer = b''


    def handle(self, client_socket):
        try:
            self.logger.info('Client connected', addr=self.addr)
            self.on_connected(self)
            while self.is_connected:
                self.lock.acquire(True, 1)
                start_time = time.time()
                opcode = self.read_opcode()
                self.logger.info('Received opcode', opcode=opcode, duration=time.time() - start_time)

                start_time = time.time()
                if opcode not in opcodes_map:
                    self.logger.warning('Unknown opcode', opcode=opcode)
                    break

                handler = opcodes_map[opcode](self)
                handler.handle()
                self.logger.info('Opcode handled', opcode=opcode, duration=time.time() - start_time)
                self.lock.release()
        except DisconnectedException:
            # произошел дисконнект, ничего делать не нужно
            pass
        except ConnectionResetError:
            pass
        except ServerException as exc:
            self.logger.exception('server error')
        except Exception:
            self.logger.exception('unexpected error')
        finally:
            client_socket.close()
            self.logger.info('Client disconnected', addr=self.addr)
            self.on_disconnected(self)
            if self.lock.locked():
                self.lock.release()
