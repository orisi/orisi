#!/bin/bash

PYTHON_EXEC=python2

BITMESSAGE_HOME=$(pwd)/PyBitmessage/
export BITMESSAGE_HOME

$PYTHON_EXEC PyBitmessage/src/bitmessagemain.py > /dev/null &
bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -datadir=$(pwd)/.bitcoin/ -port=2520 -rpcport=2521 &
sleep 5
$PYTHON_EXEC src/run_oracle.py
