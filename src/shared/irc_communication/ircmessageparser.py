import base64
import uuid

MAXIMUM_IRC_MESSAGE_LENGTH = 400

class IrcMessageParser:

  @staticmethod
  def prepare_message(message):
    """
    Takes message and prepares it to send via IRC.
    Arguments: string with message
    Return value: List of strings with given format:
    <msg_id>,<part_number>,<base64_encoded_message_part>
    """

    message_id = str(uuid.uuid4())
    enc_message = base64.encodestring(message)
    msg_length = len(enc_message)
    available_length_per_message = MAXIMUM_IRC_MESSAGE_LENGTH - len(message_id)

    factor = 1
    # Loop is responsible for determining how many digits we need for 'part_number' field
    while 1:
      available_length_per_message -= 1
      factor *= 10

      if msg_length / available_length_per_message <= factor:
        break

    chunk_size = available_length_per_message
    message_chunks = [enc_message[i:i+chunk_size] for i in range(0, msg_length, chunk_size)]

    result = []
    for idx, chunk in enumerate(message_chunks):
      result.append("{}#{}#{}".format(message_id, idx, chunk))

    return result
