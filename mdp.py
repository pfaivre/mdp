#!/usr/bin/env python3
# TODO: Reorganize within a module and classes
# TODO: Create unit tests

__title__ = "mdp"
__copyright__ = "Copyright 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPL"
__version__ = "0.2"
__date__ = "2015-08-09"
__maintainer__ = "Pierre Faivre"
__status__ = "Developement"

import errno
from getpass import getpass
import hashlib
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
try:
    from Crypto.Cipher import AES
    from Crypto import Random
except ImportError:
    print("mdp: Error: The module pycrypto (python-crypto) is missing",
          file=sys.stderr)
    sys.exit(1)

DEFAULT_OUTPUT_DIR = expanduser("~")
VALID_COMMANDS = ("get", "set", "del", "exit")


class Password:
    """ Represents a password for a couple login/domain
    """
    def __init__(self, domain: str, login: str, password: str):
        self.domain = domain
        self.login = login
        self.password = password

    def __repr__(self):
        return "{0} {1}".format(self.domain, self.login)

    def __str__(self):
        return "{0}\t{1}".format(self.domain, self.login)


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
        confirm_password = getpass(prompt="Confirm password: ")

        if not new_password.__eq__(confirm_password):
            print("Error: the passwords don't match, please retry.")
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

    wrong_password = True
    while wrong_password:
        master_password = getpass()

        # Creating a key by hashing the password
        key = hashlib.sha256(master_password.encode("utf-8")).digest()

        # Creating a new instance of decrypter given the key and the IV.
        crypto = AES.new(key, AES.MODE_CBC, file_crypted[:16])

        try:
            plain = crypto.decrypt(file_crypted[16:])
        except ValueError:
            print("mdp: Error: the crypted file '{0}' seems to be corrupted."
                  .format(file_path),
                  file=sys.stderr)
            sys.exit(1)

        padding_length = int((plain[-1]))
        if padding_length > AES.block_size and padding_length != 32:
            # 32 is the space character and is kept for backwards compatibility
            wrong_password = True
        elif padding_length == 32:
            plain = plain.strip()
            wrong_password = False
        elif plain[-padding_length:] != bytes((padding_length,)) * padding_length:
            # Invalid padding!
            wrong_password = True
        else:
            plain = plain[:-padding_length]
            wrong_password = False

        if wrong_password:
            print("Wrong password, try again.")

    # Getting back to UTF-8
    file_decrypted = plain.decode("utf-8")

    json_passwords = json.loads(file_decrypted)

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

    # Creating a key by hashing the password
    key = hashlib.sha256(master_password.encode("utf-8")).digest()

    # New seed for PyCrypto
    Random.atfork()

    # Generating initialization vector
    iv = Random.new().read(AES.block_size)

    crypto = AES.new(key, AES.MODE_CBC, iv)
    plain = json_passwords.encode("utf-8")

    # Adding some data at the end to match the block size required by AES
    padding_length = AES.block_size - len(plain) % AES.block_size
    plain += bytes((padding_length,)) * padding_length

    # Finally creating the crypted data
    crypted_passwords = iv + crypto.encrypt(plain)

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
        # Getting optionnal arguments domain and login
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
