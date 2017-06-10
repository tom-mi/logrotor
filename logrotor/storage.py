import aiofiles
import asyncio
import logging
import os


def _synchronized(func):
    async def wrapper(self, *args, **kwargs):
        await self._lock.acquire()
        result = await func(self, *args, **kwargs)
        self._lock.release()
        return result

    return wrapper


class StorageError(Exception):
    pass


class FileRing:

    def __init__(self, path, size):
        if not isinstance(size, int) and size > 0:
            raise ValueError('Invalid size {}'.format(size))
        logging.info('Initializing ring {} with size {}'.format(path, size))
        self._path = path
        self._data_path = os.path.join(path, 'data')
        self._current_path = os.path.join(path, 'current')
        self._size = size
        self._index = None
        self._f = None
        self._lock = asyncio.Lock()

        self._initialize()

    def _initialize(self):
        os.makedirs(self._path, exist_ok=True)
        self._initialize_ring()
        self._initialize_current_index()

    def _initialize_ring(self):
        os.makedirs(self._data_path, exist_ok=True)
        for i in range(self._size):
            open(os.path.join(self._data_path, str(i)), 'a')

    def _initialize_current_index(self):
        if os.path.lexists(self._current_path):
            index = self._get_index_from_link(os.readlink(self._current_path))
            self._set_index(index)
        else:
            self._set_index(0)

    def _get_index_from_link(self, link):
        datadir, current_file = os.path.split(link)
        if not datadir == 'data':
            raise StorageError('Invalid current link {}'.format(link))
        try:
            index = int(current_file)
        except ValueError:
            raise StorageError('Invalid current link {}'.format(link))

        if index not in range(self._size):
            raise StorageError('Invalid current link {} to file outside ring of size {}'.format(link, self._size))

        return index

    def _set_index(self, index):
        self._index = index
        if os.path.lexists(self._current_path):
            os.unlink(self._current_path)
        os.symlink(os.path.join('data', str(index)), self._current_path)

    @property
    def index(self):
        return self._index

    async def _open(self):
        self._f = await aiofiles.open(os.path.join(self._data_path, str(self._index)), 'a')

    @_synchronized
    async def start(self):
        await self._open()

    @_synchronized
    async def stop(self):
        await self._f.close()

    @_synchronized
    async def write(self, value):
        await self._f.write(value)

    @_synchronized
    async def flush(self):
        await self._f.flush()

    @_synchronized
    async def rotate(self):
        new_index = (self._index + 1) % self._size
        logging.info('Rotating ring: {} -> {}'.format(self._index, new_index))

        os.unlink(os.path.join(self._data_path, str(new_index)))
        await self._f.close()
        self._set_index(new_index)
        await self._open()
