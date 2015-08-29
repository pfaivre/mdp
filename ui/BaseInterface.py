#!/usr/bin/env python3

#     mdp - Base class for the user interfaces
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

from Cryptography import Cryptography, CorruptedError
from Keychain import Keychain


class BaseInterface:
    """ Base class for all user interfaces
    """

    def __init__(self, file_path):
        self._master_password = None
        self._file_path = file_path

    def start(self):
        pass

    def _load_pass_file(self):
        """ Loads passwords from the crypted Json file
        :return: List of the passwords in the file
        :rtype : Keychain
        """
        with open(self._file_path, 'rb') as file:
            file_crypted = file.read()

        c = Cryptography()
        correct_password = False
        while not correct_password:
            if self._master_password is not None:
                try:
                    correct_password = c.validate(file_crypted,
                                                  self._master_password)
                except CorruptedError:
                    print(_("mdp: Error: The file '{filename}' seems to be"
                            "corrupted.").format(filename=self._file_path),
                          file=sys.stderr)
                    sys.exit(1)

            if not correct_password:
                if self._master_password is not None:
                    print(_("Wrong password, try again."))
                self._master_password = getpass(prompt=_("Password: "))

        try:
            file_decrypted = c.decrypt(file_crypted, self._master_password)
        except UnicodeDecodeError as e:
            print(_("mdp: Error: Unable to decrypt the file. {error}")
                  .format(error=e.__str__()),
                  file=sys.stderr)
            sys.exit(1)

        try:
            passwords = Keychain(file_decrypted)
        except ValueError as e:
            print(_("mdp: Error: Unable to parse the file. {error}")
                  .format(error=e.__str__()),
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
