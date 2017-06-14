from datetime import datetime

from freezegun import freeze_time
import pytest

from logrotor.util.syslog import message_to_bytes, bytes_to_message, Message, Facility, Level


@pytest.mark.parametrize('message,data', [
    (Message(Level.CRIT, Facility.KERN, datetime(2018, 7, 28, 1, 2, 3), 'localhost', 'tag', None, 'Test message'),
        b'<2>Jul 28 01:02:03 localhost tag: Test message'),
    (Message(Level.ERR, Facility.CRON, datetime(2018, 1, 1, 15, 55, 55), 'localhost', 'tag', None, 'Test message'),
        b'<75>Jan  1 15:55:55 localhost tag: Test message'),
    (Message(Level.ERR, Facility.CRON, datetime(2018, 1, 1, 15, 55, 55), 'localhost', 'tag', None, 'Test message'),
        b'<75>Jan  1 15:55:55 localhost tag: Test message'),
])
@freeze_time('2018-01-01')
def test_message_conversion(message, data):
    assert message_to_bytes(message) == data

    converted_message = bytes_to_message(data)
    assert converted_message.level == message.level
    assert converted_message.facility == message.facility
    assert converted_message.timestamp == message.timestamp
    assert converted_message.hostname == message.hostname
    assert converted_message.tag == message.tag
    assert converted_message.message == message.message


@pytest.mark.parametrize('tag,pid,data,two_way', [
    ('tag', None, b'<75>Jan  1 15:55:55 localhost tag: Test',     True),
    ('tag', None, b'<75>Jan  1 15:55:55 localhost tag Test',      False),
    ('tag', 42,   b'<75>Jan  1 15:55:55 localhost tag[42]: Test', True),
    ('tag', 42,   b'<75>Jan  1 15:55:55 localhost tag[42] Test',  False),
])
@freeze_time('2018-01-01')
def test_parse_tags(tag, pid, data, two_way):

    message = Message(Level.ERR, Facility.CRON, datetime(2018, 1, 1, 15, 55, 55), 'localhost', tag, pid, 'Test')

    if two_way:
        assert message_to_bytes(message) == data

    converted_message = bytes_to_message(data)
    assert converted_message.level == message.level
    assert converted_message.facility == message.facility
    assert converted_message.timestamp == message.timestamp
    assert converted_message.hostname == message.hostname
    assert converted_message.tag == message.tag
    assert converted_message.pid == message.pid
    assert converted_message.message == message.message


def test_syslog_bytes_to_message(benchmark):
    data = b'<75>Jan  1 15:55:55 localhost tag[42]: Test message'
    benchmark(bytes_to_message, data)
