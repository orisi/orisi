protocol_version = '0.1'
protocol_footer = \
"""
--
Distributed Oracle
Version {0}
""".format(protocol_version)

PING_SUBJECT = 'PingResponse'
PING_MESSAGE = \
"""
Hello, I'm active!
""" + protocol_footer