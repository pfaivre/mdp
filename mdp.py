#!/usr/bin/env python3

__title__ = "mdp"
__copyright__ = "Copyright (C) 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPLv3+"
__version__ = "0.4.0"
__date__ = "2015-08-27"
__maintainer__ = "Pierre Faivre"
__status__ = "Development"

import errno
import os
from os.path import expanduser
import sys

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
    print("This program comes with ABSOLUTELY NO WARRANTY.")
    print("This is free software, and you are welcome to redistribute it"
          "{new_line}under certain conditions; "
          "see the LICENCE file for more information."
          .format(new_line=os.linesep))


def print_help():
    print("{0} {1} {2}".format(__title__, __version__, __copyright__))
    print("This program can store your passwords on a crypted file and"
          "\nallows you to access it in a very simple way.")
    print()
    print("This program is fully interactive. "
          "You can also use one of these commands:")
    print("\t-h, --help\n\t\tShows this help and exits")
    print("\t-v, --version\n\t\tShows version information and exits")
    print()
    print("mdp depends on these third party libraries:")
    print(" - Pyperclip, by Al Sweigart")
    print(" - Urwid, Copyright (C) 2004-2012 Ian Ward")
    print(" - pycrypto, by Dwayne Litzenberger")
    print("Make sure to have them installed on your system in order to access "
          "all the\nfeatures.")


def main(argv):
    mode = ""

    # Checking arguments
    if len(argv) == 0:
        mode = "interactive"
    elif argv[0] in ("-v", "--version"):
        print_version()
        sys.exit(0)
    elif argv[0] in ("-h", "--help"):
        print_help()
        sys.exit(0)
    else:
        print("mdp: error: unrecognized argument: {0}".format(argv[0]),
              file=sys.stderr)
        sys.exit(errno.EINVAL)

    # TODO: Let the user configure the password file
    # Getting pass file
    pass_file_path = os.path.join(DEFAULT_OUTPUT_DIR, "pass.txt")

    # Starting user interface
    try:
        ui_obj = User_interface(pass_file_path)
        ui_obj.start()
    except OSError:
        print()
        print("Failing to use the advanced interface. "
              "Switching back to the classic one.", file=sys.stderr)
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
        print("Sorry the functionality '{0}' has not been implemented yet."
              .format(e), file=sys.stderr)
