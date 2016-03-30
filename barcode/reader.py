import logging
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from evdev.events import KeyEvent

from .codes import mapping, shift_mapping


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
        modifier, code, transaction_uid = self._args
        data = {
            'code': code,
            'modifier': modifier if modifier is not None else b'',
            'uid': transaction_uid,
        }

        r = Request(self._kwargs['api_url'], urlencode(data).encode('utf-8'))
        try:
            urlopen(r)
        except HTTPError as e:
            print(e)


class WebReader(Reader):
    re_modifier = re.compile(r'USER\d{6}|INVENTORY')

    def __init__(self, api_url, sqlite_path):
        super().__init__()
        self._modifier = None
        self._last_activity = None
        self.api_url = api_url
        self.con = sqlite3.connect(sqlite_path)
        with self.con:
            self.con.execute(
                'CREATE TABLE IF NOT EXISTS request_log'
                '(uid VARCHAR PRIMARY KEY, modifier VARCHAR, code VARCHAR, date_created timestamp)')

    def _set_modifier(self, modifier):
        self._modifier = modifier

    def get_modifier(self):
        if self._last_activity is not None and (datetime.now() - self._last_activity) < timedelta(minutes=3):
            return self._modifier
        return None

    def send_code(self, code):
        modifier = self.get_modifier()
        transaction_uid = uuid.uuid4()
        self.write_log(modifier, code, transaction_uid)
        CodeSender(args=(modifier, code, transaction_uid), kwargs={'api_url': self.api_url}).start()

    def write_log(self, modifier, code, transaction_uid):
        with self.con:
            now = datetime.now()
            self.con.execute(
                "INSERT INTO request_log (uid, modifier, code, date_created) VALUES (?, ?, ?, ?)",
                (str(transaction_uid), modifier, code, now)
            )

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
