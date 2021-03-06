import asyncio
import logging
from threading import Thread
import time
from datetime import datetime

from logrotor.endpoint import create_endpoint
from logrotor.storage import FileRing


class Runner:

    def __init__(self, config):
        self._loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()

        self._endpoints = self._configure_endpoints(config)
        self._file_ring = self._configure_file_ring(config)

        self._consumer_task = None
        self._rotator_task = None

        self._running = False
        self._rotate_interval = config['rotate_every_seconds']
        self._flush_interval = config['flush_every_seconds']

    def _configure_file_ring(self, config):
        return FileRing(**config['storage'])

    def _configure_endpoints(self, config):
        return [create_endpoint(self._queue, e) for e in config['endpoints']]

    def run(self):
        self._running = True
        logging.info('Starting file ring')
        start_tasks = []
        start_tasks.append(self._loop.create_task(self._file_ring.start()))
        for endpoint in self._endpoints:
            logging.info('Starting {}'.format(endpoint.__class__.__name__))
            start_tasks.append(self._loop.create_task(endpoint.start(self._loop)))

        self._loop.run_until_complete(asyncio.gather(*start_tasks))
        logging.info('Startup finished')

        logging.info('Creating queue consumer')
        self._consumer_task = self._loop.create_task(self._consumer())
        logging.info('Creating rotator')
        self._rotator_task = self._loop.create_task(self._rotator())
        logging.info('Creating flusher')
        self._flusher_task = self._loop.create_task(self._flusher())

        logging.info('Running forever')
        self._loop.run_until_complete(asyncio.gather(self._consumer_task, self._rotator_task, self._flusher_task))

        stop_tasks = []
        for endpoint in self._endpoints:
            logging.info('Stopping {}'.format(endpoint.__class__.__name__))
            stop_tasks.append(self._loop.create_task(endpoint.stop()))
        logging.info('Stopping file ring')
        stop_tasks.append(self._loop.create_task(self._file_ring.stop()))
        self._loop.run_until_complete(asyncio.gather(*stop_tasks))
        logging.info('Shutdown finished')

    def stop(self):
        logging.info('Stopping runner')
        self._running = False

    @property
    def is_running(self):
        return self._running

    async def _consumer(self):
        while self._running:
            if self._queue.empty():
                await asyncio.sleep(0.1)
            else:
                msg = self._queue.get_nowait()
                await self._file_ring.write(msg + '\n')

    async def _rotator(self):
        while self._running:
            now = time.time()
            delta = self._rotate_interval - (now % self._rotate_interval)
            next_rotation = now + delta
            logging.info('Scheduling next rotation at {} (in {} seconds)'
                         .format(datetime.fromtimestamp(next_rotation).isoformat(), delta))
            while self._running:
                await asyncio.sleep(1)
                if time.time() >= next_rotation:
                    await self._file_ring.rotate()
                    break

    async def _flusher(self):
        while self._running:
            for _ in range(int(self._flush_interval)):
                if not self._running:
                    break
                await asyncio.sleep(1)
            logging.debug('Flushing')
            await self._file_ring.flush()
