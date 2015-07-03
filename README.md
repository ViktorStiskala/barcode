# barcode
Simple barcode reader – script reading barcode scanner input.

Reads barcodes (EAN13, EAN8, etc.) and modifier codes (`USER\d{6}|INVENTORY`) and sends them to web API endpoint.

## Configuration
Create file `reader.conf` in the same directory as `read.py` with the following contents:
```ini
[DEFAULT]
logfile = /var/log/reader
api_url = https://example.com/webhook/market/
input_device = /dev/input/by-id/usb-Microchip_Technology_Inc._Keyboard_Emulate_RS232-event-kbd
```
