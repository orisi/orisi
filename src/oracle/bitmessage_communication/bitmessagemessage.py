import base64
import datetime

class BitmessageMessage:

  def __init__(self, message_dict, direct=True):
    self.encoding_type = message_dict['encodingType']

    self.from_address = message_dict['fromAddress']
    self.to_address = message_dict['toAddress']

    self.received_time_epoch = int(message_dict['receivedTime'])
    self.received_time = datetime.datetime.fromtimestamp(self.received_time_epoch)

    self.read = message_dict['read'] == True
    self.msgid = message_dict['msgid']

    self.subject_encoded = message_dict['subject']
    self.subject = base64.decodestring(self.subject_encoded)

    self.message_encoded = message_dict['message']
    self.message = base64.decodestring(self.message_encoded)
    self.direct = direct

  def __repr__(self):
    return "BitmessageMessage(id:{0})".format(self.msgid)

  def __str__(self):
    return \
    "BitmessageMessage\nFrom: {0}\nTo: {1}\nDate: {2}\nSubject: {3}\nMessage: {4}".format(
        self.from_address,
        self.to_address,
        self.received_time.strftime("%Y-%m-%d %H:%M:%S"),
        self.subject,
        self.message)
