# Installing the Orisi Node without Vagrant

We highly recommend using a Vagrant box to run the Orisi node. First of all, it comes with bitcoind and bitmessage preinstalled. Second of all, you never want to run both the client and the Orisi sever on a same machine due to bitcoind & bitmessage conflicts.

But if you really want to run Orisi without Vagrant, do this:

1. Install [Bitcoin](https://bitcoin.org/en/download) (only the `bitcoind` executable is needed)
1. Install [PyBitmessage](https://github.com/Bitmessage/PyBitmessage)
1. Install the requirements, `python2` and the python library `jsonrpclib`
1. Run `PyBitmessage` once (src/bitmessagemain.py) to create the basic configuration files, and then [enable the API](https://www.bitmessage.org/wiki/API_Reference).
1. Edit `scripts/secrets.sh` to match the paths in your system and run it once
1. Restart `PyBitmessage` and run `bitcoind` by editing the paths of the scripts in the `orisi/scripts` folder
1. Run `python2 orisi/src/run_oracle.py` to start up the oracle node, and you should see recurring POST requests after your initial addresses are printed.

*Please report any errors you have with this build process [to the issue tracker](https://github.com/orisi/orisi/issues?state=open)*

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
    /vagrant/scripts/runbitcoind.sh
    /vagrant/scripts/runbitmessage.sh
    ```
    
1. If you wanted to run an oracle:
    ```
    cd /vagrant/src/
    python run_oracle.py
    ```

    After the first oracle run, a private bitcoin address will be generated, and you'll be asked to copy it into your settings file.

1. If you wanted to run the client
    ```
    cd /vagrant/client/
    python main.py help
    ```

    *Don't run both client and the oracle on one box!* They need separate instances of Bitcoind, and Bitmessage. The easiest way to run both an Orisi node, and an Orisi client on one computer is to launch two Vagrant boxes.


## Why Vagrant?

Vagrant makes it extremely easy to set up an oracle and launch tests. Without Vagrant, a host would need to set up a VirtualBox or run two instances of bitcoind/bitmessage, one personal and one for the oracle. Vagrant standarizes the install process and makes it simpler to keep oracles up to date.
