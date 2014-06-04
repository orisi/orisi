import re

PROTOCOL_REGEX = [
    (r'^ping.*$', 'PingRequest')
]


PROTOCOL_VERSION = '0.1'
PROTOCOL_FOOTER = \
"""
--
Distributed Oracle
Version {0}
""".format(PROTOCOL_VERSION)

PING_SUBJECT = 'PingResponse'
PING_MESSAGE = \
"""
Hello, I'm active!
""" + PROTOCOL_FOOTER