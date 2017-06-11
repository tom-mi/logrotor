import pytest
import asyncio
import time

from logrotor.storage import FileRing, StorageError


ROTATE_DELAY_SECONDS = 2


@pytest.fixture
def file_ring(tmpdir):
    return FileRing(str(tmpdir), 5)


@pytest.fixture
def file_ring_with_rotate_delay(tmpdir):
    return FileRing(str(tmpdir), 5, rotate_delay_seconds=ROTATE_DELAY_SECONDS)


@pytest.fixture
def file_ring_with_existing_index(tmpdir):
    tmpdir.join('data').mkdir()
    for i in range(5):
        tmpdir.join('data', str(i)).write_text('log-' + str(i), 'utf8')
    tmpdir.join('current').mksymlinkto(tmpdir.join('data', '3'), absolute=False)

    return FileRing(str(tmpdir), 5)


def test_initialize_empty_store(tmpdir, file_ring):
    files = sorted(f.basename for f in tmpdir.join('data').listdir())

    assert files == ['0', '1', '2', '3', '4']
    assert tmpdir.join('current').readlink() == 'data/0'
    assert file_ring.index == 0


def test_open_existing_index(tmpdir, file_ring_with_existing_index):
    files = sorted(f.basename for f in tmpdir.join('data').listdir())

    assert files == ['0', '1', '2', '3', '4']
    assert tmpdir.join('current').readlink() == 'data/3'
    for f in files:
        assert tmpdir.join('data', f).read() == 'log-' + f
    assert file_ring_with_existing_index.index == 3


@pytest.mark.parametrize('link', [
    '5',
    '-1',
    'abc',
])
def test_open_with_invalid_current_path(tmpdir, link):
    tmpdir.join('current').mksymlinkto(tmpdir.join('data', link), absolute=False)

    with pytest.raises(StorageError):
        FileRing(str(tmpdir), 5)


@pytest.mark.asyncio
async def test_write(tmpdir, file_ring):
    msg = 'Test message\n'
    await file_ring.start()
    await file_ring.write(msg)
    await file_ring.stop()

    assert tmpdir.join('data', '0').read() == msg


@pytest.mark.asyncio
async def test_write_appends_to_existing_index(tmpdir, file_ring_with_existing_index):
    await file_ring_with_existing_index.start()
    msg = 'Test message\n'
    await file_ring_with_existing_index.write(msg)
    await file_ring_with_existing_index.flush()

    assert tmpdir.join('data', '3').read() == 'log-3' + msg


@pytest.mark.asyncio
async def test_rotate(tmpdir, file_ring):
    await file_ring.start()
    await file_ring.write('Alice')
    await file_ring.rotate()
    await file_ring.write('Bob')
    await file_ring.flush()

    assert file_ring.index == 1
    assert tmpdir.join('data', '0').read() == 'Alice'
    assert tmpdir.join('data', '1').read() == 'Bob'


@pytest.mark.asyncio
async def test_rotating_clears_file_rotated_to(tmpdir, event_loop, file_ring_with_existing_index):
    await file_ring_with_existing_index.start()
    await file_ring_with_existing_index.write('Alice')
    await file_ring_with_existing_index.rotate()
    await file_ring_with_existing_index.write('Bob')
    await file_ring_with_existing_index.flush()

    assert file_ring_with_existing_index.index == 4
    assert tmpdir.join('data', '3').read() == 'log-3Alice'
    assert tmpdir.join('data', '4').read() == 'Bob'


async def measure_file_absence(path):
    while path.exists():
        await asyncio.sleep(0.01)
    start = time.time()
    while not path.exists():
        await asyncio.sleep(0.01)
    return time.time() - start


@pytest.mark.asyncio
async def test_rotate_delays_creation_of_new_file(tmpdir, event_loop, file_ring_with_rotate_delay):
    await file_ring_with_rotate_delay.start()

    measurement = event_loop.create_task(measure_file_absence(tmpdir.join('data', '1')))
    await file_ring_with_rotate_delay.rotate()
    delay = await asyncio.wait_for(measurement, timeout=5)

    assert delay == pytest.approx(ROTATE_DELAY_SECONDS, 0.1)


@pytest.mark.asyncio
async def test_parallel_execution(tmpdir, event_loop, file_ring):
    await file_ring.start()
    tasks = [
        event_loop.create_task(file_ring.write('A\n')),
        event_loop.create_task(file_ring.write('B\n')),
        event_loop.create_task(file_ring.rotate()),
        event_loop.create_task(file_ring.write('C\n')),
        event_loop.create_task(file_ring.write('D\n')),
    ]
    await asyncio.gather(*tasks)
    await file_ring.stop()

    assert tmpdir.join('data', '0').readlines() == ['A\n', 'B\n']
    assert tmpdir.join('data', '1').readlines() == ['C\n', 'D\n']
