from threading import Thread
import datetime
import logging
import time

import pytest
from freezegun import freeze_time

from logrotor.runner import Runner


UDP_PORT = 1024


@pytest.fixture
def runner(tmpdir):
    config = {
        'rotate_seconds': 3600,
        'storage': {
            'path': str(tmpdir),
            'size': 5,
        },
        'endpoints': [{
            'type': 'UdpEndpoint',
            'port': UDP_PORT,
        }],
    }

    return Runner(config)


@pytest.fixture
def runner_thread(runner):
    return Thread(target=runner.run)


def test_runner(send_udp, tmpdir, runner, runner_thread):
    logging.basicConfig(level=logging.DEBUG)

    runner_thread.start()
    time.sleep(1)
    send_udp('Message'.encode())
    time.sleep(1)
    runner.stop()
    runner_thread.join(timeout=1)

    assert tmpdir.join('data', '0').read() == '127.0.0.1 Message\n'


def test_runner_rotates_at_given_interval(send_udp, tmpdir, runner, runner_thread):
    with freeze_time('2017-07-28') as frozen_time:
        runner_thread.start()
        time.sleep(1)
        send_udp('Alice'.encode())
        time.sleep(1)
        frozen_time.tick(delta=datetime.timedelta(seconds=3600))
        time.sleep(1)
        send_udp('Bob'.encode())
        time.sleep(1)
        runner.stop()
        runner_thread.join(timeout=1)

    assert tmpdir.join('data', '0').read() == '127.0.0.1 Alice\n'
    assert tmpdir.join('data', '1').read() == '127.0.0.1 Bob\n'


def test_runner_does_not_schedule_rotation_in_0_seconds(tmpdir, runner, runner_thread):
    with freeze_time('2017-07-28 01:59:59,999') as frozen_time:
        runner_thread.start()
        time.sleep(1)
        runner.stop()
        runner_thread.join(timeout=1)

    assert tmpdir.join('current').readlink() == 'data/0'
