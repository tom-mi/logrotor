from datetime import datetime
from enum import Enum
import re
import socket


class Facility(Enum):
    KERN, USER, MAIL, DAEMON, AUTH, SYSLOG, LPR, NEWS, UUCP, CRON, AUTHPRIV, FTP = range(12)
    LOCAL0, LOCAL1, LOCAL2, LOCAL3, LOCAL4, LOCAL5, LOCAL6, LOCAL7 = range(16, 24)


class Level(Enum):
    EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, DEBUG = range(8)

TAG_REGEX = re.compile(r'([a-zA-Z0-9]+)(?:\[(\d+)\]|)[:]?[\s]?')


class Message:

    def __init__(self, level, facility, timestamp, hostname, tag, pid, message):
        self.level = level
        self.facility = facility
        self.timestamp = timestamp
        self.hostname = hostname
        self.tag = tag
        self.pid = pid
        self.message = message


def message_to_bytes(message):
    pri = message.level.value + message.facility.value * 8
    tag_with_pid = message.tag
    if message.pid is not None:
        tag_with_pid += '[{}]'.format(message.pid)

    return '<{pri}>{timestamp:%b %e %H:%M:%S} {hostname} {tag_with_pid}: {message}'.format(
        pri=pri, timestamp=message.timestamp, hostname=message.hostname, tag_with_pid=tag_with_pid,
        message=message.message).encode()


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

    tag, pid = None, None
    tag_match = TAG_REGEX.match(message)
    if tag_match and tag_match.end() != len(message):
        tag = tag_match.group(1)
        pid = tag_match.group(2)
        pid = int(pid) if pid else None
        message = message[tag_match.end():]

    return Message(level, facility, timestamp, hostname, tag, pid, message)


def _parse_syslog_timestamp(timestamp):
    normalized_timestamp = str(datetime.now().year) + ' ' + timestamp
    return datetime.strptime(normalized_timestamp, '%Y %b %d %H:%M:%S')
