#!/usr/bin/env python3

#     mdp - Unit tests for the Cryptography module
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

from unittest import TestCase

from Cryptography import Cryptography


class TestCryptography(TestCase):

    def setUp(self):
        self.c = Cryptography()
        self.msg = "My dirty secret message."
        self.key = "key1234"

    def test_validate(self):
        encrypted = self.c.encrypt(self.msg, self.key)

        self.assertTrue(self.c.validate(encrypted, self.key),
                        "Validation of a correct key.")
        self.assertFalse(self.c.validate(encrypted, "wrong_key"),
                         "Validation of an incorrect key.")

    def test_encrypt(self):
        encrypted = self.c.encrypt(self.msg, self.key)

        self.assertNotEqual(self.msg, encrypted,
                            "The encrypted message should be different than "
                            "the original.")
        self.assertEqual(self.msg, self.c.decrypt(encrypted, self.key),
                         "We should get the original message after decryption.")

    def test_decrypt(self):
        encrypted = self.c.encrypt(self.msg, self.key)

        self.assertEqual(self.msg, self.c.decrypt(encrypted, self.key),
                         "The message should stay the same after encryption "
                         "and decryption.")
