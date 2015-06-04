#!/bin/bash

tflag=no
set -- $(getopt t "$@")
while [ $# -gt 0 ]
do
    case "$1" in
    (-t) tflag=yes;;
    (--) shift; break;;
    (-*) echo "$0: error - unrecognized option $1" 1>&2; exit 1;;
    (*)  break;;
    esac
    shift
done

sudo apt-get update
sudo apt-get install python-dev vim screen
sudo pip install -r requirements.txt

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOME="$DIR/.."

wget --directory-prefix=$HOME https://bitcoin.org/bin/bitcoin-core-0.9.1/bitcoin-0.9.1-linux.tar.gz
tar -C $HOME -zxvf $HOME/bitcoin-0.9.1-linux.tar.gz
mv $HOME/bitcoin-0.9.1-linux $HOME/bitcoin
rm $HOME/bitcoin-0.9.1-linux.tar.gz

cp $DIR/src/settings_local.py.example $DIR/src/settings_local.py

if [ "$tflag" == "yes" ]
then
  echo BITCOIND_TEST_MODE=True >> $DIR/src/settings_local.py
fi


mkdir $HOME/.bitcoin/
touch $HOME/.bitcoin/bitcoin.conf

BTCRPC=`openssl rand -hex 32`
echo rpcuser=bitrpc >> $HOME/.bitcoin/bitcoin.conf
echo rpcpassword=$BTCRPC >> $HOME/.bitcoin/bitcoin.conf
if [ "$tflag" == "yes" ]
then
  echo connect=127.0.0.1:8333 >> $HOME/.bitcoin/bitcoin.conf
fi
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> $DIR/src/settings_local.py
