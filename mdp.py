#!/usr/bin/env python3

__title__ = "mdp"
__copyright__ = "Copyright 2015, Pierre Faivre"
__credits__ = ["Pierre Faivre"]
__license__ = "GPL"
__version__ = "0.3.0"
__date__ = "2015-08-13"
__maintainer__ = "Pierre Faivre"
__status__ = "Development"

import errno
import os
from os.path import expanduser
import sys

from Cli import Cli

DEFAULT_OUTPUT_DIR = expanduser("~")


def print_version():
    print("{0} {1} {2}".format(__title__, __version__, __copyright__))


def print_help():
    print("{0} {1} {2}".format(__title__, __version__, __copyright__))
    print("usage:\nmdp [get|set|del] [domain] [login]")


def main(argv: list):
    mode = ""
    domain = None
    login = None

    # Checking arguments
    if len(argv) == 0:
        mode = "interactive"
    elif argv[0] in ("get", "set", "del"):
        mode = argv[0]
        # Getting optional arguments domain and login
        if len(argv) > 1:
            domain = argv[1]
        if len(argv) > 2:
            login = argv[2]
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
    cli = Cli(pass_file_path)
    cli.start(mode, domain, login)


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
