# Installing the Orisi Oracle Node

Orisi installs both Bitcoin and Bitmessage, so it is **highly suggested that you run it in either a server without either of these installed or a self contained Vagrant box**. These install instructions will detail an installation with Vagrant, but they are very similar for a typical linux install.

Requirements: python2, jsonrpclib python library (`pip install jsonrpclib`)

1. [Install Vagrant](http://docs.vagrantup.com/v2/installation/index.html)
1. [Setup a basic hashicorp/precise32 (Ubuntu 12.04) box and ssh into it](http://docs.vagrantup.com/v2/getting-started/index.html)
1. Install git and pip (`sudo apt-get install python-pip git`) and run `sudo pip install jsonrpclib`
1. Clone this repository with `git clone https://github.com/orisi/orisi`
1. `cd` into the Orisi directory, `cd ./orisi`, and run `installoracle.sh` (may have to run `chmod +x ./installoracle.sh` first)
1. Run `runoracle.sh` (may have to do the same as above to run it)

[Please report any issues you have!](https://github.com/orisi/orisi/issues?state=open)
