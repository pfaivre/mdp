#!/usr/bin/env python3

import urwid
from getpass import getpass
import os

from Keychain import Keychain
from ui.BaseInterface import BaseInterface


class EditEvent(urwid.Edit):
    """ Edit widget with events
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_text_edit = None
        self._on_enter = None

    def set_on_text_edit(self, callback):
        """ Sets the event raised when the text is changed
        """
        self._on_text_edit = callback

    def set_on_enter(self, callback):
        """ Sets the event raised on the Return key
        """
        self._on_enter = callback

    def keypress(self, size, key):
        super().keypress(size, key)

        if key in ('enter', 'down') and self._on_enter:
            self._on_enter()

        if self._on_text_edit:
            self._on_text_edit()


class Urwid(BaseInterface):
    """ Nice command line user interface using Urwid.
    """

    def __init__(self, file_path):
        super().__init__(file_path)

        if not os.path.isfile(self._file_path):
            print("{0} is not found, it will be created."
                  .format(self._file_path))
            self._create_pass_file()

        self._passwords = self._load_pass_file()

        self.palette = palette = [
        ('root',          'default', 'default'),
        ('edit',          'default', 'default')
        ]

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

    def start(self, mode="interactive", domain=None, login=None):

        frame = self._construct()

        loop = urwid.MainLoop(frame, palette=self.palette,
                              unhandled_input=self._process_input)
        loop.run()

    def _construct(self):
        """ Builds the interface
        :return: The main container
        """
        self.filter_textbox = EditEvent("Filter: ", multiline=False)
        self.filter_textbox.set_on_text_edit(self._refresh_list)
        self.filter_textbox.set_on_enter(self._focus_to_list)
        self.filter_textbox = urwid.AttrWrap(self.filter_textbox, 'edit')
        hline = urwid.BoxAdapter(urwid.SolidFill('\u2500'), 1)
        header = urwid.Pile((('weight', 1, self.filter_textbox),
                            ('weight', 1, hline)))

        self.listbox = urwid.ListBox(())
        self._refresh_list()

        self.frame = urwid.Frame(header=header,
                                 body=self.listbox,
                                 focus_part='header')

        linebox = urwid.LineBox(self.frame, title="{0} v{1}".format("mdp", "0.4.0"))
        linebox = urwid.AttrWrap(linebox, 'root')

        return linebox

    def _refresh_list(self):
        """ Updates the password list given the filter textbox
        """
        filtered = self._passwords.filter(self.filter_textbox.edit_text)
        l = []
        for p in filtered:
            l.append(urwid.Button("{0} - {1}".format(p.domain, p.login)))

        self.listbox.body = urwid.SimpleListWalker(l)

    def _focus_to_list(self):
        """ Gives the focus to the list if it is not empty
        """
        if len(self.listbox.body) > 0:
            self.frame.focus_position = 'body'

    def _process_input(self, key):
        if key in ('q', 'Q', 'esc', 'f10'):
            raise urwid.ExitMainLoop()
