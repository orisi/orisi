import signal
import socket
import urllib2
import urllib
import logging
import json

TIMEOUT = 10

socket.setdefaulttimeout(TIMEOUT)

def timeout_catcher(signum, _):
  raise urllib2.URLError("Read timeout")

signal.signal(signal.SIGALRM, timeout_catcher)

def safe_read(url, timeout_time):
  signal.setitimer(signal.ITIMER_REAL, timeout_time)
  try:
    content = urllib2.urlopen(url, timeout=timeout_time).read()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return content
  except:
    signal.setitimer(signal.ITIMER_REAL, 0)
    return None

def safe_pushtx(tx, timeout_time = 120):
  logging.info('pushing to eligius')
  signal.setitimer(signal.ITIMER_REAL, timeout_time)
  try:
    #thanks http://www.pythonforbeginners.com/python-on-the-web/how-to-use-urllib2-in-python/
    query_args = {'send': 'Push', 'transaction': tx}
    data = urllib.urlencode(query_args)
    url = 'http://eligius.st/~wizkid057/newstats/pushtxn.php'
    content = urllib2.urlopen(url, data, timeout=timeout_time).read()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return content
  except:
    signal.setitimer(signal.ITIMER_REAL, 0)
    return None

def safe_blockchain_multiaddress(addresses, timeout_time = 120):
  signal.setitimer(signal.ITIMER_REAL, timeout_time)
  try:
    url = 'http://blockchain.info/multiaddr?active={}'.format('|'.join(addresses))
    logging.debug('url: %r' % url)
    content = urllib2.urlopen(url, timeout=timeout_time).read()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return json.loads(content)
  except:
    logging.warning('timeout on blockchain multiaddress')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return None

def safe_nonbitcoind_blockchain_getblock(block_hash, timeout_time=120):
  signal.setitimer(signal.ITIMER_REAL, timeout_time)
  try:
    url = 'http://blockchain.info/rawblock/{}'.format(block_hash)
    content = urllib2.urlopen(url, timeout=timeout_time).read()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return json.loads(content)
  except:
    logging.warning('error getting info from block')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return None

def safe_get_raw_transaction(txid, timeout_time=120):
  print "getting raw transaction"
  signal.setitimer(signal.ITIMER_REAL, timeout_time)
  try:
    url = 'http://blockchain.info/tx/{}?format=hex'.format(txid)
    content = urllib2.urlopen(url, timeout=timeout_time).read()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return content
  except:
    logging.warning('timeout on get_raw_transaction')
    signal.setitimer(signal.ITIMER_REAL, 0)
    return None

