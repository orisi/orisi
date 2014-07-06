from timelock_contract.timelock_create_handler import ConditionedTransactionHandler
from bounty_contract.bounty_create_handler import PasswordTransactionRequestHandler
from bounty_contract.bounty_redeem_handler import GuessPasswordHandler
from transactionsigner import TransactionSigner


op_handlers = {
	'sign': TransactionSigner,
    'timelock_create': ConditionedTransactionHandler,
    'bounty_create': PasswordTransactionRequestHandler,
    'bounty_redeem': PasswordTransactionRequestHandler,
    'guess_password': GuessPasswordHandler,
}

OPERATION_REQUIRED_FIELDS = {
    'conditioned_transaction': ['transaction', 'locktime', 'pubkey_json', 'req_sigs'],
    'bounty_create': ['prevtx', 'locktime', 'message_id', 'sum_amount', 'miners_fee', 'oracle_fees', 'pubkey_json', 'req_sigs', 'password_hash', 'return_address'],
    'guess_password': ['pwtxid', 'passwords']
}

PROTOCOL_VERSION = '0.12'

