# messages.py
# Copyright (C) 2022 Red Hat, Inc.
#
# Authors:
#   Akira TAGOH  <tagoh@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Module to deal with messages."""

import sys
from termcolor import colored
from typing import Self


class Message:
    """Colorize message text in a structured way."""

    def __init__(self, joiner: list[str] = [' ']):
        """Initialize Message class."""
        self._message = None
        self.__joiner = joiner
        self.__njoiner = 0

    def __add_joiner(self):
        if self._message is None:
            self._message = ''
        elif isinstance(self.__joiner, list):
            self._message += self.__joiner[self.__njoiner]
            self.__njoiner = min(self.__njoiner + 1, len(self.__joiner) - 1)

    def error(self, msg: str) -> Self:
        """Output `msg` as an error."""
        self.__add_joiner()
        self._message += colored(str(msg), 'red')
        return self

    def warning(self, msg: str) -> Self:
        """Output `msg` as a warning."""
        self.__add_joiner()
        self._message += colored(str(msg), 'yellow')
        return self

    def info(self, msg: str) -> Self:
        """Output `msg` as an information."""
        self.__add_joiner()
        self._message += colored(str(msg), 'green')
        return self

    def ignored(self) -> Self:
        """Mark this as ignored."""
        self.__add_joiner()
        self._message += colored('(ignored)', 'white')
        return self

    def message(self, msg: str) -> Self:
        """Output `msg` as a message."""
        self.__add_joiner()
        self._message += str(msg)
        return self

    def out(self) -> None:
        """Output all the strings held in this object into stderr."""
        print(self._message, flush=True, file=sys.stderr)

    def __str__(self) -> str:
        """Convert messages to str."""
        return self._message


if __name__ == '__main__':
    Message([': ', ' ']).info('foo').warning('duplicate').out()
