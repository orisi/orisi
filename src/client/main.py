#!/usr/bin/env python2.7
from collections import defaultdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


import sys
import json
import hashlib
import time

import base64
from Crypto.PublicKey import RSA

from shared import liburl_wrapper

from math import ceil
from random import randrange

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient

START_COMMAND = "./client.sh"

def unknown(args):
  """unknown operation"""
  print "unknown operation, use {} help for possible operations".format(START_COMMAND)


CHARTER_URL = 'http://oracles.li/test-charter.json'

DIFFICULTY = 1000000000

def find_secret(hash,pwd):
  i = 0
  print "looking for a secret number..."
  step = DIFFICULTY/100
  while i < DIFFICULTY:
    i += 1

    if i % step == 0:
      percentage = ((100*i)/DIFFICULTY)

      if percentage <= 5 or percentage % 10 == 0:
        print "%d%%" % percentage
      if percentage == 5:
        print "(next display every 10%)"

    salted = "{}#{}".format(pwd, i)
    new_hash = hashlib.sha512(salted).hexdigest()
    if new_hash == hash:
      return salted
  return False

def main3(args): # guess password
  

    keys_json = '''
    {"keys":
    [ {"e": 65537, "n": 881162845733129246234729513244018117429201286880789702125578849628225048087377697942175461090157813718509643655401474916243671690413236804969130456245016485792946165001840681375014510373032653064397445528078081815263441614624868200537959946317063813932916811768776236796762912943783409925154394421798729263012565037143599207625041567601121319145124918820571027342994180845471006334421230951526341632427476152768366818083678457267709515412239369824895340487336612486877441259264277597497298037669961594955833393310291041324067053166971525483563445172833719531839800461949484215437408613603456287886940335349113666588919573824903213917675246188998310934931850987791471196338463147537321795621455849697770779503617487067049214119131865655068783952147213582047511244026726838853265666442294107729841800665672066564734416046189395789442166768190865908793255523957183949430957318161112489891023867275922142788936206273040623302350829766003142702584613659957539864305790606706794624984774125005517662751252225540631444575783893970157743022129237696522917666492979923776628890009347764808869280111407860691356567760933350985284012819422373336116144889051317531257109734465983847210520402172144119018909263812818717809507726045839322560838869},
      {"e": 65537, "n": 784796641189972947980165854621699542788985687544469461188637404016525076656415623003331056712288023464041171891265023535617807409509144472368145928268910875676246255181416181901701284378599404962104209492046843670210514200312541050459376736871046675240420277120639225419563110935318931020379198827017213365673278176716024143285568852978487343485459674213086150949461620643340682956946445771528205379390665874995565242596787453212823979661669161472627201593416844625621871171594409611985927697818624573526022899451979260143072776805942394361890088584557296886743725228674605628145766627275985632513635459244055265193801231742076374426198237400338777586506386120862395387679496054339762309094803356158746136520017023914983831243116928583226219791385843805592340379088657797867745926634214067048006190559928308731081238270967041131929954657599512618724370184815958254885463276027351191965466201693444770954021077133000806615678468310769887127447292033374087850840255739482582087557385754439154864681417291631888921215650556054779168866163021325936785674899220329152590355707740236444346544696095593848466003477548841188539015054402024250928690465834901748723851213188028094554918933537164151757005848713317135949525032892835412243294571},
      {"e": 65537, "n": 599701485774448439652540848349076958552703846750797480032689801946140230970247833453294343226318444908646063724744729220252077365544419236210716302228770090565681282954554092560197296904562106305818912666654641445779666256437646114103355578976161982520343893208660211015408482306585106766456960724616700594717781577099308340794493714640264013768101233949564994639410028713913459333917037763909028333045124578971863372625895473130134020109335805322941120167128514738757811772643731024790343571974127212043560634677182944169905718731541173734677216424609509001891264056775727371911019648147816588849196694234641858384861119327746720938582748710258733077909846765871590016657935047530322801294581525069072480726991417475978722266633919031368954274184322959705080793934720172379369441603523221703481503597060983673603556600756504050312400328948348609043570171989972080227919220712694186181324950180222261772085598469341135981517680498750941111532618976321454578833468988091965477341836773619663250969357393839338215293421864636653083728657913344534891604691230164760268136327516553693643119138859539041725007383904126001236032131181018745181747705844112871432992580258219649269247936560278602671414234665350630952454908816109370819504499}
    ]}

    '''

    keys = json.loads(keys_json)['keys']

#    passwd = 'satoshi'
#    hash_str = 'c9a52f5adc317fd07ae181bc96acf2b9d4898788a54ad09abc831ba446d3c7d84a7948b4c5bf0f098850f35d97de460e5bd11e5339d837b69ee58c6c36498a50'
#     secret = find_secret(hash_str, passwd)
    secret = "satoshi#349798192"

    pwtxid = '33QfFivxapNeJQgGhxQvh8Hhmhg8AMGN7Z'

    address = '1FhCLQK2ZXtCUQDtG98p6fVH7S6mxAsEey'


    if not secret:
      print "secret not found. bad pass? bad DIFFICULTY limit?"
      return

    print "secret found: %s" % secret

    passwords = {}

    msg = json.dumps({
      "password": secret,
      "address": address
    })

    for key in keys:
      rsa_key = RSA.construct((
        long(key['n']),
        long(key['e'])))
      base64_msg = base64.encodestring(rsa_key.encrypt(msg, 0)[0])
      rsa_hash = hashlib.sha256(json.dumps(key)).hexdigest()
      passwords[rsa_hash] = base64_msg

    request = json.dumps({
        'operation': 'bounty_redeem',
        'pwtxid': pwtxid,
        'passwords': passwords
    })

    bm = BitmessageClient()
    bm.send_message(bm.chan_address, "bounty_redeem", request)


def main(args):

  btc = BitcoinClient()
  tmp_address = btc.validate_address(btc.get_new_address())

  charter_json = liburl_wrapper.safe_read(CHARTER_URL, timeout_time=10)
  charter = json.loads(charter_json)

  print "temp pubkey: %r" % tmp_address['pubkey']
  print "charter: %r" % charter

  client_pubkey = tmp_address['pubkey']
  oracle_pubkeys = []
  for o in charter['nodes']:
    oracle_pubkeys.append(o['pubkey'])

  min_sigs = int(ceil(float(len(oracle_pubkeys))/2))

  key_list = [client_pubkey] + oracle_pubkeys

  print "min_sigs: %r" % min_sigs
  print "keys_list: %r" % key_list
  print "-------"

  response = btc.create_multisig_address(min_sigs, key_list)

  print "%r" % response

  print btc.validate_address(response['address'])


def prepare_password_hash(password):
    rn = randrange(DIFFICULTY/100, DIFFICULTY) 
    salted_password = "{}#{}".format(password, rn)
    hashed = hashlib.sha512(salted_password).hexdigest()
    return hashed

def main2(args):

  request = {}

  btc = BitcoinClient()
  charter_json = liburl_wrapper.safe_read(CHARTER_URL, timeout_time=10)
  charter = json.loads(charter_json)

  client_pubkey = '03a9f6c8107a174f451fc7101e95fd1e1003d2b435d94b80b7ff8ebfbfba1841b7'
  oracle_pubkeys = []
  oracle_fees = {}
  oracle_bms = []

  for o in charter['nodes']:
    oracle_pubkeys.append(o['pubkey'])
    oracle_fees[o['address']] = o['fee']
    oracle_bms.append(o['bm'])

  oracle_fees[charter['org_address']] = charter['org_fee']

  min_sigs = int(ceil(float(len(oracle_pubkeys))/2))

  key_list = [client_pubkey] + oracle_pubkeys

  response = btc.create_multisig_address(min_sigs, key_list)
  msig_addr = response['address'] # we're using this as an identificator

  request['message_id'] = "%s-%s" % (msig_addr, str(randrange(1000000000,9000000000)))

  ###

  request['pubkey_list'] = key_list
  request['miners_fee'] = 0.0001

  prevtxs = [ {
    'redeemScript' : '5121022cf5e247fff0c71f98c1df0e202df7eaec94ca66b5f24b66d6b2676d7f6b9b4c2102826552f97262f90397b20f6fe398012d2950591228de6553d61cae0da5a8b4c252ae',
    'scriptPubKey' : 'a914b0c7e6ba3ca46d58c9e30e39d14a178897b5583d87',
    'vout':0,
    'txid':'d0d41f7ec8435ed65ed078facbd92a9684021751f76735de2d8457dfa5a24050',
  } ]


  '''    'redeemScript' : '52210281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c151632102e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f02103a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb306086182103a9f6c8107a174f451fc7101e95fd1e1003d2b435d94b80b7ff8ebfbfba1841b754ae',
    'scriptPubKey' : 'a91412d857a1778be8ad4b2e548a2632aac14f3063a587',
    'vout':0,
    'txid':'8b5eb0ea6a9bbbf7ecec66edb5d6b9e10cdf9e6ebe6f9bee35d630817b2fbce3',
  '''

  request['prevtxs'] = prevtxs
  request['outputs'] = oracle_fees

  request['password_hash'] = prepare_password_hash('satoshi')
  request["req_sigs"] = min_sigs
#  request['operation'] = 'bounty_create'
  request['operation'] = 'timelock_create'
  request['sum_amount'] = 0.002
  request['locktime'] = time.time() + 1*60 #1405418400
  request['return_address'] = '1MGqtD59cwDGpJww2nugDKUiT2q81fxT5A'

  bm = BitmessageClient()
  print "sending: %r" % json.dumps(request)
  print bm.chan_address

  request_content = json.dumps(request)

  print bm.send_message(bm.chan_address, request['operation'], request_content)

  print ""
  print '''Gathering oracle responses. If it's your first time using this Bitmessage address, it may take even an hour to few hours before the network
  forwards your message and you get the replies. All the future communication should be faster and come within single minutes. [this message may be inaccurate, todo for: @gricha]'''
  print ""

  keys = []

  print "%r" % oracle_bms

  while oracle_bms:
    messages = bm.get_unread_messages()
    print "unread messages: %r" % len(messages)
    for msg in messages:
      print msg.from_address
      if msg.from_address in oracle_bms:
        print "msg in bms"
        try:
          content = json.loads(msg.message)
        except:
          print msg.message
          print 'failed decoding message'
          continue

        print "a"
        if 'in_reply_to' not in content:
          continue

        print "b"
        if content['in_reply_to'] == request['message_id']:
            print "[%r][%r] %r" % (msg.subject, msg.from_address, msg.message)
            print ""
            oracle_bms.remove(msg.from_address)
#            keys.append(content['rsa_pubkey'])

    if oracle_bms:
      print "waiting..."
      time.sleep(5)

    print "done"


  print "oracle keys"
  print ""
  print json.dumps(keys)


RAW_OPERATIONS = {
  'main': main,
  'main2': main2,
  'main3': main3,
}
OPERATIONS = defaultdict(lambda:unknown, RAW_OPERATIONS)

SHORT_DESCRIPTIONS = {
  'main': "prepares the first multisig",
  'main2': "broadcasts a request for create (timelock/bounty)",
  "main3": "broadcasts bounty_redeem",
}


def help():
  print "You can use one of the following functions:"
  for name, desc in SHORT_DESCRIPTIONS.iteritems():
    print "{0} - {1}".format(name, desc)
  print "Learn more by using {0} help functionname".format(START_COMMAND)

def help_fun(fun_name):
  fun = OPERATIONS[fun_name]
  print fun.__doc__

def main(args):
  if len(args) == 0:
    print "no arguments given, use {0} help for possible operations".format(START_COMMAND)
    return
  if args[0] == 'help':
    if len(args) == 1:
      help()
    else:
      help_fun(args[1])
    return
  operation = OPERATIONS[args[0]]
  #special case
  operation(args[1:])


if __name__=="__main__":
  args = sys.argv[1:]
  main(args)
