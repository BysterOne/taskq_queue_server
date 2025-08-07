import os


class ServerConfig:
    password: str = os.getenv("QSERVER_PASSWORD", "password")


