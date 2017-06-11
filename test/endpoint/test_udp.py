import asyncio
from logrotor.endpoint.udp import UdpEndpoint
import pytest
import socket


pytestmark = pytest.mark.asyncio


async def test_default_settings(event_loop, send_udp, udp_port, queue):
    endpoint = UdpEndpoint(queue, bind='127.0.0.1', port=udp_port)
    await endpoint.start(event_loop)

    send_udp('Test message'.encode())

    result = await queue.get()
    assert result == '127.0.0.1 Test message\n'


async def test_format(event_loop, send_udp, udp_port, queue):
    endpoint = UdpEndpoint(queue, bind='127.0.0.1', port=udp_port, format='Foo {message}')
    await endpoint.start(event_loop)

    send_udp('Test message'.encode())

    result = await queue.get()
    assert result == 'Foo Test message'


async def test_splitlines(event_loop, send_udp, udp_port, queue):
    endpoint = UdpEndpoint(queue, bind='127.0.0.1', port=udp_port, splitlines=True)
    await endpoint.start(event_loop)

    send_udp('A\nB'.encode())

    results = [await queue.get() for _ in range(2)]
    assert results == ['127.0.0.1 A\n', '127.0.0.1 B\n']
