import json

class OPERATION:
  TRANSACTION = 'TransactionRequest'

class RESPONSE:
  CONFIRMED = 'transaction accepted and added to queue'
  INVALID_CONDITION = 'invalid condition'
  INVALID_TRANSACTION = 'invalid transaction'
  TRANSACTION_SIGNED = 'transaction signed'
  DIRECT = 'direct message unsupported'
  SIGNED = 'transaction signed by {0}'

class SUBJECT:
  CONFIRMED = 'TransactionResponse'
  INVALID_CONDITION = 'ConditionInvalid'
  INVALID_TRANSACTION = 'TransactionInvalid'
  TRANSACTION_SIGNED = 'TransactionSigned'
  DIRECT = 'DirectMessage'
  SIGNED = 'SignedTransaction'

VALID_OPERATIONS = {
    'transaction': OPERATION.TRANSACTION
}

OPERATION_REQUIRED_FIELDS = {
    OPERATION.TRANSACTION: ['raw_transaction', 'check_time', 'condition', 'origin_address'],
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