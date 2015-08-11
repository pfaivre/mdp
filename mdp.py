#!/usr/bin/env python3

__title__ = "mdp"
__copyright__ = "Copyright 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPL"
__version__ = "0.3.0"
__date__ = "2015-08-11"
__maintainer__ = "Pierre Faivre"
__status__ = "Development"

import errno
from getpass import getpass
import json
import os
from os.path import expanduser
import sys
try:
    import pyperclip as pyperclip
except ImportError:
    # TODO: Make the pyperclip missing error non blocking
    print("mdp: Error: The module pyperclip is missing", file=sys.stderr)
    sys.exit(1)

from Keychain import Keychain, Password
from Cryptography import Cryptography, CorruptedError

DEFAULT_OUTPUT_DIR = expanduser("~")
VALID_COMMANDS = ("get", "set", "del", "exit")


def create_pass_file(file_path: str) -> str:
    """ Create a new pass file
    :param file_path: Full path to the file
    :return: The new master password entered by the user
    :rtype : str
    """
    new_password = None
    print("Please enter a password to protect this file.")

    password_match = False
    while not password_match:
        new_password = getpass(prompt="New password: ")
        if len(new_password) < 3:
            print("The password must have at least 3 characters.")
            continue

        confirm_password = getpass(prompt="Confirm password: ")

        if not new_password.__eq__(confirm_password):
            print("The passwords don't match, please retry.")
        else:
            password_match = True

    save_pass_file(file_path, [], new_password)

    return new_password


def load_pass_file(file_path: str) -> list:
    """ Loads passwords from the crypted Json file
    :param file_path:
    :return: List of the passwords in the file
    :rtype : list
    """
    with open(file_path, "rb") as file:
        # Reads the crypted file
        file_crypted = file.read()

    c = Cryptography()
    correct_password = False
    while not correct_password:
        master_password = getpass()
        try:
            correct_password = c.validate(file_crypted, master_password)
        except CorruptedError as e:
            print("mdp: Error: The file '{0}' seems to be corrupted."
                  .format(file_path),
                  file=sys.stderr)
            sys.exit(1)

        if not correct_password:
            print("Wrong password, try again.")

    try:
        file_decrypted = c.decrypt(file_crypted, master_password)
    except UnicodeDecodeError as e:
        print("mdp: Error: Error while decrypting the file. " + e.__str__(),
              file=sys.stderr)
        sys.exit(1)

    try:
        json_passwords = json.loads(file_decrypted)
    except ValueError as e:
        print("mdp: Error: Unable to parse the file. " + e.__str__(),
              file=sys.stderr)
        sys.exit(1)

    # TODO: Add an automatic Json parser
    passwords = []
    for p in json_passwords:
        passwords.append(Password(p["domain"], p["login"], p["password"]))

    return passwords, master_password


def save_pass_file(file_path: str, passwords: list, master_password: str):
    """ Encrypt and save a Json file containing the passwords
    :param file_path: File to write the passwords
    :param passwords: List of the passwords to write
    :param master_password: Password to encrypt the file
    """
    json_passwords = json.dumps(obj=passwords,
                                default=lambda o: o.__dict__,
                                sort_keys=True,
                                indent=4)

    c = Cryptography()
    crypted_passwords = c.encrypt(json_passwords, master_password)

    with open(file_path, 'wb') as file:
        file.write(crypted_passwords)


def get_password(file_path: str, domain=None, login=None):
    """ Helps the user to get a password
    :param file_path: Path to the passwords file
    :param domain: Filter by domain
    :param login: Filter by login
    """
    passwords, master_password = load_pass_file(file_path)

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
        print("    \033[00;33m{0}. \033[00;00m{1}".format(i+1, p))

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
    """ Helps the user to define a password
    :param file_path: Path to the passwords file
    :param domain: The domain
    :param login: The login
    """
    passwords, master_password = load_pass_file(file_path)

    # Getting the informations
    if domain is None:
        domain = input("Domain for the new password > ")
    if login is None:
        login = input("Login for the new password > ")
    new_password = getpass("Password for this account > ")

    # Searching for an existing entry with theses informations
    match_passwords = list(filter(lambda p: domain == p.domain, passwords))
    match_passwords = list(filter(lambda p: login == p.login, match_passwords))

    # In case this password already exists
    if len(match_passwords) > 0:
        print("this account already exists, do you want to update the "
              "password? (y, n)")
        answer = input("> ")
        if answer.lower() in ("y", "yes"):
            # Update it
            match_passwords[0].password = new_password
        else:
            return
    # In case it doesn't exists yet
    else:
        # Create it
        passwords.append(Password(domain, login, new_password))

    # And finally write it on the file
    save_pass_file(file_path, passwords, master_password)


def del_password(file_path: str, domain=None, login=None):
    """ Helps the user to delete a(some) password(s)
    :param file_path: Path to the passwords file
    :param domain: Filter by domain
    :param login: Filter by login
    """
    passwords, master_password = load_pass_file(file_path)

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
        print("    \033[00;33m{0}. \033[00;00m{1}".format(i+1, p))

    # Selecting which ones to delete
    numbers = ()
    while len(numbers) <= 0:
        try:
            user_input = input("Which ones to delete? > ")
            # Splits the strings and deletes duplicates with set()
            user_input = set(user_input.split())
            # Converts in int() the numbers entered by the user
            numbers = sorted([int(n) for n in user_input
                              if 0 < int(n) <= len(match_passwords)])
        except ValueError:
            numbers = ()

    # Deletes the selected entries
    for i in reversed(numbers):
        passwords.remove(match_passwords[i-1])

    # And finally save the changes
    save_pass_file(file_path, passwords, master_password)


def main(argv: list):
    mode = ""
    domain = None
    login = None

    # Checking arguments
    if len(argv) == 0:
        mode = "interactive"
    elif argv[0] in ("get", "set", "del"):
        mode = argv[0]
        # Getting optional arguments domain and login
        if len(argv) > 1:
            domain = argv[1]
        if len(argv) > 2:
            login = argv[2]
    else:
        print("mdp: error: unrecognized arguments: {0}".format(argv[0]),
              file=sys.stderr)
        sys.exit(errno.EINVAL)

    # TODO: Let the user configure the password file
    # Checking pass file
    pass_file_path = os.path.join(DEFAULT_OUTPUT_DIR, "pass.txt")

    if not os.path.isfile(pass_file_path):
        print("{0} is not found, it will be created."
              .format(pass_file_path))
        master_password = create_pass_file(pass_file_path)

    # Executing user command
    if mode == "interactive":
        mode = ""
        while mode not in VALID_COMMANDS:
            mode = input("What do you want to do? {0}\n> "
                         .format(VALID_COMMANDS))
            # TODO: Add a help and version commands
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
