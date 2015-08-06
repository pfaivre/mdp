#!/usr/bin/env python3

__copyright__ = "Copyright 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPL"
__version__ = "0.1"
__date__ = "2015-08-06"
__maintainer__ = "Pierre Faivre"
__status__ = "Developement"

from getpass import getpass
import json
import os
from os.path import expanduser
import sys
import errno
import pyperclip as pyperclip

DEFAULT_OUTPUT_DIR = expanduser("~")
VALID_COMMANDS = ("get", "set", "del", "exit")


class Password:
    def __init__(self, domain: str, login: str, password: str):
        self.domain = domain
        self.login = login
        self.password = password

    def __repr__(self):
        return "{0} {1}".format(self.domain, self.login, self.password)

    def __str__(self):
        return "{0}\t{1}".format(self.domain, self.login)


def create_pass_file(file_path: str) -> str:
    """
    Create a new pass file
    :param file_path: Full path to the file
    :return: The new master password entered by the user
    :rtype : str
    """
    new_password = None
    print("Please enter a password to protect this file.")

    password_match = False
    while not password_match:
        new_password = getpass(prompt="New password: ")
        confirm_password = getpass(prompt="Confirm password: ")

        if not new_password.__eq__(confirm_password):
            print("Error: the passwords don't match, please retry.")
        else:
            password_match = True

    # pass_file = open(file_path, "w")
    # pass_file.write("")
    # pass_file.close()

    with open(file_path, "w") as file:
        passwords = list()
        json_content = json.dumps(passwords, indent=True)
        file.write(json_content)

    return new_password


def load_pass_file(file_path: str) -> list:
    """
    :param file_path:
    :return: List of the passwords in the file
    :rtype : list
    """
    with open(file_path) as file:
        master_password = getpass()
        json_passwords = json.load(file)

    passwords = []
    for p in json_passwords:
        passwords.append(Password(p["domain"], p["login"], p["password"]))

    return passwords


def save_pass_file(file_path: str, passwords: list, user_password: str):
    """
    :param file_path:
    :param passwords:
    :param user_password: Password to encrypt the file
    """
    pass


def get_password(file_path: str, domain=None, login=None):
    """
    :param file_path: Path to the passwords file
    :param domain: Filter by domain
    :param login: Filter by login
    """
    passwords = load_pass_file(file_path)

    if domain is None:
        domain = input("Any specific domain? (leave blank if not) > ")
    if login is None:
        login = input("Any specific login? (leave blank if not) > ")

    # Filtering results
    match_passwords = [p for p in passwords if domain in p.domain]
    match_passwords = [p for p in match_passwords if login in p.login]

    if len(match_passwords) < 1:
        print("No account for theses filters.")
        return

    # Printing matching accounts
    for i, p in enumerate(match_passwords):
        print("    \033[00;33m{0}. \033[00;00m{1}\033[00;00m".format(i+1, p))

    # Selecting which one to get
    number = -1 if len(match_passwords) > 1 else 1
    while number < 1 or number > len(match_passwords):
        try:
            number = int(input("Which one? > "))
        except ValueError:
            number = -1

    # Put the password into the clipboard
    pwd = match_passwords[number-1].password
    pyperclip.copy(pwd)
    print("The password have been copied in the clipboard.")
    # TODO: Ask the user if he wants to see the password


def set_password(file_path: str, domain=None, login=None):
    """
    :param file_path: Path to the passwords file
    :param domain: The domain
    :param login: The login
    """
    passwords = load_pass_file(file_path)

    # Getting the informations
    if domain is None:
        domain = input("Domain for the new password > ")
    if login is None:
        login = input("Login for the new password > ")
    password = getpass("Password for this account > ")

    # Searching for an existing entry with theses informations
    match_passwords = list(filter(lambda p: domain == p.domain, passwords))
    match_passwords = list(filter(lambda p: login == p.login, match_passwords))

    if len(match_passwords) > 0:
        answer = input("this account already exists, do you want to update "
                       "the password? "
                       "(\033[00;32my\033[00;00m, \033[00;31mn\033[00;00m) > ")


def del_password(file_path: str, domain=None, login=None):
    """
    :param file_path: Path to the passwords file
    :param domain: Filter by domain
    :param login: Filter by login
    """
    raise NotImplementedError("del")


def main(argv: list):
    mode = ""
    domain = None
    login = None

    # Checking arguments
    if len(argv) == 0:
        mode = "interactive"
    elif argv[0] in ("get", "set", "del"):
        mode = argv[0]
        # Getting optionnal arguments domain and login
        if len(argv) > 1:
            domain = argv[1]
        if len(argv) > 2:
            login = argv[2]
    else:
        print("mdp: error: unrecognized arguments: {0}".format(argv[0]),
              file=sys.stderr)
        sys.exit(errno.EINVAL)

    # Checking pass file
    pass_file_path = os.path.join(DEFAULT_OUTPUT_DIR, "pass.txt")

    if not os.path.isfile(pass_file_path):
        print("{0} is not found, it will be created."
              .format(pass_file_path))
        user_password = create_pass_file(pass_file_path)

    # Executing user command
    if mode == "interactive":
        mode = ""
        while mode not in VALID_COMMANDS:
            mode = input("What do you want to do? {0}\n> "
                         .format(VALID_COMMANDS))
            if mode not in VALID_COMMANDS:
                print("Unknown command : '{0}'".format(mode))

    if mode == "get":
        get_password(pass_file_path, domain, login)
    elif mode == "set":
        set_password(pass_file_path, domain, login)
    elif mode == "del":
        del_password(pass_file_path, domain, login)
    elif mode == "exit":
        return


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("")
    except EOFError:
        print("")
    except NotImplementedError as e:
        print("Sorry the functionality '{0}' has not been implemented yet."
              .format(e), file=sys.stderr)
