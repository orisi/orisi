#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="~/"

if [ -z $(pgrep $PYTHON_EXEC) ]
then
    $PYTHON_EXEC $HOME/PyBitmessage/src/bitmessagemain.py > /dev/null &
    sleep 2
fi

if [ -z $(pgrep bitcoind) ]
then
    $HOME/bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -rpcport=2521 &
    sleep 2
fi

$PYTHON_EXEC $DIR/src/run_oracle.py $@
