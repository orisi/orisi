class BaseHandler:
  def __init__(self, oracle):
    self.oracle = oracle

  def handle_request(self, task):
    raise NotImplementedError()

  def handle_task(self, task):
    raise NotImplementedError()

  def filter_tasks(self, task):
    raise NotImplementedError()
