#!/usr/bin/env python3

import urwid
from getpass import getpass
import os
import sys

try:
    import pyperclip as pyperclip
except ImportError:
    # TODO: Make the pyperclip missing error non blocking
    print("mdp: Error: The module pyperclip is missing", file=sys.stderr)
    sys.exit(1)

from Keychain import Keychain
from ui.BaseInterface import BaseInterface


#
# Custom widgets
#


class EditEvent(urwid.Edit):
    """ Edit widget with events
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_text_edit = None
        self._on_validation = None
        self._on_exit = None

    def set_on_text_edit(self, callback):
        """ Sets the event raised when the text is changed
        """
        self._on_text_edit = callback

    def set_on_validation(self, callback):
        """ Sets the event raised on the Validation keys
        """
        self._on_validation = callback

    def set_on_exit(self, callback):
        """ Sets the event raised on the Exit keys
        """
        self._on_exit = callback

    def keypress(self, size, key):
        ret = super().keypress(size, key)

        if key in ('enter', 'down', 'tab') and self._on_validation:
            self._on_validation()
            return None
        elif key in ('esc', 'f10') and self._on_exit:
            self._on_exit()
            return None
        elif self._on_text_edit:
            self._on_text_edit()


class ListBoxEvent(urwid.ListBox):
    """ Listbox widget with events
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_search_key = None

    def set_on_search_key(self, callback):
        """ Sets the event raised on the search keys
        """
        self._on_search_key = callback

    def keypress(self, size, key):
        ret = super().keypress(size, key)

        # If the event has not been handled by children
        if ret is not None:
            # TODO: use command_map to link the keys to the action
            if key in ('/', 'tab', 'up') and self._on_search_key:
                self._on_search_key()
                return None

        return key


class PasswordMenuDialog(urwid.WidgetWrap):
    """ A dialog that appears with nothing but a close button
    """
    signals = ['close']

    def __init__(self):
        l = []
        l.append(urwid.Button("Copy the domain in the clipboard"))
        l.append(urwid.Button("Copy the login in the clipboard"))
        l.append(urwid.Button("Copy the password in the clipboard"))
        close_button = urwid.Button("Close")
        urwid.connect_signal(close_button, 'click',
                             lambda button: self._emit("close"))
        l.append(close_button)
        listbox = urwid.ListBox(urwid.SimpleListWalker(l))

        fill = urwid.Filler(listbox)
        super().__init__(urwid.AttrWrap(fill, 'popup menu'))


#
# Main frame
#


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

        # Color scheme for the interface
        self.palette = palette = [
            ('root',          'default',    'default'),
            ('edit',          'default',    'default'),
            ('button normal', 'default',    'default',      'standout'),
            ('button select', 'default',    'dark magenta'),
            ('popup menu',    'default',    'default')
        ]

        self.window = urwid.WidgetPlaceholder(urwid.SolidFill())

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

        self.window = self._construct()

        loop = urwid.MainLoop(self.window, palette=self.palette,
                              unhandled_input=self._process_input)
        loop.run()

    def _construct(self):
        """ Builds the interface
        :return: The main container
        """
        # The header
        self.filter_textbox = EditEvent("Filter: ", multiline=False)
        self.filter_textbox.set_on_text_edit(self._refresh_list)
        self.filter_textbox.set_on_validation(self._focus_to_list)
        self.filter_textbox.set_on_exit(self._exit_application)
        self.filter_textbox = urwid.AttrWrap(self.filter_textbox, 'edit')
        hline = urwid.Divider('\u2500')
        header = urwid.Pile((('weight', 1, self.filter_textbox),
                             ('weight', 1, hline)))

        # The body
        self.listbox = ListBoxEvent(())
        self.listbox.set_on_search_key(self._focus_to_filter_textbox)
        self._refresh_list()

        # Whole frame
        self.frame = urwid.Frame(header=header,
                                 body=self.listbox,
                                 focus_part='header')

        # And finally the border around the frame
        linebox = urwid.LineBox(self.frame,
                                title="{0} v{1}".format("mdp", "0.4.0"))
        linebox = urwid.AttrWrap(linebox, 'root')

        return linebox

    def _refresh_list(self):
        """ Updates the password list given the filter textbox
        """
        # Passwords buttons
        filtered = self._passwords.filter(self.filter_textbox.edit_text)
        l = []
        for p in filtered:
            b = urwid.Button("{0} - {1}".format(p.domain, p.login),
                             on_press=self._select_password)
            b.user_data = {"password": p}
            b = urwid.AttrWrap(b, 'button normal', 'button select')
            l.append(b)

        # New password button at the end
        b = urwid.Button("[+] New entry",
                         on_press=self._open_edit_password_dialog,
                         user_data={"domain": "", "login": "", "password": ""})
        b = urwid.AttrWrap(b, 'button normal', 'button select')
        l.append(b)

        self.listbox.body = urwid.SimpleListWalker(l)

    def _open_menu(self, title, choices):
        """
        :param title: Title to show at the top
        :type title: str
        :param choices: List of urwid.Buttons
        :type choices: list
        """

        def dismiss(button=None):
            self.window.original_widget = self.window.original_widget.bottom_w

        body = [urwid.Text(title, align='center'), urwid.Divider('\u2500')]
        body.extend(choices)
        body.append(urwid.Button("Return", on_press=dismiss))
        menu = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(body)))
        self.window.original_widget = urwid.Overlay(
            menu,
            self.window.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=2,
            right=2,
            top=2,
            bottom=2)

    def _open_edit_password_dialog(self, button, user_data):
        """ Opens a dialog to edit or add a password
        """
        d = urwid.Edit("Domain: ", edit_text=user_data["domain"])
        l = urwid.Edit("Login: ")
        p = urwid.Edit("Password: ")

        def dismiss(button=None):
            self.window.original_widget = self.window.original_widget.bottom_w

        def save_entry(button):
            self._passwords.set(d.edit_text, l.edit_text, p.edit_text)
            self._refresh_list()
            dismiss()

        body = [urwid.Text("Password", align='center'),
                urwid.Divider('\u2500'),
                d,
                l,
                p,
                urwid.Button("Ok", on_press=save_entry),
                urwid.Button("Cancel", on_press=dismiss)]

        menu = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(body)))
        self.window.original_widget = urwid.Overlay(
            menu,
            self.window.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=2,
            right=2,
            top=2,
            bottom=2)

    def _select_password(self, button):
        p = button.user_data["password"]
        self._open_menu(
            repr(p),
            [urwid.Button("Copy the password in the clipboard",
                          on_press=lambda b: pyperclip.copy(p.password)),
             urwid.Button("Copy the domain in the clipboard",
                          on_press=lambda b: pyperclip.copy(p.domain)),
             urwid.Button("Copy the login in the clipboard",
                          on_press=lambda b: pyperclip.copy(p.login)),
             urwid.Button("Edit this entry"),
             urwid.Button("Delete this entry")])

    def _focus_to_list(self):
        """ Gives the focus to the list if it is not empty
        """
        if len(self.listbox.body) > 0:
            self.frame.focus_position = 'body'

    def _focus_to_filter_textbox(self):
        """ Gives the focus to the filter textbox
        """
        self.frame.focus_position = 'header'

    def _exit_application(self):
        raise urwid.ExitMainLoop()

    def _process_input(self, key):
        if key in ('q', 'Q', 'esc', 'f10'):
            self._exit_application()
