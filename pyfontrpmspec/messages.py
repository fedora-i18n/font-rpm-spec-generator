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

import sys
from termcolor import colored

class Message:

    def __init__(self, joiner = [' ']):
        self._message = None
        self.__joiner = joiner
        self.__njoiner = 0

    def __add_joiner(self):
        if self._message is None:
            self._message = ''
        elif isinstance(self.__joiner, list):
            self._message += self.__joiner[self.__njoiner]
            self.__njoiner = min(self.__njoiner + 1, len(self.__joiner)-1)

    def error(self, msg):
        self.__add_joiner()
        self._message += colored(str(msg), 'red')
        return self

    def warning(self, msg):
        self.__add_joiner()
        self._message += colored(str(msg), 'yellow')
        return self

    def info(self, msg):
        self.__add_joiner()
        self._message += colored(str(msg), 'green')
        return self

    def ignored(self):
        self.__add_joiner()
        self._message += colored('(ignored)', 'white')
        return self

    def message(self, msg):
        self.__add_joiner()
        self._message += str(msg)
        return self

    def out(self):
        print(self._message, flush=True, file=sys.stderr)

    def __str__(self):
        return self._message

if __name__ == '__main__':
    Message([': ', ' ']).info('foo').warning('duplicate').out()
