# orisi protocol for transactions

Every transaction needs to be a valid JSON. An example of valid transaction:
```json
{
    "raw_transaction": "01000000010b6a56c1c2cb...03f12b591069c9b47639b88ac00000000",
    "prevtx": [
        {
            "redeemScript": "522102096567bfcd7908d81...7d77145b5c37247eb3060861852ae",
            "scriptPubKey": "a914418cd0fce2351e8547783a93000f3849f78c9c0287",
            "vout": 0,
            "txid": "a70e7cd15eab6dca5f5839a89a74cd71991aae23ff7f957d7caccbc2c1566a0b"
        }
    ],
    "pubkey_json": [
        "02096567bfcd7908d8105c4851eef374a58a6b3d3b627d2b986080047aeaa22c20",
        "03a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb30608618"
    ],
    "req_sigs": 2,
    "operation": "transaction",
    "locktime": 1402534143,
    "condition": "True"
}
```

```raw_transaction``` is just a transaction that can be generated with bitcoind.

```prevtx``` is a list of objects describing previous transaction, it's needed since
bitcoind is offline on oracle machine and can't verify some transaction data from inputs

```pubkey_json``` is a list of public keys from multisig address

```req_sigs``` tells us how many signatures it is needed for transaction to be valid

```operation``` is just kind of operation we want to perform, with that request it's transaction

```locktime``` tells us when oracle should check the condition for signing transaction

```condition``` for now - it's not used parameter - condition can be for example btcpricecheck in the future, but it's not yet implemented.
