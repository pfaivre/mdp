#!/usr/bin/env python3

from getpass import getpass
import os
import sys

try:
    import pyperclip as pyperclip
except ImportError:
    # TODO: Make the pyperclip missing error non blocking
    print("mdp: Error: The module pyperclip is missing", file=sys.stderr)
    sys.exit(1)

from Cryptography import Cryptography, CorruptedError
from Keychain import Keychain


VALID_COMMANDS = ("get", "set", "del", "exit")


class Cli:
    """ Command line user interface
    """

    def __init__(self, file_path):
        self._master_password = None
        self._file_path = file_path

        if not os.path.isfile(self._file_path):
            print("{0} is not found, it will be created."
                  .format(self._file_path))
            self._create_pass_file()

    def _create_pass_file(self):
        """ Create a new pass file
        """
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
                self._master_password = new_password
                password_match = True

        self._save_pass_file(Keychain())

    def _load_pass_file(self):
        """ Loads passwords from the crypted Json file
        :return: List of the passwords in the file
        :rtype : Keychain
        """
        with open(self._file_path, "rb") as file:
            file_crypted = file.read()

        c = Cryptography()
        correct_password = False
        while not correct_password:
            if self._master_password is not None:
                try:
                    correct_password = c.validate(file_crypted,
                                                  self._master_password)
                except CorruptedError:
                    print("mdp: Error: The file '{0}' seems to be corrupted."
                          .format(self._file_path),
                          file=sys.stderr)
                    sys.exit(1)

            if not correct_password:
                if self._master_password is not None:
                    print("Wrong password, try again.")
                self._master_password = getpass()

        try:
            file_decrypted = c.decrypt(file_crypted, self._master_password)
        except UnicodeDecodeError as e:
            print("mdp: Error: Unable to decrypt the file. " + e.__str__(),
                  file=sys.stderr)
            sys.exit(1)

        try:
            passwords = Keychain(file_decrypted)
        except ValueError as e:
            print("mdp: Error: Unable to parse the file. " + e.__str__(),
                  file=sys.stderr)
            sys.exit(1)

        return passwords

    def _save_pass_file(self, passwords):
        """ Encrypt and save a Json file containing the passwords
        :param passwords: List of the passwords to write
        :type passwords: Keychain
        """
        json_passwords = passwords.to_json()

        c = Cryptography()
        crypted_passwords = c.encrypt(json_passwords, self._master_password)

        with open(self._file_path, 'wb') as file:
            file.write(crypted_passwords)

    def start(self, mode="interactive", domain=None, login=None):
        if mode == "interactive":
            mode = ""
            while mode not in VALID_COMMANDS:
                mode = input("What do you want to do? {0}\n> "
                             .format(VALID_COMMANDS))
                if mode not in VALID_COMMANDS:
                    print("Unknown command : '{0}'".format(mode))

        if mode == "get":
            self.get_password(domain, login)
        elif mode == "set":
            self.set_password(domain, login)
        elif mode == "del":
            self.del_password(domain, login)
        elif mode == "exit":
            return

    def get_password(self, domain=None, login=None):
        """ Helps the user to get a password
        :param domain: Filter by domain
        :param login: Filter by login
        """
        passwords = self._load_pass_file()

        if domain is None:
            domain = input("Any specific domain? (leave blank if not) > ")
        if login is None:
            login = input("Any specific login? (leave blank if not) > ")

        match_passwords = passwords.filter(domain, login)

        if len(match_passwords) <= 0:
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

    def set_password(self, domain=None, login=None):
        """ Helps the user to define a password
        :param domain: The domain
        :param login: The login
        """
        passwords = self._load_pass_file()

        # Getting the informations
        if domain is None:
            domain = input("Domain for the new password > ")
        if login is None:
            login = input("Login for the new password > ")
        new_password = getpass("Password for this account > ")

        # Trying to add the entry
        is_added = passwords.set(domain, login, new_password)

        # In case this entry already exists
        if not is_added:
            print("this account already exists, do you want to update the "
                  "password? (y, n)")
            answer = input("> ")
            if answer.lower() in ("y", "yes"):
                # Update it
                passwords.set(domain, login, new_password, replace=True)
            else:
                return

        # And finally write it on the file
        self._save_pass_file(passwords)

    def del_password(self, domain=None, login=None):
        """ Helps the user to delete a(some) password(s)
        :param domain: Filter by domain
        :param login: Filter by login
        """
        passwords = self._load_pass_file()

        if domain is None:
            domain = input("Any specific domain? (leave blank if not) > ")
        if login is None:
            login = input("Any specific login? (leave blank if not) > ")

        # Filtering results
        match_passwords = passwords.filter(domain, login)

        if len(match_passwords) <= 0:
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
            passwords.delete(match_passwords[i-1])

        # And finally save the changes
        self._save_pass_file(passwords)
