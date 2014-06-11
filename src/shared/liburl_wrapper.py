import signal
import socket
import urllib2

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
    pass
