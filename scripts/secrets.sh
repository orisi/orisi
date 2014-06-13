#!/bin/bash
cp /vagrant/src/settings_local.py.example /vagrant/src/settings_local.py

BTCRPC=`openssl rand -hex 32` 
echo rpcpassword=$BTCRPC >> ~/.bitcoin/bitcoin.conf 
echo BITCOIND_RPC_PASSWORD = \"$BTCRPC\" >> /vagrant/src/settings_local.py


BMPW=`openssl rand -hex 32`
echo "[bitmessagesettings]" >> ~/.config/PyBitmessage/keys.dat
echo "apipassword = $BMPW" >> ~/.config/PyBitmessage/keys.dat
echo BITMESSAGE_PASSWORD = \"$BMPW\" >> /vagrant/src/settings_local.py

echo "done."
