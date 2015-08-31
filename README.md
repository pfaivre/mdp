mdp
===

## Name
mdp - User friendly password storage tool.

It comes from the french "*Mot De Passe*"

## Description
this program can store your passwords on a encrypted file and allows you to
access it in a very simple way.

![mdp in action](docs/images/mdp-0.4.0.gif)

Each password has 3 information:
* Domain : (or service or URL) where the account is registered
* Login : identifier for the account
* Password

This program doesn't interact with keyring or any other key manager.
All the passwords are stored in a human readable text file; which is encrypted
with a master password using the highly secure AES algorithm.

## Installation
See [installation notes](docs/Installation.md) to know how to use mdp.

## Usage
The program is fully interactive :
```sh
$ mdp.py
```

You can also use these parameters:

`-h --help`
Output some help and exit

`-v --version`
Output version information and exit

## License
Copyright © 2015 Pierre Faivre. This is free software, and may be redistributed
under the terms specified in the LICENSE file.

