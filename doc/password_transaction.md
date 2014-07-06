# Password Transaction

Password transaction is kind of smart contract you can use, where you create a request (called **password_transaction**) and pass it to Oracles. From now Oracles will monitor the network for every request that tries to guess the password (the requests called **bounty_redeem**). If someone will guess password, Oracle will give him bounty, otherwise, after given time period, the cash will return to bounty creator.
___

### Password Transaction Request

To create password transaction you'll need to send JSON to Bitmessage network on Oracles channel, that will look like this:


```json
{
    "pubkey_json": [
        "0281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c15163",
        "02e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f0",
        "039558d46a42499ae695b70f99d43d0dd960698448d5dd9ddac1585fcc66e1bdd8",
        "03a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb30608618"
    ],
    "miners_fee": 0.0001,
    "prevtx": [
        {
            "redeemScript": "5221039558d46a42499ae695b70f99d43d0dd960698448d5dd9ddac1585fcc66e1bdd82103a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb306086182102e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f0210281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c1516354ae",
            "scriptPubKey": "a914b267985c9263503323f2dc64ae48e2fa3f52d67e87",
            "vout": 0,
            "txid": "e1a09c8d35d768943cc09b2dfdc2ef6660f94426228f6a3adf499ed91185eb46"
        }
    ],
    "password_hash": "b38e8cda33d5145f750c059b9d69a3d3e32b7057c04826ab9697ad89e1ef56ac",
    "req_sigs": 2,
    "operation": "password_transaction",
    "sum_amount": 0.003,
    "locktime": 1403834057,
    "return_address": "1PZcftn7U92T4hEHAs74qnrooxgUudYX4t",
    "oracle_fees": {
        "1x1gjLNEqP9uYTWoEf9jLefZevM2s1YVs": "0.0003",
        "1BpLELGTdXy3c7vMyVy8UzcHoyZS2WD7t3": "0.00003",
        "1CkWe8mUTLicJSyhn8vNi6RmKPuvqX2Rtw": "0.00003"
    }
}
```

The json above is absolutely valid JSON with request transaction that actually took place.

```pubkey_json``` is a list of public keys of all oracles that take part in this transaction. It also contains one additional public key generated for client (orisi client takes care of that). These public keys will be used to generate multisignature address for that transaction.

```req_sigs``` tells oracles how many signatures it is needed for transaction to be valid

```prevtx``` is a list of previous transactions that will supply funds for bounty. Every input in that list should point to funds moved to multisignature address (otherwise the final transaction will be invalid, this should be checked). It also contains redeemScript and scriptPubKey for previous transaction, since oracles run offline. (This is exactly the same prevtx as in bitcoind signrawtrasaction API)

```sum_amount``` is an amount of money you've included in your previous transactions. Oracles run offline and should not be forced to check it by themselves. You can lie, but the final transaction will not be valid then.

```miners_fee``` is just a fee you want to give miners that will mine your transaction. If you have many inputs or outputs the transaction fee should be higher (if the transaction is too big, only eligius will mine it for now).

```operation``` determines operation you're trying to perform. In this case - it's **password_transaction**

```locktime``` epoch time after which you want oracles to give your cash back to you

```return_address``` is a bitcoin address you want us to return you money after unsuccesful lottery

```password_hash``` is an SHA256 hash in hexes of your password.

```oracle_fees``` is a json object with oracles' bitcoin addresses as keys and their fees as values. Every oracle will check if it exists in that object and will accept or reject transaction accordingly


Every Oracle interested in request (being part of the request) will answer with JSON that looks exactly like JSON above, but it will add some data.

```json
{
    "rsa_pubkey": {"n":1098235043983085403850938, "e":1352940},
    "pwtxid": "882a1d913b4b5c60d5521bec869b4ce0649add0486ae5c209553ae5bc7cef1a8",
    "operation": "new_bounty"
    ...
}
```

```rsa_pubkey``` is RSA public key pair of responding Oracle. It should be used to prepare encrypted message with answer for anyone who wants to take part in password guessing.

```pwtxid``` is unique id for password transaction.

```operation``` is the only changed element in dictionary. Now it should be **new_bounty** and will be recognized by clients.

___

### Claiming bounty by sending password

Everybody who wants to guess password needs to get RSA public key pairs from all Oracles taking part in bounty. If you are using Orisi client you can just type ```./client.sh listbounties```. It will parse all **new_bounty** messages and store them grouping them by ```pwtxid```. If you want to check if your password is correct, just call ```./client.sh checkpass pwtxid password```. You'll get your answer instantly. With correct password all you need to do is to call ```./client.sh sendbountysolution pwtxid password your_bitcoin_address```, and wait for *coins*. Of course if you were first.

The protocol for guessing transactions states that the answers should be sent as JSON that looks for example like this:

```json
{
    "pwtxid": "882a1d913b4b5c60d5521bec869b4ce0649add0486ae5c209553ae5bc7cef1a8",
    "operation": "bounty_redeem",
    "passwords": {
        "rsa_hash": "answer"
    }
}
```

Ok, let's clear things out a bit.

```pwtxid``` as usual - is password transaction id

```operation``` this time should be **bounty_redeem**

```passwords``` is a dictionary. It's keys are SHA256 hashes of public key pair JSON client have received in **new_bounty**. So for example it's hashlib.sha256('{"n":1243567, "e":4093256476}').hexdigest(). Answer is message encrypted with this RSA public key and encoded with base64. Message should have following format:

```json
{
    "password": "plain_password",
    "address": "where_oracles_should_pay"
}
```

Oracles after receiving your answer will wait one hour before finalizing it. Then they will take all right guesses and choose the earliest to sign as winner. That way they avoid Bitmessage race condition (or rather - are minimalizing the risk of that race to occur).

After that - oracles will just create plain transaction using ```prevtx``` from request and address of the winner. If nobody will guess the right password - Oracles will return money to ```return_address``` from request.
