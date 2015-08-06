mdp
===

## Name
mdp - User friendly password storage tool.

It comes from the french "*Mot De Passe*"

## Description
this program can store your passwords on a crypted file and allows you to acces
it in a very simple way.

Each password has 3 informations:
* Domain : (or service or URL) where the account is registred
* Login : identifier for the account
* Password

This program doesn't interact with keyring or any other key manager.
All the passwords are stored in a human readable text file; which is crypted
with a master password using the highly secure AES algorithm.

## Usage
To get the password associated to an account:
```sh
$ mdp get [domain] [login]
```

To add a new password:
```sh
$ mdp add [domain] [login]
```

To delete an existing password:
```sh
$ mdp del [domain] [login]
```

All the arguments are optional.

## License
Copyright 2015 Pierre Faivre. This is free software, and may be redistributed
under the terms specified in the LICENSE file.

