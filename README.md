#Orisi - Distributed Oracle System

**Orisi is a distributed system of anonymous oracle nodes which safely validates smart contracts using external conditions.**

Basic Bitcoin and Ethereum contracts cannot - by themselves - use external inputs, like stock prices or checking website urls for data. Orisi solves this dependency problem by creating a distributed network in which the majority of oracles have to agree to have a transaction validated. This distributed system makes it exponentially harder to bribe or otherwise influence the oracles, and is still able to validate a contract if one or more of the oracles fail.

## Learn about Orisi

1. [Read the White Paper](https://github.com/orisi/wiki/wiki/Orisi-White-Paper) - Introduction to Orisi
2. [Create a timelock transaction](https://github.com/orisi/wiki/wiki/Performing-a-Timelock-transaction) and [understand how it works](https://www.youtube.com/watch?v=boPW1FwNu4c) - A thorough explanation of how to install the client and create a timelock transaction, and a Khan-academy style video explaning how the process works
3. [Ask questions!](https://github.com/orisi/orisi/issues/new) - Questions, ideas? Create a new issue on Github


## Contribute to Orisi

* [Install and run the oracle node](https://github.com/orisi/wiki/wiki/Installing-the-oracle-node) - Instructions for setting up an oracle node

---------------------

Contribute to the code base! The main programs are split into the oracle and client folders, with a shared folder including other resources:

* [src/oracle](./src/oracle) - Oracle node source

* [src/client](./src/client) - Reference client source

* [src/shared](./src/shared) - Shared resources

---------------------

_Please keep in mind that both the client and oracle are in very early alpha versions and are unstable. We encourage you to use them and test them. Please post any issue to the [Issue Tracker](https://github.com/orisi/orisi/issues). If you have any fixes do not hesitate to [pull request](https://github.com/orisi/orisi/pulls)_
