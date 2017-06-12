from logrotor.endpoint.udp import UdpEndpoint
from logrotor.endpoint.syslog import SyslogUdpEndpoint


def create_endpoint(out, config):
    class_name = config.pop('type')
    endpoint_class = globals()[class_name]
    return endpoint_class(out, **config)


def class_for_name(module_name, class_name):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)
