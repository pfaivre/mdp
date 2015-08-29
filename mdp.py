#!/usr/bin/env python3

#     mdp - User friendly password storage tool
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

__title__ = "mdp"
__copyright__ = "Copyright (C) 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPLv3+"
__version__ = "0.4.0"
__date__ = "2015-08-30"
__maintainer__ = "Pierre Faivre"
__status__ = "Development"

import errno
import os
from os import path
from os.path import expanduser
import sys

# l10n configuration
# To generate POT file:
# $ xgettext --language=Python --keyword=_ --add-comments="." --output=./locale/mdp.pot *.py ui/*.py
import locale
import gettext
# ./../locale
locale_dir = path.join(path.dirname(path.realpath(__file__)), 'locale')
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

try:
    # Using Urwid as default interface
    from ui.Urwid import Urwid as User_interface
except ImportError:
    # Using Cli as a fallback interface if urwid is unavailable
    from ui.Cli import Cli as User_interface

DEFAULT_OUTPUT_DIR = expanduser("~")


def print_version():
    print("{0} {1}".format(__title__, __version__))
    print("{0}".format(__copyright__))
    print()
    print(_("This program comes with ABSOLUTELY NO WARRANTY."))
    print(_("This is free software, and you are welcome to redistribute it\n"
            "under certain conditions; "
            "see the LICENCE file for more information."))


def print_help():
    print("{0} {1} {2}".format(__title__, __version__, __copyright__))
    print(_("This program can store your passwords on an encrypted file and"
          "\nallows you to access it in a very simple way."))
    print()
    print(_("This program is fully interactive. "
          "You can also use one of these commands:"))
    print(_("\t-h, --help\n\t\tShows this help and exits"))
    print(_("\t-v, --version\n\t\tShows version information and exits"))
    print()
    print(_("mdp depends on these third party libraries:"))
    print(_(" - Pyperclip, by Al Sweigart"))
    print(_(" - Urwid, Copyright (C) 2004-2012 Ian Ward"))
    print(_(" - pycrypto, by Dwayne Litzenberger"))
    print(_("Make sure to have them installed on your system in order to"
            "access all the\nfeatures."))


def main(argv):
    mode = ''

    # Checking arguments
    if len(argv) == 0:
        mode = 'interactive'
    elif argv[0] in ('-v', '--version'):
        print_version()
        sys.exit(0)
    elif argv[0] in ('-h', '--help'):
        print_help()
        sys.exit(0)
    else:
        print(_("mdp: error: unrecognized argument: {0}").format(argv[0]),
              file=sys.stderr)
        sys.exit(errno.EINVAL)

    # TODO: Let the user configure the password file
    # Getting pass file
    pass_file_path = os.path.join(DEFAULT_OUTPUT_DIR, 'pass.txt')

    # Starting user interface
    try:
        ui_obj = User_interface(pass_file_path)
        ui_obj.start()
    except OSError:
        print()
        print(_("Failing to use the advanced interface. "
              "Switching back to the classic one."), file=sys.stderr)
        from ui.Cli import Cli as Fallback_user_interface
        ui_obj = Fallback_user_interface(pass_file_path)
        ui_obj.start()


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("")
    except EOFError:
        print("")
    except NotImplementedError as e:
        print(_("Sorry the functionality '{0}' has not been implemented yet.")
              .format(e), file=sys.stderr)
