#!/usr/bin/env python3


class Password:
    """ Represents a password for a couple login/domain
    """
    def __init__(self, domain, login, password):
        self.domain = domain
        self.login = login
        self.password = password
        self.visible = True

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
        raise NotImplementedError("Keychain.from_json")

    def to_json(self, reduced=True):
        """ Converts the password list in a Json string.
        :param reduced: Specifies if the string must be reduced
        (no spaces nor new lines) or prettily formatted
        :return: A Json string containing all the information
        """
        raise NotImplementedError("Keychain.to_json")

    def filter(self, domain="", login=""):
        """ Selects passwords by their domain and login.
        It doesn't affect the password list, it will just hide the unselected
        passwords in the enumerate method.
        :param domain: Filter by domain. Wildcards '?' and '*' are accepted
        :param login: Filter by login. Wildcards '?' and '*' are accepted
        :return:
        """
        raise NotImplementedError("Keychain.filter")

    def get_filtered(self):
        """ Gives the passwords that have been highlighted by the filter method
        :return: A list of Password objects
        """
        raise NotImplementedError("Keychain.get_filtered")

    def set(self, domain, login, password, replace=False):
        """ Defines a new password
        :param replace: Replace the password if the entry already exists
        """
        raise NotImplementedError("Keychain.set")

    def delete(self, password_obj):
        """ Remove the password from the keychain
        :param password_obj: Password object to delete
        """
        raise NotImplementedError("Keychain.delete")

    def __str__(self):
        return "Keychain: {0} passwords".format(len(self._passwords))

