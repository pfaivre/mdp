#!/usr/bin/env python3

#     mdp - Basic command line user interface
#     Copyright (C) 2015 Pierre Faivre
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 3 of the License, or
#     any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from getpass import getpass
import os
from os import path
import sys

# l10n configuration
# To generate POT file:
# $ xgettext --language=Python --keyword=_ --add-comments="." --output=./locale/mdp.pot *.py ui/*.py
import locale
import gettext
# ./../locale
locale_dir = path.join(path.dirname(path.dirname(path.realpath(__file__))),
                       'locale')
USER_LOCALE = locale.getlocale()[0]
USER_LOCALE = USER_LOCALE if USER_LOCALE is not None else 'en'
try:
    # Trying to get the translations given the user localization.
    lang = gettext.translation('mdp',
                               localedir=locale_dir,
                               languages=[USER_LOCALE])
    lang.install()
except FileNotFoundError:
    # If the localization is not found, fall back to the default strings.
    _ = lambda s: s

try:
    import pyperclip as pyperclip
except ImportError:
    # TODO: Make the pyperclip missing error non blocking
    print(_("mdp: Error: The module pyperclip is missing"), file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(_("mdp: Error: Unable to initialize pyperclip: {error}")
          .format(error=e), file=sys.stderr)
    sys.exit(1)

from Keychain import Keychain
from ui.BaseInterface import BaseInterface


VALID_COMMANDS = ('get', 'set', 'del', 'exit')
YELLOW = "\033[00;33m"
NORMAL = "\033[00;00m"


class Cli(BaseInterface):
    """ Basic command line user interface
    """

    def __init__(self, file_path):
        super().__init__(file_path)

        if not os.path.isfile(self._file_path):
            print(_("{filename} is not found, it will be created.")
                  .format(filename=self._file_path))
            self._create_pass_file()

    def _create_pass_file(self):
        """ Create a new pass file
        """
        print(_("Please enter a password to protect this file."))

        password_match = False
        while not password_match:
            new_password = getpass(prompt=_("New password: "))
            if len(new_password) < 3:
                print(_("The password must have at least 3 characters."))
                continue

            confirm_password = getpass(prompt=_("Confirm password: "))

            if not new_password.__eq__(confirm_password):
                print(_("The passwords don't match, please retry."))
            else:
                self._master_password = new_password
                password_match = True

        self._save_pass_file(Keychain())

    def start(self):
        mode = ''
        while mode not in VALID_COMMANDS:
            mode = input(_("What do you want to do? {commands}\n> ")
                         .format(commands=VALID_COMMANDS))
            if mode not in VALID_COMMANDS:
                print(_("Unknown command : '{0}'").format(mode))

        if mode == 'get':
            self.get_password()
        elif mode == 'set':
            self.set_password()
        elif mode == 'del':
            self.del_password()
        elif mode == 'exit':
            return

    def get_password(self, pattern=None):
        """ Helps the user to get a password
        :param pattern: Filter
        """
        passwords = self._load_pass_file()

        if pattern is None:
            pattern = input(_("Any specific domain or login?"
                              "(leave blank if not) > "))

        match_passwords = passwords.filter(pattern)

        if len(match_passwords) <= 0:
            print(_("No account for theses filters."))
            return

        # Printing matching accounts
        for i, p in enumerate(match_passwords):
            print("    {yellow}{num}. {normal}{password}"
                  .format(yellow=YELLOW, num=i+1,
                          normal=NORMAL, password=p))

        # Selecting which one to get
        number = -1 if len(match_passwords) > 1 else 1
        while number < 1 or number > len(match_passwords):
            try:
                number = int(input(_("Which one? > ")))
            except ValueError:
                number = -1

        # Put the password into the clipboard
        pwd = match_passwords[number-1].password
        pyperclip.copy(pwd)
        print(_("The password have been copied in the clipboard."))
        # TODO: Ask the user if he wants to see the password

    def set_password(self, domain=None, login=None):
        """ Helps the user to define a password
        :param domain: The domain
        :param login: The login
        """
        passwords = self._load_pass_file()

        # Getting the information
        if domain is None:
            domain = input(_("Domain for the new password > "))
        if login is None:
            login = input(_("Login for the new password > "))
        new_password = getpass(_("Password for this account > "))

        # Trying to add the entry
        is_added = passwords.set(domain, login, new_password)

        # In case this entry already exists
        if not is_added:
            print(("this account already exists, do you want to update the "
                  "password? (y, n)"))
            answer = input("> ")
            if answer.lower() in ('y', 'yes'):
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
            pattern = input(_("Any specific domain or login?"
                              "(leave blank if not) > "))

        # Filtering results
        match_passwords = passwords.filter(pattern)

        if len(match_passwords) <= 0:
            print(_("No account for theses filters."))
            return

        # Printing matching accounts
        for i, p in enumerate(match_passwords):
            print("    {yellow}{num}. {normal}{password}"
                  .format(yellow=YELLOW, num=i+1,
                          normal=NORMAL, password=p))

        # Selecting which ones to delete
        numbers = ()
        while len(numbers) <= 0:
            try:
                user_input = input(_("Which ones to delete? > "))
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
