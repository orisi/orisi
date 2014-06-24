from conditionedtransactionhandler import ConditionedTransactionHandler
from password_transaction.passwordtransactionrequesthandler import PasswordTransactionRequestHandler

handlers = [
    ConditionedTransactionHandler,
]

handlers = {
    'conditioned_transaction': ConditionedTransactionHandler,
    'password_transaction': PasswordTransactionRequestHandler
}
