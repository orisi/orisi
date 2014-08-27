#!/bin/bash

sudo apt-get update
sudo apt-get install python-dev vim screen
sudo pip install -r requirements.txt

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="$DIR/.."

wget --directory-prefix=$HOME https://bitcoin.org/bin/0.9.1/bitcoin-0.9.1-linux.tar.gz
tar -C $HOME -zxvf $HOME/bitcoin-0.9.1-linux.tar.gz
mv $HOME/bitcoin-0.9.1-linux $HOME/bitcoin
rm $HOME/bitcoin-0.9.1-linux.tar.gz

cp $DIR/src/settings_local.py.example $DIR/src/settings_local.py

mkdir $HOME/.bitcoin/
touch $HOME/.bitcoin/bitcoin.conf

BTCRPC=`openssl rand -hex 32`
echo rpcuser=bitrpc >> $HOME/.bitcoin/bitcoin.conf
echo rpcpassword=$BTCRPC >> $HOME/.bitcoin/bitcoin.conf
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> $DIR/src/settings_local.py
