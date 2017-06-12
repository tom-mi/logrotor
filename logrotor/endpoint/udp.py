import asyncio
import logging


class UdpEndpoint:

    def __init__(self, out, bind='0.0.0.0', port=None, **kwargs):
        if port is None or not isinstance(port, int):
            raise ValueError('No valid port configured for {}'.format(self.__class__.__name__))
        self._address = (bind, port)
        self._protocol = self._get_protocol(out, **kwargs)

    def _get_protocol(self, out, **kwargs):
        return UdpProtocol(out, **kwargs)

    async def start(self, loop):
        logging.debug('Starting udp endpoint for protocol {} on {}'
                      .format(self._protocol.__class__.__name__, self._address))
        self._transport, _ = await loop.create_datagram_endpoint(lambda: self._protocol, local_addr=self._address)

    async def stop(self):
        logging.debug('Closing udp endpoint on {}'.format(self._address))
        self._transport.close()


class UdpProtocol(asyncio.DatagramProtocol):

    def __init__(self, out, format='{host} {message}', splitlines=False):
        super().__init__()
        self._format = format
        self._out = out
        if splitlines:
            self._filter = lambda data: data.splitlines()
        else:
            self._filter = lambda data: [data]

    def datagram_received(self, data, source):
        host, port = source
        for message in self._filter(data.decode()):
            self._out.put_nowait(self._format.format(host=host, port=port, message=message))
