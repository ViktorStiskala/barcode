import configparser
import os
import sqlite3
from datetime import datetime, timedelta

from barcode.reader import CodeSender

config_file = os.path.join(os.path.dirname(__file__), 'reader.conf')
config = configparser.ConfigParser()
config.read(config_file)
conf = config['DEFAULT']

con = sqlite3.connect(conf['sqlite_path'])
c = con.cursor()
resend_from_date = datetime.now() - timedelta(hours=int(conf['resend_interval']))
c.execute('SELECT * FROM request_log WHERE date_created > ?', (resend_from_date,))

for uid, modifier, code, date_created in c:
    CodeSender(args=(modifier, code, uid), kwargs={'api_url': conf['api_url']}).run()
