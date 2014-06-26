#!/bin/bash

PYTHON_EXEC=python2

wget https://bitcoin.org/bin/0.9.1/bitcoin-0.9.1-linux.tar.gz
tar -zxvf bitcoin-0.9.1-linux.tar.gz
mv ./bitcoin-0.9.1-linux ./bitcoin
rm bitcoin-0.9.1-linux.tar.gz

git clone git://github.com/Bitmessage/PyBitmessage.git

cp src/settings_local.py.example src/settings_local.py

mkdir ./.bitcoin/
touch ./.bitcoin/bitcoin.conf

BTCRPC=`openssl rand -hex 32`
echo rpcuser=bitrpc >> ./.bitcoin/bitcoin.conf
echo rpcpassword=$BTCRPC >> ./.bitcoin/bitcoin.conf
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> src/settings_local.py


BITMESSAGE_HOME=$(pwd)/PyBitmessage/
export BITMESSAGE_HOME

$PYTHON_EXEC PyBitmessage/src/bitmessagemain.py > /dev/null &
sleep 5
pkill -x $PYTHON_EXEC

echo port = 2522 >> PyBitmessage/keys.dat
echo daemon = true >> PyBitmessage/keys.dat
echo apienabled = true >> PyBitmessage/keys.dat
echo apiport = 2523 >> PyBitmessage/keys.dat
echo apiinterface = 127.0.0.1 >> PyBitmessage/keys.dat
echo apiusername = bitrpc >> PyBitmessage/keys.dat

BMPW=`openssl rand -hex 32`
echo "apipassword = $BMPW" >> keys.dat
echo BITMESSAGE_PASSWORD = \"$BMPW\" >> src/settings_local.py

echo "done."
