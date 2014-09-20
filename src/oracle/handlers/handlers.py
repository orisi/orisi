from timelock_contract.timelock_create_handler import TimelockCreateHandler
from transactionsigner import TransactionSigner
from safe_timelock_contract.timelock_mark_release_handler import TimelockMarkReleaseHandler
from safe_timelock_contract.safe_timelock_create_handler import SafeTimelockCreateHandler


op_handlers = {
	'sign': TransactionSigner,
    'timelock_create': TimelockCreateHandler,
    'safe_timelock_create': SafeTimelockCreateHandler,
    'timelock_mark_release': TimelockMarkReleaseHandler,
}

OPERATION_REQUIRED_FIELDS = {
    'timelock_create': ['message_id', 'sum_satoshi', 'prevtxs', 'outputs', 'miners_fee_satoshi', 'return_address', 'locktime', 'pubkey_list', 'req_sigs'],
    'timelock_mark_release': [],
    'safe_timelock_create': ['message_id', 'oracle_fees', 'miners_fee_satoshi','return_address', 'locktime', 'pubkey_list', 'req_sigs'],
}

PROTOCOL_VERSION = '0.12'

