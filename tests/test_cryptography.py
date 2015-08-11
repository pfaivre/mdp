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
