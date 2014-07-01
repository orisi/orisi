#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="$DIR/.."

if [ -z $(pgrep $PYTHON_EXEC) ]
then
	cd ..
    BITMESSAGE_HOME=$HOME/PyBitmessage/
    export BITMESSAGE_HOME
    $PYTHON_EXEC $HOME/PyBitmessage/src/bitmessagemain.py
fi
