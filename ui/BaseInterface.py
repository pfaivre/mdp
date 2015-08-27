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
import sys

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
