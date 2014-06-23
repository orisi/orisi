#!/bin/bash

python27 PyBitmessage/src/bitmessagemain.py > /dev/null &
bitcoin/bin/32/bitcoind -connect=127.0.0.1 &
sleep 5
python27 src/run_oracle.py
