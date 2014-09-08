import signal
import socket
import urllib2
import urllib
import logging

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

def safe_pushtx(tx, timeout_time = 10):
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


