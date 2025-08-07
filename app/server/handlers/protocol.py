import socket
import struct
import threading

from .exceptions import DisconnectedException, ServerException


class Buffer:
    def __init__(self):
        self.read_buffer = bytearray()
        self.write_buffer = bytearray()


class Protocol:
    def __init__(self, client_socket: socket.socket) -> None:
        """
        Инициализация протокола.

        :param client_socket: сокет клиента
        """
        self.client_socket = client_socket
        self.is_connected = True
        self._buffers = {}
        self._write_buffer = b''
        self._read_buffer = b''

    def _get_buffer(self) -> Buffer:
        thread_id = threading.get_ident()
        if thread_id not in self._buffers:
            self._buffers[thread_id] = Buffer()

        return self._buffers[thread_id]
        
    def read_buffer(self):
        """
        Чтение данных из сокета.

        :return: прочитанные данные
        """
        try:
            packet = self.client_socket.recv(1024)
            if not packet:
                self.is_connected = False
                raise DisconnectedException("Connection closed by the peer")
        except socket.error as e:
            self.is_connected = False
            raise ServerException(f"Error reading from socket: {e}")
        self._read_buffer += packet


    def read(self, size: int) -> bytes:
        """
        Чтение данных из буфера.

        :param size: количество байтов для чтения
        :return: прочитанные данные
        """
        data = b''
        while True:
            packet = self._read_buffer[:size - len(data)]
            self._read_buffer = self._read_buffer[size - len(data):]
            data += packet
            length = len(data)
            if length == size:
                return data
            if length > size:
                raise ValueError("Data too big")
            self.read_buffer()

    def write(self, data: bytes) -> None:
        """
        Запись данных в сокет.

        :param data: данные для записи
        """
        self._write_buffer += data

    def read_opcode(self) -> int:
        """
        Чтение опкода из сокета.

        :return: прочитанное число
        """
        return struct.unpack('h', self.read(2))[0]

    def write_opcode(self, value: int) -> None:
        """
        Запись короткого целого числа в сокет.

        :param value: число для записи
        """
        self.write(struct.pack('h', value))

    def read_int(self) -> int:
        """
        Чтение целого числа из сокета.

        :return: прочитанное число
        """
        return struct.unpack('i', self.read(4))[0]

    def write_int(self, value: int) -> None:
        """
        Запись целого числа в сокет.

        :param value: число для записи
        """
        self.write(struct.pack('i', value))

    def read_float(self) -> float:
        """
        Чтение числа с плавающей точкой из сокета.

        :return: прочитанное число
        """
        return struct.unpack('d', self.read(8))[0]

    def write_float(self, value: float) -> None:
        """
        Запись числа с плавающей точкой в сокет.

        :param value: число для записи
        """
        self.write(struct.pack('d', value))

    def read_bool(self) -> bool:
        """
        Чтение булевого значения из сокета.

        :return: прочитанное значение
        """
        return struct.unpack('?', self.read(1))[0]

    def write_bool(self, value: bool) -> None:
        """
        Запись булевого значения в сокет.

        :param value: значение для записи
        """
        self.write(struct.pack('?', value))

    def read_int64(self) -> int:
        """
        Чтение 64-битного целого числа из сокета.

        :return: прочитанное число
        """
        return struct.unpack('q', self.read(8))[0]

    def write_int64(self, value: int) -> None:
        """
        Запись 64-битного целого числа в сокет.

        :param value: число для записи
        """
        self.write(struct.pack('q', value))

    def read_string(self) -> str:
        """
        Чтение строки из сокета.

        :return: прочитанная строка
        """
        length = self.read_int()
        return self.read(length).decode('utf-8')

    def write_string(self, value: str) -> None:
        """
        Запись строки в сокет.

        :param value: строка для записи
        """
        encoded_value = value.encode('utf-8')
        self.write_int(len(encoded_value))
        self.write(encoded_value)

    def close(self) -> None:
        """
        Закрытие сокета.
        """
        self.is_connected = False
        self.client_socket.close()

    def flush_buffer(self) -> None:
        """
        Очистка буфера.
        """
        self.client_socket.setblocking(False)
        while True:
            try:
                self.client_socket.recv(4096)
            except BlockingIOError:
                break
        self.client_socket.setblocking(True)
    
    def send(self):
        self.client_socket.sendall(self._write_buffer)
        self._write_buffer = b""
