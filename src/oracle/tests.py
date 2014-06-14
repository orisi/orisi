from oracle import Oracle
from oracle_db import OracleDb, TaskQueue, TransactionRequestDb

from shared.bitmessage_communication.bitmessagemessage import BitmessageMessage

import base64
import os
import unittest

from collections import defaultdict

TEMP_DB_FILE = 'temp_db_file.db'

class MockOracleDb(OracleDb):
  def __init__(self):
    self._filename = TEMP_DB_FILE
    self.connect()
    operations = {
      'TransactionRequest': TransactionRequestDb
    }
    self.operations = defaultdict(lambda: False, operations)

class OracleTests(unittest.TestCase):
  def setUp(self):
    self.oracle = Oracle()
    self.db = MockOracleDb()
    self.oracle.db = self.db
    self.oracle.task_queue = TaskQueue(self.db)

  def tearDown(self):
    os.remove(TEMP_DB_FILE)

  def test_add_transaction(self):
    msg_dict = defaultdict(lambda: 'dummy')
    msg_dict['receivedTime'] = 1000
    msg_dict['subject'] = base64.encodestring('dummy')
    msg_dict['message'] = base64.encodestring("""
    {"raw_transaction": "01000000014ff832338cba3d9cfbd05b72953c66a1cce6f120e31d4f0d86414c2bb8140533000000009200473044022015e24c28bb38f290566bf04096c5f58cb76a8f92ca77983a4d07d4bb7bc5f1ab0220049f27abca6a0aceaf6c4fafb0b8565605e574eb8a14fc90ef9cbef274e1485a010047522103e3d472b367d3cbc496baf95edafd38fb0f9093c8aefed0b4bba8c48eefff7ac12103ba6a863daed5f13a66e09dab44d96ef8b27b55f9dd969c91a281e41c5871553052aeffffffff02e87a0100000000001976a914f77ddab3ea50377e1ce8995b1eb52310e43b43e988acb80b0000000000001976a91476a4dc3e419783ec85503f12b591069c9b47639b88ac00000000", 
    "prevtx": [{"redeemScript": "522103e3d472b367d3cbc496baf95edafd38fb0f9093c8aefed0b4bba8c48eefff7ac12103ba6a863daed5f13a66e09dab44d96ef8b27b55f9dd969c91a281e41c5871553052ae", "txid": "330514b82b4c41860d4f1de320f1e6cca1663c95725bd0fb9c3dba8c3332f84f", "vout": 0, "scriptPubKey": "a914a5f2f964c9ece7644d1a2012b283a0ac0c008a7187"}], 
    "pubkey_json": ["03e3d472b367d3cbc496baf95edafd38fb0f9093c8aefed0b4bba8c48eefff7ac1", "03ba6a863daed5f13a66e09dab44d96ef8b27b55f9dd969c91a281e41c58715530"], 
    "req_sigs": 2, 
    "operation": "transaction", 
    "locktime": 1402318623, 
    "condition": "True"}
    """)
    message = BitmessageMessage(
        msg_dict,
        'dummyaddress')
    request = ('TransactionRequest', message)
    self.oracle.handle_request(request)