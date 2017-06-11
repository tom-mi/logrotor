import asyncio
from logrotor.endpoint.udp import UdpEndpoint
from logrotor.util.syslog import bytes_to_message


class SyslogUdpEndpoint(UdpEndpoint):

    def __init__(self, out, bind='0.0.0.0', port=514, **kwargs):
        super().__init__(out, bind=bind, port=port, **kwargs)

    def _get_protocol(self, out, **kwargs):
        return SyslogUdpProtocol(out, **kwargs)


class SyslogUdpProtocol(asyncio.DatagramProtocol):

    def __init__(self, out, format='{timestamp:%b %e %H:%M:%S} {hostname} {message}\n'):
        super().__init__()
        self._format = format
        self._out = out

    def datagram_received(self, data, source):
        host, port = source
        message = bytes_to_message(data)
        self._out.put_nowait(self._format.format(
            src_host=host, src_port=port,
            timestamp=message.timestamp, level=message.level.name, facility=message.facility.name,
            hostname=message.hostname, message=message.message
        ))
