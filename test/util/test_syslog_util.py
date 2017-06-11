from datetime import datetime

from freezegun import freeze_time
import pytest

from logrotor.util.syslog import message_to_bytes, bytes_to_message, Message, Facility, Level


@pytest.mark.parametrize('message,data', [
    (Message(Level.CRIT, Facility.KERN, datetime(2018, 7, 28, 1, 2, 3), 'localhost', 'Test message'),
        b'<2>Jul 28 01:02:03 localhost Test message'),
    (Message(Level.ERR, Facility.CRON, datetime(2018, 1, 1, 15, 55, 55), 'localhost', 'Test message'),
        b'<75>Jan  1 15:55:55 localhost Test message'),
])
@freeze_time('2018-01-01')
def test_message_conversion(message, data):
    assert message_to_bytes(message) == data

    converted_message = bytes_to_message(data)
    assert converted_message.level == message.level
    assert converted_message.facility == message.facility
    assert converted_message.timestamp == message.timestamp
    assert converted_message.hostname == message.hostname
    assert converted_message.message == message.message


def test_syslog_bytes_to_message(benchmark):
    data = b'<75>Jan  1 15:55:55 localhost Test message'
    benchmark(bytes_to_message, data)
