from evdev import ecodes
from evdev.device import InputDevice
import barcode
import os
import time
import logging
import configparser
import sys

config_file = os.path.join(os.path.dirname(__file__), 'reader.conf')
config = configparser.ConfigParser()
config.read(config_file)

try:
    conf = config['DEFAULT']

    logging.basicConfig(filename=conf['logfile'], level=logging.DEBUG,format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    barcode_reader = barcode.WebReader(conf['api_url'])

    while True:
        try:
            dev = InputDevice(conf['input_device'])
        except OSError:
            logging.info("Waiting for device to become ready")
            time.sleep(conf['sleep_time'])
            continue

        dev.grab()

        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    barcode_reader.keypress(event)
        except KeyboardInterrupt:
            pass
        except IOError:
            pass

except KeyError:
    sys.stderr.write('Invalid config file\n')
    sys.exit(1)

