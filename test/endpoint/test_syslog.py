from datetime import datetime

from freezegun import freeze_time
import pytest

from logrotor.endpoint.syslog import SyslogUdpEndpoint
from logrotor.util.syslog import message_to_bytes, Level, Facility, Message


pytestmark = pytest.mark.asyncio


@pytest.fixture
def send_syslog(send_udp):

    def sender(message, level=Level.INFO, facility=Facility.LOCAL7, hostname='localhost'):
        message = Message(level, facility, datetime.now(), hostname, message)
        send_udp(message_to_bytes(message))

    return sender


async def test_default_settings(event_loop, send_syslog, udp_port, queue):
    with freeze_time('2018-01-01 02:03:04'):
        endpoint = SyslogUdpEndpoint(queue, bind='127.0.0.1', port=udp_port)
        await endpoint.start(event_loop)

        send_syslog('Test message')

        result = await queue.get()
        assert result == 'Jan  1 02:03:04 localhost Test message'


async def test_all_format_variables(event_loop, send_syslog, udp_port, queue):
    with freeze_time('2018-01-01 02:03:04'):
        full_format = '{src_host} {timestamp} {level} {facility} {hostname} {message}'
        endpoint = SyslogUdpEndpoint(queue, bind='127.0.0.1', port=udp_port, format=full_format)
        await endpoint.start(event_loop)

        send_syslog('Test message')

        result = await queue.get()
        assert result == '127.0.0.1 2018-01-01 02:03:04 INFO LOCAL7 localhost Test message'
