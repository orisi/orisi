from timelock_contract.timelock_create_handler import TimelockCreateHandler
from transactionsigner import TransactionSigner
from safe_timelock_contract.timelock_mark_release_handler import TimelockMarkReleaseHandler
from safe_timelock_contract.safe_timelock_create_handler import SafeTimelockCreateHandler
from bounty_contract.request_handler import BountyCreateHandler
from bounty_contract.release_handler import BountyReleaseHandler
from bounty_contract.redeem_handler import BountyRedeemHandler



op_handlers = {
	'sign': TransactionSigner,
    'timelock_create': TimelockCreateHandler,
    'safe_timelock_create': SafeTimelockCreateHandler,
    'timelock_mark_release': TimelockMarkReleaseHandler,
    'bounty_create': BountyCreateHandler,
    'bounty_mark_release': BountyReleaseHandler,
    'bounty_redeem': BountyRedeemHandler,
}

OPERATION_REQUIRED_FIELDS = {
    'timelock_create': ['message_id', 'sum_satoshi', 'prevtxs', 'outputs', 'miners_fee_satoshi', 'return_address', 'locktime', 'pubkey_list', 'req_sigs'],
    'timelock_mark_release': [],
    'bounty_mark_release': [],
    'safe_timelock_create': ['message_id', 'oracle_fees', 'miners_fee_satoshi','return_address', 'locktime', 'pubkey_list', 'req_sigs'],
    'bounty_create': ['message_id', 'password_hash', 'oracle_fees', 'miners_fee_satoshi','return_address', 'locktime', 'pubkey_list', 'req_sigs'],
    'bounty_redeem': ['message_id', 'password_hash', 'password', 'return_address'],
}

PROTOCOL_VERSION = '0.12'

