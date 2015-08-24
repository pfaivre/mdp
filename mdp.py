#!/usr/bin/env python3

__title__ = "mdp"
__copyright__ = "Copyright 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPL"
__version__ = "0.4.0"
__date__ = "2015-08-24"
__maintainer__ = "Pierre Faivre"
__status__ = "Development"

import errno
import os
from os.path import expanduser
import sys

try:
    # Using Curses as default interface
    from ui.Urwid import Urwid as User_interface
except ImportError:
    # Using Cli as a fallback interface if urwid is unavailable
    from ui.Cli import Cli as User_interface

DEFAULT_OUTPUT_DIR = expanduser("~")


def print_version():
    print("{0} {1} {2}".format(__title__, __version__, __copyright__))


def print_help():
    print_version()
    print("usage:\nmdp")


def main(argv):
    mode = ""
    domain = None
    login = None

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
