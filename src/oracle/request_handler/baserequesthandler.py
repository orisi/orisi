

class BaseRequestHandler:

  def __init__(self, oracle):
    self.oracle = oracle

  def handle_request(self, task):
    raise NotImplementedError()
