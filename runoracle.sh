#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="$DIR/.."

if [ -z $(pgrep $PYTHON_EXEC) ]
then
    BITMESSAGE_HOME=$HOME/PyBitmessage/
    export BITMESSAGE_HOME
    $PYTHON_EXEC $HOME/PyBitmessage/src/bitmessagemain.py > bm_error.log &
    sleep 2
fi

if [ -z $(pgrep bitcoind) ]
then
    $HOME/bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -datadir=$HOME/.bitcoin/ -rpcport=2521 &
    sleep 2
fi

echo "running oracle"

$PYTHON_EXEC $DIR/src/run_oracle.py $@
