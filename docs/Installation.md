Getting started
===============

## Installation

mdp has been tested on Windows 7, Linux Mint 17.2 and Fedora 22, but it should 
works as well on other platforms.

It depends on:
* **Python 3**
* [**Pyperclip**](https://pypi.python.org/pypi/pyperclip/1.5.11)
* [**pycrypto**](https://www.dlitz.net/software/pycrypto/)
* [**Colorama**](https://pypi.python.org/pypi/colorama) (Optional)
* [**Urwid**](http://urwid.org/) (Optional, not on Windows)

### Windows
* **Python 3**. Download and install official installer [here](https://www.python.org/downloads/).
* **pycrypto**. You can download binaries for Python 3.4 [here](https://github.com/axper/python3-pycrypto-windows-installer).
* **Pyperclip** and **Colorama**. Open a Command window and type `pip3 install pyperclip colorama`

### Debian and derivative
These commands will install everything you need:
```bash
$ sudo pip3 install pyperclip
$ sudo apt-get install python3-urwid xclip
```
**Python 3**, **pycrypto** and **colorama** are already shipped with the system.

### Fedora
These commands will install everything you need:
```bash
$ sudo pip3 install pyperclip
$ sudo dnf install python3-crypto python3-urwid xclip
```
**Python 3** is already shipped with the system.

## Usage

Just extract and execute `mdp.py` on a terminal.

