# Main Oracle file
from oracle_communication import OracleCommunication
from db_connection import OracleDb

import time

class Oracle:
  def __init__(self):
    self.communication = OracleCommunication()
    self.db = OracleDb()

    self.operations = {
      'PingRequest': self.ping,
    }

  def ping(self, message):
    self.communication.ping_response(message.from_address)

  def handle_request(self, request):
    operation, message = request
    fun = self.operations[operation]
    fun(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def run(self):
    while True:
      # Proceed all requests
      requests = self.communication.get_new_requests()
      for request in requests:
        self.handle_request(request)
        self.communication.mark_request_done(request)

      time.sleep(1)