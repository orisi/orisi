

class BaseHandler:

  def handle_task(self, task):
    raise NotImplementedError()

  def handle_request(self, task):
    raise NotImplementedError()

  def filter_tasks(self, task):
    raise NotImplementedError()
