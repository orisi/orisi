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
  NO_FEE = 'transaction doesn\'t have oracle fee'

class SUBJECT:
  CONFIRMED = 'TransactionResponse'
  INVALID_CONDITION = 'ConditionInvalid'
  INVALID_TRANSACTION = 'TransactionInvalid'
  TRANSACTION_SIGNED = 'TransactionSigned'
  DIRECT = 'DirectMessage'
  SIGNED = 'SignedTransaction'
  NO_FEE = 'MissingOracleFee'

VALID_OPERATIONS = {
    'transaction': OPERATION.TRANSACTION
}

OPERATION_REQUIRED_FIELDS = {
    OPERATION.TRANSACTION: ['raw_transaction', 'locktime', 'condition', 'prevtx', 'pubkey_json', 'req_sigs'],
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