from shared.db_classes import GeneralDb, TableDb

CLIENT_DB_FILE = 'client.db'

class ClientDb(GeneralDb):
  def __init__(self):
    self._filename = CLIENT_DB_FILE