#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z $(pgrep $PYTHON_EXEC) ]
then

	echo "bitmessage not running?"

fi

if [ -z $(pgrep bitcoind) ]
then
    $DIR/../bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 -datadir=$DIR/../.bitcoin/ -rpcport=2521 &
    sleep 2
fi

$PYTHON_EXEC $DIR/src/client/main.py $@
