import json
import requests
import base64
FASTCAST_API_URL = 'http://54.77.58.8?format=json'

headers = {'content-type': 'application/json'}


def constructMessage(**kwargs):
    """
    Constructing a message, with base64 encoding of body, and signing
    """
    request = kwargs
    # request  = {"source": "1", "channel": "1", "body": "1"}

    request['body'] = base64.encodestring(request['body'])

    # signature should be body confirmed
    # "signature":
    # request['signature'] = sign(request['body'])
    request['signature'] = "temporary_string"
    payload = json.dumps(request)
    return payload

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
    print data['results']
    return data

#getMessages()
#sendMessage(constructMessage())


def decode_data(data):
        return base64.decodestring(data)

def code_data(data):
        base64.encodestring(data)

