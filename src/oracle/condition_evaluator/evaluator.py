

class Evaluator:

  def evaluate(self, condition):
    # TODO: CONDITION EVALUATION
    return True

  def valid(self, condition):
    # TODO: VALID CONDITION
    return True

  def permissions_to_sign(self, condition, transactions):
    # TODO: WHICH TRANSACTIONS SHOULD BE SIGNED
    permissions = [True] * len(transactions)
    return permissions
