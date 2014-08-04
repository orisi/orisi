#Orisi - Distributed Oracle System

**Orisi is a distributed system of oracle nodes which validates smart contracts safely. Such contracts, unlike blockchain-only ones, can rely on external conditions.**

Basic Bitcoin and Ethereum contracts cannot - by themselves - use external inputs, like stock prices or checking website urls for data. Orisi solves this dependency problem by creating a distributed network in which the majority of oracles have to agree to have a transaction validated. This distributed system makes it exponentially harder to bribe or otherwise influence the oracles, and is still able to validate a contract if one or more of the oracles fail.

## Orisi Tutorial

Completing those steps should take you 2-3 working days, and will end up with your own contract, and a thorough understanding of the Orisi distributed oracles system.

1. [Read the White Paper](https://github.com/orisi/wiki/wiki/Orisi-White-Paper) - Introduction to Orisi
2. [Create a timelock transaction](https://github.com/orisi/wiki/wiki/Performing-a-Timelock-transaction) - A thorough explanation of how to install the client and create a timelock transaction
3. [Understand how the timelock works](https://www.youtube.com/watch?v=boPW1FwNu4c) - a Khan-academy style video explaning how the process works
4. [Create your own contract in 29 easy steps](https://github.com/orisi/wiki/wiki/How-to-create-a-contract)
5. [Ask questions!](https://github.com/orisi/orisi/issues/new) - Questions, ideas? Create a new issue on Github


## Contribute to Orisi

* [Install and run the oracle node](https://github.com/orisi/wiki/wiki/Installing-the-oracle-node) - Instructions for setting up an oracle node

---------------------

Contribute to the code base! The main programs are split into the oracle and client folders, with a shared folder including other resources:

* [src/oracle](./src/oracle) - Oracle node source

* [src/client](./src/client) - Reference client source

* [src/shared](./src/shared) - Shared resources

---------------------

_Please keep in mind that both the client and oracle are in very early alpha versions and are unstable. We encourage you to use them and test them. Please post any issue to the [Issue Tracker](https://github.com/orisi/orisi/issues). If you have any fixes do not hesitate to [pull request](https://github.com/orisi/orisi/pulls)_
