import socket
import threading
import time
import logging

from server.handlers.protocol import Protocol

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


# Серверная часть
def server(host: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    logging.info("Server started and listening")

    conn, addr = server_socket.accept()
    logging.info(f"Accepted connection from {addr}")

    protocol = Protocol(conn)

    try:
        while True:
            # Чтение float
            start_read_time = time.time()
            value_float = protocol.read_float()
            end_read_time = time.time()
            logging.info(f"Server Read float time: {end_read_time - start_read_time:.4f} seconds")

            # Запись float
            start_write_time = time.time()
            protocol.write_float(value_float)
            protocol.send()
            end_write_time = time.time()
            logging.info(f"Server Write float time: {end_write_time - start_write_time:.4f} seconds")

            # Чтение int
            start_read_time = time.time()
            value_int = protocol.read_int()
            value_int = protocol.read_int()
            value_int = protocol.read_int()
            end_read_time = time.time()
            logging.info(f"Server Read int time: {end_read_time - start_read_time:.4f} seconds")

            # Запись int
            start_write_time = time.time()
            protocol.write_int(value_int)
            protocol.send()
            end_write_time = time.time()
            logging.info(f"Server Write int time: {end_write_time - start_write_time:.4f} seconds")

            # Чтение short
            start_read_time = time.time()
            value_short = protocol.read_opcode()
            end_read_time = time.time()
            logging.info(f"Server Read short time: {end_read_time - start_read_time:.4f} seconds")

            # Запись short
            start_write_time = time.time()
            protocol.write_opcode(value_short)
            protocol.send()
            end_write_time = time.time()
            logging.info(f"Server Write short time: {end_write_time - start_write_time:.4f} seconds")

            # Чтение bool
            start_read_time = time.time()
            value_bool = protocol.read_bool()
            end_read_time = time.time()
            logging.info(f"Server Read bool time: {end_read_time - start_read_time:.4f} seconds")

            # Запись bool
            start_write_time = time.time()
            protocol.write_bool(value_bool)
            protocol.send()
            end_write_time = time.time()
            logging.info(f"Server Write bool time: {end_write_time - start_write_time:.4f} seconds")

            # Чтение string
            start_read_time = time.time()
            value_string = protocol.read_string()
            end_read_time = time.time()
            logging.info(f"Server Read string time: {end_read_time - start_read_time:.4f} seconds")

            # Запись string
            start_write_time = time.time()
            protocol.write_string(value_string)
            protocol.send()
            end_write_time = time.time()
            logging.info(f"Server Write string time: {end_write_time - start_write_time:.4f} seconds")

    except ConnectionError:
        pass

    protocol.close()
    server_socket.close()
    logging.info("Server closed connection")


# Клиентская часть
def client(host: str, port: int):
    time.sleep(1)  # Ожидание, чтобы сервер успел запуститься

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    logging.info("Client connected to server")

    protocol = Protocol(client_socket)

    try:
        # Отправка и получение float
        start_time = time.time()
        protocol.write_float(start_time)
        protocol.send()
        logging.info(f"Client Write float time: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        response = protocol.read_float()
        logging.info(f"Client Read float time: {time.time() - start_time:.4f} seconds")

        # Отправка и получение int
        value_int = 123456
        start_time = time.time()
        protocol.write_int(value_int)
        protocol.write_int(value_int)
        protocol.write_int(value_int)
        protocol.send()
        logging.info(f"Client Write int time: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        response = protocol.read_int()
        logging.info(f"Client Read int time: {time.time() - start_time:.4f} seconds")

        # Отправка и получение short
        value_short = 12345
        start_time = time.time()
        protocol.write_opcode(value_short)
        protocol.send()
        logging.info(f"Client Write short time: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        response = protocol.read_opcode()
        logging.info(f"Client Read short time: {time.time() - start_time:.4f} seconds")

        # Отправка и получение bool
        value_bool = True
        start_time = time.time()
        protocol.write_bool(value_bool)
        protocol.send()
        logging.info(f"Client Write bool time: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        response = protocol.read_bool()
        logging.info(f"Client Read bool time: {time.time() - start_time:.4f} seconds")

        # Отправка и получение string
        value_string = "1gasldgnasdjlgnaskdngklasdngkasdljgbnasdngljasdgnads"
        start_time = time.time()
        protocol.write_string(value_string)
        protocol.send()
        logging.info(f"Client Write string time: {time.time() - start_time:.4f} seconds")

        start_time = time.time()
        response = protocol.read_string()
        logging.info(f"Client Read string time: {time.time() - start_time:.4f} seconds")

    except ConnectionError:
        pass

    protocol.close()
    logging.info("Client closed connection")


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
