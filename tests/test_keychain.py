import json
from unittest import TestCase

from Keychain import Keychain, Password


class TestKeychain(TestCase):

    def setUp(self):
        # A dataset for the tests
        json_string = """[
    {
        "domain": "superwebsite.com",
        "login": "my_account_login",
        "password": "password1"
    },
    {
        "domain": "google.com",
        "login": "my_mail@gmail.com",
        "password": "password2"
    },
    {
        "domain": "Wifi Password",
        "login": "",
        "password": "*7@._:#Er#j{r/\\\\J"
    },
    {
        "domain": "mail.yahoo.com",
        "login": "my_mail@yahoo.com",
        "password": "password3"
    },
    {
        "domain": "House alarm",
        "login": "",
        "password": "1234"
    }
]"""
        self.keychain = Keychain(json_string)

    def test__from_json(self):
        self.assertEqual(len(self.keychain._passwords), 5,
                         "Wrong number of passwords in the keychain")
        self.assertEqual(self.keychain._passwords[0].domain, "superwebsite.com",
                         "The first password should have 'superwebsite.com' as "
                         "domain")
        self.assertEqual(self.keychain._passwords[0].login, "my_account_login",
                         "The first password should have 'my_account_login' as "
                         "login")
        self.assertEqual(self.keychain._passwords[0].password, "password1",
                         "The first password should have 'password1' as "
                         "password")

    def test_to_json(self):
        json_string = self.keychain.to_json()

        json_valid = True
        try:
            json.loads(json_string)
        except ValueError:
            json_valid = False
        self.assertTrue(json_valid,
                        "'to_json()' should return a valid json string.")

        new_keychain = Keychain(json_string)
        self.assertEqual(len(new_keychain._passwords), 5,
                         "We should get back all the 5 passwords from the "
                         "exported json string.")

    def test_filter(self):
        self.assertEqual(len(self.keychain.filter("", "")), 5,
                         "Before filtering, the method 'filter()' "
                         "should return all the 5 passwords.")

        self.assertEqual(len(self.keychain.filter("", "my_mail")), 2,
                         "Only 2 passwords which login contains 'my_mail'.")

    def test_set(self):
        new_password = "different_password\/-.*"

        self.keychain.set("Wifi Password", "", new_password)
        wifi_password = list(filter(lambda p: p.domain == "Wifi Password",
                                    self.keychain._passwords))[0]
        self.assertNotEqual(wifi_password.password, new_password,
                            "Trying to override an existing password without "
                            "the parameter 'replace=True' shouldn't change it.")

        self.keychain.set("Wifi Password", "", new_password, replace=True)
        wifi_password = list(filter(lambda p: p.domain == "Wifi Password",
                                    self.keychain._passwords))[0]
        self.assertEqual(wifi_password.password, new_password,
                         "Trying to override an existing password with "
                         "the parameter 'replace=True' should change it.")

        self.keychain.set("New domain", "New login", new_password)
        new_entry = list(filter(lambda p: p.domain == "New domain",
                                self.keychain._passwords))[0]
        self.assertEqual(new_entry.password, new_password,
                         "Non existing password for the couple domain/login "
                         "should create a new password.")

    def test_delete(self):
        success = self.keychain.delete(Password("a", "a", "a"))
        self.assertFalse(success, "delete() should return False on an "
                                  "unsuccessful deletion.")

        success = self.keychain.delete(self.keychain._passwords[1])
        self.assertEqual(len(self.keychain._passwords), 4,
                         "There should be 4 passwords left after deleting one "
                         "of them.")
        self.assertTrue(success, "delete() should return True on a successful "
                                 "deletion.")
