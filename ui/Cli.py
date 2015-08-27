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
except Exception as e:
    print("mdp: Error: Unable to initialize pyperclip: {error}"
          .format(error=e), file=sys.stderr)
    sys.exit(1)

from Keychain import Keychain
from ui.BaseInterface import BaseInterface


VALID_COMMANDS = ("get", "set", "del", "exit")


class Cli(BaseInterface):
    """ Basic command line user interface
    """

    def __init__(self, file_path):
        super().__init__(file_path)

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

    def start(self):
        mode = ""
        while mode not in VALID_COMMANDS:
            mode = input("What do you want to do? {0}\n> "
                         .format(VALID_COMMANDS))
            if mode not in VALID_COMMANDS:
                print("Unknown command : '{0}'".format(mode))

        if mode == "get":
            self.get_password()
        elif mode == "set":
            self.set_password()
        elif mode == "del":
            self.del_password()
        elif mode == "exit":
            return

    def get_password(self, pattern=None):
        """ Helps the user to get a password
        :param pattern: Filter
        """
        passwords = self._load_pass_file()

        if pattern is None:
            pattern = input("Any specific domain or login? (leave blank if not) > ")

        match_passwords = passwords.filter(pattern)

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

    def del_password(self, pattern=None):
        """ Helps the user to delete a(some) password(s)
        :param pattern: Filter
        """
        passwords = self._load_pass_file()

        if pattern is None:
            pattern = input("Any specific domain or login? (leave blank if not) > ")

        # Filtering results
        match_passwords = passwords.filter(pattern)

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
