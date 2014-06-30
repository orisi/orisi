#!/bin/bash

PYTHON_EXEC=python2.7
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="~/"

wget --directory-prefix=$HOME https://bitcoin.org/bin/0.9.1/bitcoin-0.9.1-linux.tar.gz
tar -C $HOME -zxvf $HOME/bitcoin-0.9.1-linux.tar.gz
mv $HOME/bitcoin-0.9.1-linux $HOME/bitcoin
rm $HOME/bitcoin-0.9.1-linux.tar.gz

git clone git://github.com/Bitmessage/PyBitmessage.git $HOME/PyBitmessage

cp $DIR/src/settings_local.py.example $DIR/src/settings_local.py

mkdir $HOME/.bitcoin/
touch $HOME/.bitcoin/bitcoin.conf

BTCRPC=`openssl rand -hex 32`
echo rpcuser=bitrpc >> $HOME/.bitcoin/bitcoin.conf
echo rpcpassword=$BTCRPC >> $HOME/.bitcoin/bitcoin.conf
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> $DIR/src/settings_local.py

$PYTHON_EXEC $HOME/PyBitmessage/src/bitmessagemain.py > /dev/null &
sleep 5
pkill -x $PYTHON_EXEC

echo daemon = true >> $HOME/.config/PyBitmessage/keys.dat
echo apienabled = true >> $HOME/.config/PyBitmessage/keys.dat
echo apiport = 2523 >> $HOME/.config/PyBitmessage/keys.dat
echo apiinterface = 127.0.0.1 >> $HOME/.config/PyBitmessage/keys.dat
echo apiusername = bitrpc >> $HOME/.config/PyBitmessage/keys.dat

BMPW=`openssl rand -hex 32`
echo "apipassword = $BMPW" >> $Home/.config/PyBitmessage/keys.dat
echo BITMESSAGE_PASSWORD = \"$BMPW\" >> $DIR/src/settings_local.py

