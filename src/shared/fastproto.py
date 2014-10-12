import json
import requests
import base64
import time
import datetime

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

import re

import logging
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

FASTCAST_API_URL = 'http://54.77.58.8?format=json'

headers = {'content-type': 'application/json'}
def decode_data(data):
        return base64.decodestring(data)

def code_data(data):
        base64.encodestring(data)

def sign(message, priv_b64):
  priv = base64.decodestring(priv_b64)
  key = RSA.importKey(priv)
  signer = PKCS1_v1_5.new(key)

  digest = SHA256.new()
  digest.update(message)

  sign = signer.sign(digest)

  return base64.encodestring(sign)

def verify(message, signature_b64, pub_b64):
  pub = base64.decodestring(pub_b64)
  signature = base64.decodestring(signature_b64)
  key = RSA.importKey(pub)
  signer = PKCS1_v1_5.new(key)
  digest = SHA256.new()
  digest.update(message)
  if signer.verify(digest, signature):
    return True
  return False

def constructMessage(priv, **kwargs):
    """
    Constructing a message, with base64 encoding of body, and signing
    """
    req = kwargs

    # We do not want to sign base64 encoded string, but actual string

    req['signature'] = sign(req['body'], priv)
    req['body'] = base64.encodestring(req['body'])

    payload = json.dumps(req)
    return payload

def generateKey():
  new_key = RSA.generate(1024)
  public_key = new_key.publickey().exportKey("DER")
  private_key = new_key.exportKey("DER")

  public_key_base64 = re.sub(r'\n','',base64.encodestring(public_key))
  private_key_base64 = re.sub(r'\n','',base64.encodestring(private_key))

  return (public_key_base64, private_key_base64)

def tryForever(requestsFunction, *args, **kwargs):
  retry_time = 1

  while 1:
    try:
      r = requestsFunction(*args, **kwargs)
      return r
    except requests.ConnectionError:
      logging.warning("FastCast connection error")

    retry_time *= 2
    retry_time = min(retry_time, 60)
    time.sleep(retry_time)

def sendMessage(payload):
    """
    Sending a message via api gateway
    """
    url = 'http://54.77.58.8?format=json'
    r = tryForever(requests.post, url, data=payload, headers=headers)
    print r.text
    return r.text

def getMessages():
  url = 'http://54.77.58.8?format=json'
  r = tryForever(requests.get, url)
  data = json.loads(r.text)

  decoded_results = []
  for req in data['results']:
    try:
      decoded_body = decode_data(req['body'])
      req['body'] = decoded_body

      if not verify(req['body'], req['signature'], req['source']):
        continue

      decoded_results.append(req)
    except:
      continue

  data['results'] = decoded_results
  return data

def broadcastMessage(body, pub, priv):
  meta_request = {}
  meta_request['source'] = pub
  meta_request['channel'] = 0
  meta_request['epoch'] = time.mktime(datetime.datetime.utcnow().timetuple())
  meta_request['body'] = body

  print sendMessage(constructMessage(priv, **meta_request))
