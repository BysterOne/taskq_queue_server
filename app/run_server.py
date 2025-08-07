import os

import structlog

from server.server import TcpServer
from server.serverconfig import ServerConfig

logger = structlog.get_logger("TcpServer")

def main():
    port = int(os.getenv("QSERVER_PORT", 9999))
    config = ServerConfig()
    server = TcpServer("0.0.0.0", port, config)
    logger.info("starting server", host=server.host, port=server.port)
    server.start()

if __name__ == '__main__':
    main()
