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
    <msg_id>#<part_number>#<number_of_last_part>#<base64_encoded_message_part>
    """

    message_id = str(uuid.uuid4())
    enc_message = base64.encodestring(message)
    msg_length = len(enc_message)
    available_length_per_message = MAXIMUM_IRC_MESSAGE_LENGTH - len(message_id)

    factor = 1
    # Loop is responsible for determining how many digits we need for 'part_number' field
    while 1:
      available_length_per_message -= 2
      factor *= 10

      if msg_length / available_length_per_message <= factor:
        break

    chunk_size = available_length_per_message
    message_chunks = [enc_message[i:i+chunk_size] for i in range(0, msg_length, chunk_size)]

    result = []
    for idx, chunk in enumerate(message_chunks):
      result.append("{}#{}#{}#{}".format(message_id, idx, len(message_chunks) - 1, chunk))

    return result

  @staticmethod
  def extract_message(message_chunks):
    """
    Takes list of messages chunks corresponding to protocol from above function:
    <msg_id>#<part_number>#<number_of_last_part>#<base64_encoded_message_part>
    Returns string with message hidden in that list

    If list of messages has some errors (invalid base64 message, not all the same msg_id, or other error)
    function will return None. The order of parts doesn't matter
    """

    chunks = [{"id":ch[0], "part":int(ch[1]), "last_part":int(ch[2]), "msg":ch[3]} for ch in [ch.split('#') for ch in message_chunks]]

    if len(chunks) == 0:
      return None

    ids = set()
    for c in chunks:
      ids.add(c['id'])

    if len(list(ids)) != 1:
      return None

    if len(chunks) - 1 != chunks[0]['last_part']:
      print "guwno 2"
      print chunks
      return None

    message_parts = sorted([(ch['part'], ch['msg']) for ch in chunks])
    message_parts = [m[1] for m in message_parts]

    full_string = ''.join(message_parts)
    try:
      message = base64.decodestring(full_string)
    except:
      # Probably corrupted string
      print "guwno 3"
      print full_string
      print message_parts
      return None

    return message

