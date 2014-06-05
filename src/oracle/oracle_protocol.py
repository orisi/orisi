import json

class OPERATION:
  PING = 'PingRequest'
  TRANSACTION = 'TransactionRequest'

class RESPONSE:
  CONFIRMED = 'transaction accepted and added to queue'
  PING = 'active'
  INVALID_CONDITION = 'invalid condition'
  INVALID_TRANSACTION = 'invalid transaction'
  TRANSACTION_SIGNED = 'transaction signed'
  DIRECT = 'direct message unsupported'

class SUBJECT:
  CONFIRMED = 'TransactionResponse'
  PING = 'PingResponse'
  INVALID_CONDITION = 'ConditionInvalid'
  INVALID_TRANSACTION = 'TransactionInvalid'
  TRANSACTION_SIGNED = 'TransactionSigned'
  DIRECT = 'DirectMessage'

VALID_OPERATIONS = {
    'ping': OPERATION.PING,
    'transaction': OPERATION.TRANSACTION
}

OPERATION_REQUIRED_FIELDS = {
    OPERATION.PING: [],
    OPERATION.TRANSACTION: ['raw_transaction', 'check_time', 'condition', 'original_sender'],
}


PROTOCOL_VERSION = '0.1'

RAW_RESPONSE = {
  'version': PROTOCOL_VERSION
}

IDENTITY_SUBJECT = 'IdentityBroadcast'
IDENTITY_MESSAGE_RAW = {
  "response": "active",
  "version": PROTOCOL_VERSION 
}
IDENTITY_MESSAGE = json.dumps(IDENTITY_MESSAGE_RAW)