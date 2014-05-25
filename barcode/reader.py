from .codes import mapping, shift_mapping
from evdev.events import KeyEvent


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
        print(self._code)

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
                print(key.keycode)