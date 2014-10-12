#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="$DIR/.."
export LC_ALL="en_US.UTF-8"

if [ -z $(pgrep bitcoind) ]
then
    $HOME/bitcoin/bin/$(getconf LONG_BIT)/bitcoind -datadir=$HOME/.bitcoin/ -rpcport=2521 &
    sleep 2
fi

echo "running oracle"

$PYTHON_EXEC $DIR/src/run_oracle.py $@
