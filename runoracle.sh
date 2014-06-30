#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z $(pgrep $PYTHON_EXEC) ]
then
    BITMESSAGE_HOME=$DIR/PyBitmessage/
    export BITMESSAGE_HOME
    $PYTHON_EXEC $DIR/PyBitmessage/src/bitmessagemain.py > bm_error.log &
    sleep 2
fi

if [ -z $(pgrep bitcoind) ]
then
    $DIR/bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -datadir=$DIR/.bitcoin/ -rpcport=2521 &
    sleep 2
fi

$PYTHON_EXEC $DIR/src/run_oracle.py $@
