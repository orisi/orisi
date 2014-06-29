import json

class OPERATION:
  TRANSACTION = 'conditioned_transaction'
  PASSWORD_TRANSACTION = 'password_transaction'
  GUESS_PASSWORD = 'guess_password'

class RESPONSE:
  CONFIRMED = 'transaction accepted and added to queue'
  INVALID_CONDITION = 'invalid condition'
  INVALID_TRANSACTION = 'invalid transaction'
  TRANSACTION_SIGNED = 'transaction signed'
  DIRECT = 'direct message unsupported'
  SIGNED = 'transaction signed by {0}'
  NO_FEE = 'transaction doesn\'t have oracle fee'
  ADDRESS_DUPLICATE = 'this multisig address was already used'

class SUBJECT:
  CONFIRMED = 'TransactionResponse'
  INVALID_CONDITION = 'ConditionInvalid'
  INVALID_TRANSACTION = 'TransactionInvalid'
  TRANSACTION_SIGNED = 'TransactionSigned'
  DIRECT = 'DirectMessage'
  SIGNED = 'SignedTransaction'
  NO_FEE = 'MissingOracleFee'
  ADDRESS_DUPLICATE = 'AddressDuplicate'

VALID_OPERATIONS = {
    'conditioned_transaction': OPERATION.TRANSACTION,
    'password_transaction': OPERATION.PASSWORD_TRANSACTION,
    'guess_password': OPERATION.GUESS_PASSWORD
}

OPERATION_REQUIRED_FIELDS = {
    OPERATION.TRANSACTION: ['transactions', 'locktime', 'condition', 'pubkey_json', 'req_sigs'],
    OPERATION.PASSWORD_TRANSACTION: ['prevtx', 'locktime', 'sum_amount', 'miners_fee', 'oracle_fees', 'pubkey_json', 'req_sigs', 'password_hash', 'return_address'],
    OPERATION.GUESS_PASSWORD: ['pwtxid', 'passwords']
}

PROTOCOL_VERSION = '0.11'

RAW_RESPONSE = {
  'version': PROTOCOL_VERSION
}

IDENTITY_SUBJECT = 'IdentityBroadcast'
IDENTITY_MESSAGE_RAW = {
  "response": "active",
  "version": PROTOCOL_VERSION
}
IDENTITY_MESSAGE = json.dumps(IDENTITY_MESSAGE_RAW)
