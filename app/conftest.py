import sys
import threading
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent))


from client.client import Client  # noqa: E402
from server.server import TcpServer  # noqa: E402
from server.serverconfig import ServerConfig  # noqa: E402
from task_queue.manager import QueueManager  # noqa: E402
from task_queue.node import TaskNode  # noqa: E402


@pytest.fixture(autouse=True)
def f_clear_queue_manager() -> None:
    QueueManager.clear()
    yield
    QueueManager.clear()


@pytest.fixture
def f_server_config() -> ServerConfig:
    return ServerConfig()


@pytest.fixture
def f_server(f_server_config: ServerConfig):
    srv = TcpServer("localhost", 9999, f_server_config)
    thread = threading.Thread(target=srv.start)
    thread.start()
    yield srv
    srv.stop()
    thread.join()


@pytest.fixture
def f_client(f_server: TcpServer) -> Client:
    cli = Client("localhost", 9999)
    yield cli
    cli.close()


@pytest.fixture
def f_auth_client(f_client: Client, f_server_config: ServerConfig) -> Client:
    f_client.authenticate(f_server_config.password)
    return f_client


@pytest.fixture
def f_queue_factory():
    def _create(queue_id: int):
        return QueueManager.create_queue(queue_id)

    return _create


@pytest.fixture
def f_task_factory():
    def _create(task_id: int, duration: float = 10):
        return TaskNode(task_id, duration)

    return _create
