from conditionedtransactionhandler import ConditionedTransactionHandler
from password_transaction.passwordtransactionrequesthandler import PasswordTransactionRequestHandler
from password_transaction.guesspasswordhandler import GuessPasswordHandler

handlers = {
    'conditioned_transaction': ConditionedTransactionHandler,
    'password_transaction': PasswordTransactionRequestHandler,
    'guess_password': GuessPasswordHandler,
}
