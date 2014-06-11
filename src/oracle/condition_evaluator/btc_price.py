from shared.liburl_wrapper import safe_read

import json

def get_last_price_usd():
  ticker = json.loads(safe_read('https://www.bitstamp.net/api/ticker/', 10))
  return float(ticker['last'])
