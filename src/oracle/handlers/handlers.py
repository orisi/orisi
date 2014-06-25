from conditionedtransactionhandler import ConditionedTransactionHandler
from password_transaction.passwordtransactionrequesthandler import PasswordTransactionRequestHandler

handlers = {
    'conditioned_transaction': ConditionedTransactionHandler,
    'password_transaction': PasswordTransactionRequestHandler
}
