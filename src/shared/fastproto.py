import json
import requests
import base64
import time
import datetime

FASTCAST_API_URL = 'http://54.77.58.8?format=json'

headers = {'content-type': 'application/json'}
def decode_data(data):
        return base64.decodestring(data)

def code_data(data):
        base64.encodestring(data)

def constructMessage(**kwargs):
    """
    Constructing a message, with base64 encoding of body, and signing
    """
    #request = dict(req)
    #print req
    # request  = {"source": "1", "channel": "1", "body": "1"}
    req = kwargs

    req['body'] = base64.encodestring(req['body'])

    # signature should be body confirmed
    # "signature":
    # request['signature'] = sign(request['body'])
    req['signature'] = "temporary_string"
    payload = json.dumps(req)
    return payload

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto import Random


"""
key64 = b'MIGJAoGBAJNrHWRFgWLqgzSmLBq2G89exgi/Jk1NWhbFB9gHc9MLORmP3BOCJS9k\
onzT/+Dk1hdZf00JGgZeuJGoXK9PX3CIKQKRQRHpi5e1vmOCrmHN5VMOxGO4d+znJDEbNHOD\
ZR4HzsSdpQ9SGMSx7raJJedEIbr0IP6DgnWgiA7R1mUdAgMBAAE='

keyDER = decode_data(key64)
externKey = RSA.importKey(keyDER)


orisi_key = RSA.importKey(externKey)
key = orisi_key

def sign(text):


    hash = SHA256.new(text).digest()
    return key.sign(hash, '')

def verify(text, signature):

    hash = SHA256.new(text).digest()
    public_key = key.publickey()
    public_key.verify(hash, signature)

"""

def sendMessage(payload):
    """
    Sending a message via api gateway
    """
    url = 'http://54.77.58.8?format=json'
    r = requests.post(url, data=payload, headers=headers)
    print r.text
    return r.text

def getMessages():
    url = 'http://54.77.58.8?format=json'
    r = requests.get(url)
    data = json.loads(r.text)

    decoded_results = []
    for req in data['results']:
        try:
          decoded_body = decode_data(req['body'])
          req['body'] = decoded_body
          decoded_results.append(req)
        except:
          continue

    data['results'] = decoded_results


    return data

def broadcastMessage(body):
  meta_request = {}
  meta_request['source'] = 0
  meta_request['channel'] = 0
  meta_request['signature'] = 0
  meta_request['epoch'] = time.mktime(datetime.datetime.utcnow().timetuple())
  meta_request['body'] = body

  print sendMessage(constructMessage(**meta_request))

#getMessages()


#signature = sign("dupa")
#print verify("dupa",signature)
#sendMessage(constructMessage())




