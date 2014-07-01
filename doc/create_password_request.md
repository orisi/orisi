# Create password transaction request

If you want to create your password transaction request with Orisi client - that's great, let's get started.

I assume you have your bitcoind ok? If you don't - get it please. client required both bitcoind and bitmessage. You don't have to download whole blockchain. you can run it offline by specifying ```connect=127.0.0.1:8333```  in your ```bitcoin.conf```. It will then use only your localhost as node and won't download anything.

Ok, now let's get started.

```./client.sh listoracles``` - it will download all the oracles from oracles.li. If you have your own private oracles unlisted anywhere - add them manually to your client database. Learn more with ```./client help addoracle```.

Choose the oracles you want to use. Copy their public_keys as list. (So for example ```'["03a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb30608618","02e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f0", "0281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c15163"]'```). You'll also need your own public key that sits in your bitcoind. Just call ```bitcoind getnewaddress``` and use new address as argument of ```bitcoind validateaddress NEWLYGENERATEDADDRESS```. The public key will be there.

Now - how many Oracles should be required by your transaction? My rule of thumb would be around half so for transaction with 3 oracles I'd use 2 of them necesarilly. Now call:

```./client.sh addmultisig YOURPUBKEY 2 '["03a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb30608618", "02e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f0", "0281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c15163"]'```

This method will create and add multisig address to your bitcoind and database. You'll get back the address it generated. Send funds you want to create bounty on to that address.

MORE COMING SOON
