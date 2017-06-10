import logging
import time
import datetime

import pytest
from freezegun import freeze_time

from logrotor.runner import Runner


UDP_PORT = 1024


@pytest.fixture
def runner(tmpdir):
    config = {
        'storage': {
            'path': str(tmpdir),
            'size': 5,
            'rotate_seconds': 3600,
        },
        'endpoints': [{
            'type': 'UdpEndpoint',
            'port': UDP_PORT,
        }],
    }

    return Runner(config)


def est_runner(send_udp, tmpdir, runner):
    logging.basicConfig(level=logging.DEBUG)

    runner.start()
    time.sleep(1)
    send_udp('Message'.encode())
    time.sleep(1)
    runner.stop()
    runner.join(timeout=1)

    assert tmpdir.join('data', '0').read() == '127.0.0.1 Message\n'


def test_runner_rotates_at_given_interval(send_udp, tmpdir, runner):
    with freeze_time() as frozen_time:
        runner.start()
        time.sleep(1)
        send_udp('Alice'.encode())
        time.sleep(1)
        frozen_time.tick(delta=datetime.timedelta(seconds=3600))
        time.sleep(1)
        send_udp('Bob'.encode())
        time.sleep(1)
        runner.stop()
        runner.join(timeout=1)

    assert tmpdir.join('data', '0').read() == '127.0.0.1 Alice\n'
    assert tmpdir.join('data', '1').read() == '127.0.0.1 Bob\n'
