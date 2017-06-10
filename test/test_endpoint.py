from asyncio import Queue

import pytest

from logrotor.endpoint import create_endpoint


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('minimal_config', [
    {'type': 'UdpEndpoint', 'port': 1024},

])
async def test_create_endpoint(event_loop, queue, minimal_config):
    endpoint = create_endpoint(queue, minimal_config)

    await endpoint.start(event_loop)
    await endpoint.stop()
