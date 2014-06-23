#!/bin/bash

PYTHON_EXEC=python27

$PYTHON_EXEC PyBitmessage/src/bitmessagemain.py > /dev/null &
bitcoin/bin/$(getconf LONG_BIT)/bitcoind -connect=127.0.0.1 &
sleep 5
$PYTHON_EXEC src/run_oracle.py
