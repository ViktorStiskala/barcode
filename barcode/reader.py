from datetime import datetime, timedelta
from threading import Thread
import re
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from .codes import mapping, shift_mapping
from evdev.events import KeyEvent
import logging


class Reader:
    def __init__(self):
        super().__init__()
        self._code = ''
        self._shift = False
        self._last_event = None

    def _check_timeout(self, event):
        """Deals with input timeout"""
        actual_timestamp = event.timestamp()
        if self._last_event is not None:
            if actual_timestamp - self._last_event > 0.25:
                self._reset()
        self._last_event = actual_timestamp

    def _reset(self):
        self._code = ''
        self._shift = False
        self._last_event = None

    def code_complete(self):
        pass

    def unknown_keycode(self, keycode):
        pass

    def keypress(self, event):
        self._check_timeout(event)
        key = KeyEvent(event)

        if key.keystate != KeyEvent.key_down:
            return

        if key.keycode == 'KEY_ENTER':
            self.code_complete()
            self._reset()
        elif key.keycode in ('KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT'):
            self._shift = True
        else:
            try:
                if self._shift:
                    self._code += shift_mapping.get(key.keycode, mapping[key.keycode])
                    self._shift = False
                else:
                    self._code += mapping[key.keycode]
            except KeyError:
                self.unknown_keycode(key.keycode)


class CodeSender(Thread):
    def run(self):
        modifier, code = self._args
        data = {
            'code': code,
            'modifier': modifier if modifier is not None else b''
        }

        r = Request(self._kwargs['api_url'], urlencode(data).encode('utf-8'))
        try:
            urlopen(r)
        except HTTPError as e:
            print(e)


class WebReader(Reader):
    re_modifier = re.compile(r'USER\d{6}|INVENTORY')

    def __init__(self, api_url):
        super().__init__()
        self._modifier = None
        self._last_activity = None
        self.api_url = api_url

    def _set_modifier(self, modifier):
        self._modifier = modifier

    def get_modifier(self):
        if self._last_activity is not None and (datetime.now() - self._last_activity) < timedelta(minutes=3):
            return self._modifier
        return None

    def send_code(self, code):
        modifier = self.get_modifier()
        CodeSender(args=(modifier, code), kwargs={'api_url': self.api_url}).start()

    def code_complete(self):
        logging.debug('code_complete: %s', self._code)
        m = self.re_modifier.match(self._code)
        if m:
            logging.debug('modifier: %s', m.group(0))
            self._set_modifier(m.group(0))
        else:
            self.send_code(self._code)

        super().code_complete()
        self._last_activity = datetime.now()
