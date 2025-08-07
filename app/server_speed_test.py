import socket
import threading
import time

import structlog

from server.handlers.protocol import Protocol
from settings.logs import configure_logger

configure_logger()
logger = structlog.get_logger('speed_test')


# Серверная часть
def server(host: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    logger.info("Server started and listening")

    conn, addr = server_socket.accept()
    logger.info("Accepted connection", addr=addr)

    protocol = Protocol(conn)

    try:
        while True:
            # Чтение float
            start_read_time = time.time()
            value_float = protocol.read_float()
            end_read_time = time.time()
            logger.info("Server Read float time", duration=end_read_time - start_read_time)

            # Запись float
            start_write_time = time.time()
            protocol.write_float(value_float)
            protocol.send()
            end_write_time = time.time()
            logger.info("Server Write float time", duration=end_write_time - start_write_time)

            # Чтение int
            start_read_time = time.time()
            value_int = protocol.read_int()
            value_int = protocol.read_int()
            value_int = protocol.read_int()
            end_read_time = time.time()
            logger.info("Server Read int time", duration=end_read_time - start_read_time)

            # Запись int
            start_write_time = time.time()
            protocol.write_int(value_int)
            protocol.send()
            end_write_time = time.time()
            logger.info("Server Write int time", duration=end_write_time - start_write_time)

            # Чтение short
            start_read_time = time.time()
            value_short = protocol.read_opcode()
            end_read_time = time.time()
            logger.info("Server Read short time", duration=end_read_time - start_read_time)

            # Запись short
            start_write_time = time.time()
            protocol.write_opcode(value_short)
            protocol.send()
            end_write_time = time.time()
            logger.info("Server Write short time", duration=end_write_time - start_write_time)

            # Чтение bool
            start_read_time = time.time()
            value_bool = protocol.read_bool()
            end_read_time = time.time()
            logger.info("Server Read bool time", duration=end_read_time - start_read_time)

            # Запись bool
            start_write_time = time.time()
            protocol.write_bool(value_bool)
            protocol.send()
            end_write_time = time.time()
            logger.info("Server Write bool time", duration=end_write_time - start_write_time)

            # Чтение string
            start_read_time = time.time()
            value_string = protocol.read_string()
            end_read_time = time.time()
            logger.info("Server Read string time", duration=end_read_time - start_read_time)

            # Запись string
            start_write_time = time.time()
            protocol.write_string(value_string)
            protocol.send()
            end_write_time = time.time()
            logger.info("Server Write string time", duration=end_write_time - start_write_time)

    except ConnectionError:
        pass

    protocol.close()
    server_socket.close()
    logger.info("Server closed connection")


# Клиентская часть
def client(host: str, port: int):
    time.sleep(1)  # Ожидание, чтобы сервер успел запуститься

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    logger.info("Client connected to server")

    protocol = Protocol(client_socket)

    try:
        # Отправка и получение float
        start_time = time.time()
        protocol.write_float(start_time)
        protocol.send()
        logger.info("Client Write float time", duration=time.time() - start_time)

        start_time = time.time()
        response = protocol.read_float()
        logger.info("Client Read float time", duration=time.time() - start_time)

        # Отправка и получение int
        value_int = 123456
        start_time = time.time()
        protocol.write_int(value_int)
        protocol.write_int(value_int)
        protocol.write_int(value_int)
        protocol.send()
        logger.info("Client Write int time", duration=time.time() - start_time)

        start_time = time.time()
        response = protocol.read_int()
        logger.info("Client Read int time", duration=time.time() - start_time)

        # Отправка и получение short
        value_short = 12345
        start_time = time.time()
        protocol.write_opcode(value_short)
        protocol.send()
        logger.info("Client Write short time", duration=time.time() - start_time)

        start_time = time.time()
        response = protocol.read_opcode()
        logger.info("Client Read short time", duration=time.time() - start_time)

        # Отправка и получение bool
        value_bool = True
        start_time = time.time()
        protocol.write_bool(value_bool)
        protocol.send()
        logger.info("Client Write bool time", duration=time.time() - start_time)

        start_time = time.time()
        response = protocol.read_bool()
        logger.info("Client Read bool time", duration=time.time() - start_time)

        # Отправка и получение string
        value_string = "1gasldgnasdjlgnaskdngklasdngkasdljgbnasdngljasdgnads"
        start_time = time.time()
        protocol.write_string(value_string)
        protocol.send()
        logger.info("Client Write string time", duration=time.time() - start_time)

        start_time = time.time()
        response = protocol.read_string()
        logger.info("Client Read string time", duration=time.time() - start_time)

    except ConnectionError:
        pass

    protocol.close()
    logger.info("Client closed connection")


if __name__ == "__main__":
    host = 'localhost'
    port = 9999

    # Запуск сервера в отдельном потоке
    server_thread = threading.Thread(target=server, args=(host, port))
    server_thread.start()

    # Запуск клиента
    client(host, port)

    # Ожидание завершения работы сервера
    server_thread.join()
