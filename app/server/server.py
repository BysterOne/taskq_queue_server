import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import logging

from .session import Session

logger = logging.getLogger("TcpServer")


class TcpServer:
    def __init__(self, host, port, config, max_workers=10):
        self.host = host
        self.port = port
        self.config = config
        self.setup_logging()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.sessions = []
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.sessions_lock = threading.Lock()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def start(self):
        try:
            while self.is_running:
                client_socket, addr = self.server_socket.accept()
                if not self.is_running:
                    client_socket.close()
                    break

                session_handler = Session(addr, client_socket, self.config)
                session_handler.on_connected += self.add_session
                session_handler.on_disconnected += self.remove_session
                # Используем пул потоков вместо создания нового потока
                self.executor.submit(session_handler.handle, client_socket)
        except Exception as exc:
            logger.exception(exc, exc_info=True)
        finally:
            self.stop()

    def add_session(self, session):
        with self.sessions_lock:
            self.sessions.append(session)

    def remove_session(self, session):
        with self.sessions_lock:
            self.sessions.remove(session)

    def stop(self):
        if not self.is_running:
            return

        self.is_running = False

        # Закрываем все активные сессии
        with self.sessions_lock:
            for session in self.sessions:
                session.close()

        # Создаем временный сокет для разблокировки accept()
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            temp_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            pass
        finally:
            temp_socket.close()

        self.server_socket.close()
        self.executor.shutdown(wait=True)
        logger.info("Server stopped")
