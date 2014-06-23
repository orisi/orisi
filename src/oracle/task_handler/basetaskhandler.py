

class BaseTaskHandler:

  def handle_task(self, task):
    raise NotImplementedError()

  def filter_tasks(self, task):
    raise NotImplementedError()
