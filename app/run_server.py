import logging
import os

from server.server import TcpServer
from server.serverconfig import ServerConfig

logger = logging.getLogger("TcpServer")

def main():
    port = int(os.getenv("QSERVER_PORT", 9999))
    config = ServerConfig()
    server = TcpServer("0.0.0.0", port, config)
    logger.info(f"starting server on {server.host}:{server.port}")
    server.start()

if __name__ == '__main__':
    main()
