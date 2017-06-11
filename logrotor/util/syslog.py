from datetime import datetime
from enum import Enum
import re
import socket


class Facility(Enum):
    KERN, USER, MAIL, DAEMON, AUTH, SYSLOG, LPR, NEWS, UUCP, CRON, AUTHPRIV, FTP = range(12)
    LOCAL0, LOCAL1, LOCAL2, LOCAL3, LOCAL4, LOCAL5, LOCAL6, LOCAL7 = range(16, 24)


class Level(Enum):
    EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, DEBUG = range(8)


class Message:

    def __init__(self, level, facility, timestamp, hostname, message):
        self.level = level
        self.facility = facility
        self.timestamp = timestamp
        self.hostname = hostname
        self.message = message


def message_to_bytes(message):
    pri = message.level.value + message.facility.value * 8
    return '<{pri}>{timestamp:%b %e %H:%M:%S} {hostname} {message}'.format(
        pri=pri, timestamp=message.timestamp, hostname=message.hostname, message=message.message).encode()


def bytes_to_message(data):
    data = data.decode()
    if not data.startswith('<'):
        raise ValueError('Invalid syslog message {}'.format(data))

    pri_end = data.index('>')
    pri = int(data[1:pri_end])

    facility = Facility(int(pri / 8))
    level = Level(int(pri % 8))

    timestamp_end = pri_end + 16
    msg_timestamp = data[pri_end+1:timestamp_end]
    timestamp = _parse_syslog_timestamp(msg_timestamp)

    hostname, message = data[timestamp_end:].split(maxsplit=1)

    return Message(level, facility, timestamp, hostname, message)


def _parse_syslog_timestamp(timestamp):
    normalized_timestamp = str(datetime.now().year) + ' ' + timestamp
    return datetime.strptime(normalized_timestamp, '%Y %b %d %H:%M:%S')
