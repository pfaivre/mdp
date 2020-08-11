#!/usr/bin/env python3

#     mdp - Advanced user interface using Urwid
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

# TODO: Add a settings page to change master password, path file, etc.
# TODO: Add a status bar to display messages and shortcuts

from getpass import getpass
import os
from os import path

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

import urwid
try:
    import pyperclip as pyperclip
    # TODO: find a way to detect not compatible terminals such as TTYs.
    pyperclip_available = True
except ImportError:
    print(_("mdp: Warning: The module pyperclip is missing.\n"
            "You will not be able to use the clipboard"))
    pyperclip_available = False
except Exception as e:
    print(_("mdp: Warning: Unable to initialize the pyperclip module: {error}")
          .format(error=e))
    pyperclip_available = False

from Keychain import Keychain, Password
from ui.BaseInterface import BaseInterface


#
# Custom widgets
#

class FrameEvent(urwid.Frame):
    """ Frame with events
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_keypress = None

    def set_on_keypress(self, callback):
        """ Sets the event raised when a key is pressed
        """
        self._on_keypress = callback

    def keypress(self, size, key):
        ret = super().keypress(size, key)

        if self._on_keypress:
            self._on_keypress()

        return ret


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
        self._on_mouse_event = None

    def set_on_search_key(self, callback):
        """ Sets the event raised on the search keys
        """
        self._on_search_key = callback

    def set_on_mouse_event(self, callback):
        """ Sets the event raised on the search keys
        """
        self._on_mouse_event = callback

    def keypress(self, size, key):
        ret = super().keypress(size, key)

        # If the event has not been handled by children
        if ret is not None:
            # TODO: use command_map to link the keys to the action
            if key in ('/', 'tab', 'up') and self._on_search_key:
                self._on_search_key()
                return None

        return key

    def mouse_event(self, size, event, button, col, row, focus):
        """Scroll when rolling the mouse wheel
        """
        ret = super().mouse_event(size, event, button, col, row, focus)

        (maxcol, maxrow) = size

        if "mouse press" == event:
            if 4 == button:
                self._keypress_up((maxcol, maxrow))
            if 5 == button:
                self._keypress_down((maxcol, maxrow))

        if self._on_mouse_event:
            self._on_mouse_event()

        return ret

#
# Main frame
#


class Urwid(BaseInterface):
    """ Nice command line user interface using Urwid.
    """

    def __init__(self, file_path):
        super().__init__(file_path)

        self._auto_exit_alarm = None
        self._loop = None

        if not os.path.isfile(self._file_path):
            print(_("{filename} is not found, it will be created.")
                  .format(filename=self._file_path))
            self._create_pass_file()

        self._passwords = self._load_pass_file()

        # Color scheme for the interface
        self.palette = [
            ('root',          'dark gray',  'default'),
            ('button normal', 'default',    'default',      'standout'),
            ('button select', 'default',    'dark magenta'),
            ('edit normal',   'default',    'default'),
            ('edit focus',    'default',    'dark blue'),
        ]
        self.window = urwid.WidgetPlaceholder(urwid.SolidFill())

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

    def start(self, mode='interactive', domain=None, login=None):

        self.window = self._construct()

        self._loop = urwid.MainLoop(self.window, palette=self.palette,
                                    unhandled_input=self._process_input)

        self._reset_auto_exit_alarm()

        self._loop.run()

    def _construct(self):
        """ Builds the interface
        :return: The main container
        """
        # The header
        self.filter_textbox = EditEvent(_("Filter: "), multiline=False)
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
        def listbox_mouse_event():
            self._reset_auto_exit_alarm()
            self._focus_to_list()
        self.listbox.set_on_mouse_event(listbox_mouse_event)
        self._refresh_list()

        # Whole frame
        self.frame = FrameEvent(header=header,
                                body=self.listbox,
                                focus_part='header')
        self.frame.set_on_keypress(self._reset_auto_exit_alarm)

        # And finally the border around the frame
        linebox = urwid.LineBox(self.frame,
                                title="{0} v{1}".format("mdp", "0.5.0"))
        linebox = urwid.AttrWrap(linebox, 'root')

        return linebox

    def _refresh_list(self):
        """ Updates the password list given the filter textbox
        """
        pattern = self.filter_textbox.edit_text.strip()
        filtered = self._passwords.filter(pattern, True)
        filtered = sorted(filtered)

        # Passwords buttons
        l = []
        for p in filtered:
            b = urwid.Button("{0} - {1}".format(p.domain, p.login),
                             on_press=self._open_password_menu,
                             user_data={'password': p})
            b = urwid.AttrWrap(b, 'button normal', 'button select')
            l.append(b)

        # New password button at the end
        b = urwid.Button(_("[+] New entry"),
                         on_press=self._open_edit_password_dialog,
                         user_data={'password': Password()})
        b = urwid.AttrWrap(b, 'button normal', 'button select')
        l.append(b)

        self.listbox.body = urwid.SimpleListWalker(l)

    def _open_password_menu(self, button, user_data):
        """ Opens the menu for a password
        """
        p = user_data['password']

        def dismiss(button=None):
            self.window.original_widget = self.window.original_widget.bottom_w

        def delete_password(button=None):
            # TODO: Add a confirmation dialog box
            self._delete_password(p)
            dismiss()

        def edit_password(button, user_data):
            dismiss()
            self._open_edit_password_dialog(button, user_data)

        body = [urwid.Text(p.domain + " - " + p.login, align='center'),
                urwid.Divider('\u2500')]
        if pyperclip_available:
            body.extend([
                self._new_button(_("Copy the password in the clipboard"),
                                 on_press=lambda b: pyperclip.copy(p.password)),
                self._new_button(_("Copy the domain in the clipboard"),
                                 on_press=lambda b: pyperclip.copy(p.domain)),
                self._new_button(_("Copy the login in the clipboard"),
                                 on_press=lambda b: pyperclip.copy(p.login))
            ])
        body.extend([
            self._new_button(_("Edit this entry"),
                             on_press=edit_password,
                             user_data={'password': p,
                                        'replace': True}),
            self._new_button(_("Delete this entry"),
                             on_press=delete_password),
            #. TRANSLATORS: Back to the previous view.
            self._new_button(_("Return"), on_press=dismiss)
        ])

        menu = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(body)))

        self.window.original_widget = urwid.Overlay(
            menu,
            self.window.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=2, right=2,
            top=2, bottom=2)

    def _open_edit_password_dialog(self, button, user_data):
        """ Opens a dialog to edit or add a password
        """
        p_obj = user_data['password'] if 'password' \
                                         in user_data else Password()
        d = self._new_edit(_("Domain: "), edit_text=p_obj.domain)
        l = self._new_edit(_("Login: "), edit_text=p_obj.login)
        p = self._new_edit(_("Password: "), edit_text=p_obj.password)
        replace = user_data['replace'] if 'replace' in user_data else False

        def dismiss(button=None):
            self.window.original_widget = self.window.original_widget.bottom_w

        def save_entry(button):
            if d.edit_text != "" or l.edit_text != "":
                if replace:
                    self._passwords.delete(p_obj)
                self._passwords.set(d.edit_text.strip(), l.edit_text.strip(),
                                    p.edit_text.strip(), replace)
                self._save_pass_file(self._passwords)
                self._refresh_list()
                dismiss()

        #. TRANSLATORS: Title of the password menu.
        body = [urwid.Text(_("Password"), align='center'),
                urwid.Divider('\u2500'),
                d,
                l,
                p,
                self._new_button(_("Save"), on_press=save_entry),
                self._new_button(_("Cancel"), on_press=dismiss)]

        menu = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(body)))
        self.window.original_widget = urwid.Overlay(
            menu,
            self.window.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=2, right=2,
            top=2, bottom=2)

    def _delete_password(self, password):
        """ Deletes a password from the keychain and return True on success.
        :param password: Password object to delete
        :type password: Password
        :rtype : bool
        """
        success = self._passwords.delete(password)
        if success:
            self._save_pass_file(self._passwords)
            self._refresh_list()
        return success

    def _new_button(self, *args, **kwargs):
        """ Returns an urwid.Button wrapped with 'button normal' and
        'button select' attributes.
        It takes the same parameters as the Button class.
        """
        b = urwid.Button(*args, **kwargs)
        b = urwid.AttrWrap(b, 'button normal', 'button select')
        return b

    def _new_edit(self, *args, **kwargs):
        """ Returns an urwid.Edit wrapped with 'edit normal' and
        'button focus' attributes.
        It takes the same parameters as the Edit class.
        """
        e = urwid.Edit(*args, **kwargs)
        e = urwid.AttrWrap(e, 'edit normal', 'edit focus')
        return e

    def _focus_to_list(self):
        """ Gives the focus to the list if it is not empty
        """
        if len(self.listbox.body) > 0:
            self.frame.focus_position = 'body'

    def _focus_to_filter_textbox(self):
        """ Gives the focus to the filter textbox
        """
        self.frame.focus_position = 'header'

    def _exit_application(self, *args):
        raise urwid.ExitMainLoop()

    def _reset_auto_exit_alarm(self):
        self._loop.remove_alarm(self._auto_exit_alarm)
        
        # Automatically close the application 5 minutes from now
        self._auto_exit_alarm = self._loop.set_alarm_in(
            300,
            self._exit_application)

    def _process_input(self, key):
        if key in ('q', 'Q', 'esc', 'f10'):
            self._exit_application()
