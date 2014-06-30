#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

wget --directory-prefix=$DIR https://bitcoin.org/bin/0.9.1/bitcoin-0.9.1-linux.tar.gz
tar -C $DIR -zxvf $DIR/bitcoin-0.9.1-linux.tar.gz
mv $DIR/bitcoin-0.9.1-linux $DIR/bitcoin
rm $DIR/bitcoin-0.9.1-linux.tar.gz

git clone git://github.com/Bitmessage/PyBitmessage.git $DIR/PyBitmessage

cp $DIR/src/settings_local.py.example $DIR/src/settings_local.py

mkdir $DIR/.bitcoin/
touch $DIR/.bitcoin/bitcoin.conf

BTCRPC=`openssl rand -hex 32`
echo rpcuser=bitrpc >> $DIR/.bitcoin/bitcoin.conf
echo rpcpassword=$BTCRPC >> $DIR/.bitcoin/bitcoin.conf
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> $DIR/src/settings_local.py


BITMESSAGE_HOME=$DIR/PyBitmessage/
export BITMESSAGE_HOME

$PYTHON_EXEC $DIR/PyBitmessage/src/bitmessagemain.py > /dev/null &
sleep 5
pkill -x $PYTHON_EXEC

echo daemon = true >> $DIR/PyBitmessage/keys.dat
echo apienabled = true >> $DIR/PyBitmessage/keys.dat
echo apiport = 2523 >> $DIR/PyBitmessage/keys.dat
echo apiinterface = 127.0.0.1 >> $DIR/PyBitmessage/keys.dat
echo apiusername = bitrpc >> $DIR/PyBitmessage/keys.dat

BMPW=`openssl rand -hex 32`
echo "apipassword = $BMPW" >> $DIR/PyBitmessage/keys.dat
echo BITMESSAGE_PASSWORD = \"$BMPW\" >> $DIR/src/settings_local.py

