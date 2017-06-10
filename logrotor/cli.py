import argparse
import logging
import time

import yaml

from logrotor.runner import Runner


def logrotor():
    parser = argparse.ArgumentParser(description='logrotor - a lightweight log store with time-based rotation')
    parser.add_argument('-c', '--config', help='config file', required=True)
    parser.add_argument('-v', '--verbose', help='increase verbosity', action='store_true')
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)-8s %(message)s')

    with open(args.config) as f:
        config = yaml.load(f)
    runner = Runner(config)
    runner.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        runner.stop()
