# Installing the Oracle Node

The standard and recommended way to run a node is through a Vagrant box ([Why Vagrant?](#why-vagrant)), as it allows for standarized nodes which are easy to upgrade and maintain.

1. [Download & install Vagrant](http://www.vagrantup.com/), may need [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

1. In the main Orisi folder:

    ```
    vagrant box add orisi http://oracles.li/orisi.box

    vagrant init orisi

    vagrant up

    ```

    The above initiates a Vagrant box (~1GB download, sorry about that) containing bitcoind, bitmessage, and a current oracle repo mapped onto /vagrant/

1. SSH into the box: `vagrant ssh`

1. After the first login run: `./secrets.sh`

    This will generate API passwords for bitcoind & bitmessage.

1. Then, enter the following commands:

    ```
    ./runbitcoin
    ./runbitmessage
    cd /vagrant/src/oracle/
    python main.py
    ```

This will start the bitoin & bitmessage daemons, switch you into the main oracle folder, and run the oracle.
After the first oracle run, a private bitcoin address will be generated, and you'll be asked to copy it into your settings file.

## Why Vagrant?

Vagrant makes it extremely easy to set up an oracle and launch tests. Without Vagrant, a host would need to set up a VirtualBox or run two instances of bitcoind/bitmessage, one personal and one for the oracle. Vagrant standarizes the install process and makes it simpler to keep oracles up to date.
