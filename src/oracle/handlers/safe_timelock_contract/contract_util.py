
import hashlib

def get_mark_for_address(address):
  address_hash = hashlib.sha512(address).hexdigest()

  as_number = int(address_hash, 16)
  as_mark = as_number % 10000
  return as_mark
