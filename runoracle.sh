#!/bin/bash

PYTHON_EXEC=python2
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

BITMESSAGE_HOME=$DIR/PyBitmessage/
export BITMESSAGE_HOME

$PYTHON_EXEC $DIR/PyBitmessage/src/bitmessagemain.py > /dev/null &
$DIR/bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -datadir=$DIR/.bitcoin/ -port=2520 -rpcport=2521 &
sleep 5
$PYTHON_EXEC $DIR/src/run_oracle.py
