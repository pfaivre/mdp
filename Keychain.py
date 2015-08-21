#!/usr/bin/env python3

import json


class Password:
    """ Represents a password for a couple login/domain
    """
    def __init__(self, domain, login, password):
        self.domain = domain
        self.login = login
        self.password = password

    def __repr__(self):
        return "{0} {1}".format(self.domain, self.login)

    def __str__(self):
        return "{0}\t{1}".format(self.domain, self.login)


class Keychain:
    """ Contains a list of passwords and provide methods to manipulate them
    """

    def __init__(self, json_string=None):
        if json_string is not None:
            self._from_json(json_string)
        else:
            self._passwords = []

    def _from_json(self, json_string: str):
        """ Loads a keychain from a Json string.
        """
        json_passwords = json.loads(json_string)

        # TODO: Add an automatic Json parser
        self._passwords = []
        for p in json_passwords:
            self._passwords.append(Password(p["domain"], p["login"],
                                            p["password"]))

    def to_json(self, reduced=True):
        """ Converts the password list in a Json string.
        :param reduced: Specifies if the string must be reduced
        (no spaces nor new lines) or prettily formatted
        :return: A Json string containing all the information
        """
        json_passwords = json.dumps(obj=self._passwords,
                                    default=lambda o: o.__dict__,
                                    sort_keys=True,
                                    indent=4 if not reduced else None)

        return json_passwords

    def filter(self, pattern=""):
        """ Returns a list of passwords filtered by their domain and login.
        :param pattern: Filter by domain or login.
        :return: A list of passwords matching the filters
        """
        return [p for p in self._passwords
                if pattern in p.domain or pattern in p.login]

    def set(self, domain, login, password, replace=False):
        """ Defines a new password or change an existing one
        :param replace: Replace the password if the entry already exists
        :return: True if the password has been stored
        """
        matching_passwords = [p for p in self._passwords
                              if p.domain == domain and p.login == login]
        nb_matching_passwords = len(matching_passwords)
        already_exists = nb_matching_passwords > 0
        password_saved = False

        if already_exists:
            if replace:
                matching_passwords[0].password = password
                password_saved = True
        else:
            self._passwords.append(Password(domain, login, password))
            password_saved = True

        return password_saved

    def delete(self, password_obj):
        """ Removes the password from the keychain
        :param password_obj: Password object to remove from the list
        :return: True on successful deletion
        """
        success = False

        try:
            self._passwords.remove(password_obj)
            success = True
        except ValueError:
            success = False

        return success

    def __str__(self):
        return "Keychain: {0} passwords".format(len(self._passwords))

