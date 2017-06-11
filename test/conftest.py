import asyncio
import logging
import socket

import pytest


IP = '127.0.0.1'


@pytest.fixture
def queue(event_loop):
    return asyncio.Queue(loop=event_loop)


@pytest.fixture
def udp_port():
    return 1024


@pytest.fixture
def send_udp(udp_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sender(message):
        sock.sendto(message, (IP, udp_port))

    return sender


@pytest.fixture(autouse=True)
def enable_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)-15s %(lineno)4d %(levelname)-8s %(message)s')
