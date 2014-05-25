from evdev import ecodes
from evdev.device import InputDevice
import barcode

dev = InputDevice('/dev/input/by-id/usb-Microchip_Technology_Inc._Keyboard_Emulate_RS232-event-kbd')
print(dev)

barcode_reader = barcode.Reader()

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        barcode_reader.keypress(event)
