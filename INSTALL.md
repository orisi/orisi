# Installing the Orisi Node without Vagrant

We highly recommend using a Vagrant box to run the Orisi node. First of all, it comes with bitcoind and bitmessage preinstalled. Second of all, you never want to run both the client and the Orisi sever on a same machine due to bitcoind & bitmessage conflicts.

But if you really want to run Orisi without Vagrant, do this:
   ```
   Install *Bitcoind*
   Install *Bitmessage*
   adjust *scripts/secrets.sh* to match paths in your system
   run *scripts/secrets.sh* once
   ```   

After the above, you should be all set up.

# Installing the Orisi Node with Vagrant

The standard and recommended way to run a node is through a Vagrant box ([Why Vagrant?](#why-vagrant)), as it allows for standarized nodes which are easy to upgrade and maintain.

1. [Download & install Vagrant](http://www.vagrantup.com/), may need [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

1. In the main Orisi folder:
    
    _It seems that our ISP has trouble handling the large files. We put up a mirror on Mega:
    https://mega.co.nz/#!HQwmWSzb!QvJ3CB2k8Xv-hQVSQpDiWsREN9YxhVZ7Qt-O5Z3WzPg
    you can download it using a browser and then do
    `vagrant box add orisi path/to/orisi.box` instead of the first command below_

    ```
    vagrant box add orisi http://oracles.li/orisi.box

    vagrant init orisi

    vagrant up

    ```

    The above initiates a Vagrant box (~1GB download, sorry about that) containing bitcoind, bitmessage, and a current oracle repo mapped onto /vagrant/

1. SSH into the box: `vagrant ssh`

1. After the first login run: `/vagrant/scripts/secrets.sh`

    This will generate API passwords for bitcoind & bitmessage.

1. Then, enter the following commands:

    ```
    /vagrant/scripts/runbitcoin
    /vagrant/scripts/runbitmessage
    ```
    
1. If you wanted to run an oracle:
    ```
    cd /vagrant/src/
    python run_oracle.py
    ```

1. If you wanted to run the client, check out */vagrant/src*
    Please keep in mind that you don't want to run both the oracle, and the oracle client on one box. They need separate instances of Bitcoind, and Bitmessage. The easiest way to run both an Orisi node, and an Orisi client on one computer is to launch two Vagrant boxes.

This will start the bitoin & bitmessage daemons, switch you into the main oracle folder, and run the oracle.
After the first oracle run, a private bitcoin address will be generated, and you'll be asked to copy it into your settings file.

## Why Vagrant?

Vagrant makes it extremely easy to set up an oracle and launch tests. Without Vagrant, a host would need to set up a VirtualBox or run two instances of bitcoind/bitmessage, one personal and one for the oracle. Vagrant standarizes the install process and makes it simpler to keep oracles up to date.
