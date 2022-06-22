# sources.py
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

import os
import re
import shutil
import sys
import tempfile
from lxml import etree
from pathlib import Path

class Sources:

    def __init__(self, arrays = None, sourcedir = None):
        self._sources = []
        self.__sourcedir = sourcedir
        if arrays is not None:
            for e in arrays:
                self.add(str(Path(e).name))

    def add(self, fn):
        self._sources.append(Source(fn, sourcedir = self.__sourcedir))
        return len(self._sources)-1

    def get(self, idx):
        return self._sources[idx]

    @property
    def length(self):
        return len(self._sources)

    def __iter__(self):
        yield from self._sources

class Source:

    def __init__(self, fn, sourcedir = None):
        self.__sourcedir = sourcedir
        self._sourcename = fn
        self._tempdir = None
        self._root = None
        self._is_archive = False

    def __del__(self):
        if self._tempdir is not None:
            self._tempdir.cleanup()

    def __iter__(self):
        self._tempdir = tempfile.TemporaryDirectory()
        try:
            shutil.unpack_archive(self.realname, self._tempdir.name)
            self._is_archive = True
            for root, dirs, files in os.walk(self._tempdir.name):
                self._root = str(Path(*Path(root).relative_to(self._tempdir.name).parts[:1]))
                for n in files:
                    fn = str(Path(root).relative_to(self._tempdir.name) / n)
                    print(fn)
                    yield File(fn, self._tempdir.name)
        except shutil.ReadError:
            yield File(self.name, self.__sourcedir)
        else:
            if self._tempdir is not None:
                self._tempdir.cleanup()
                self._tempdir = None

    @property
    def name(self):
        return self._sourcename

    @property
    def realname(self):
        return str(Path(self.__sourcedir) / self._sourcename)

    @property
    def root(self):
        return self._root

    def is_archive(self):
        return self._is_archive

class File:

    def __init__(self, fn, prefixdir):
        self._filename = fn
        self._prefixdir = prefixdir
        self.__family = None

    @property
    def name(self):
        p = Path(self._filename)
        d = p.parent
        n = p.name
        print(d,n,d.parts[1:])
        if not d.parts[1:]:
            if d == '.':
                return str(d / n)
            else:
                return n
        else:
            return str(d.relative_to(*d.parts[:1]) / n)

    @property
    def realname(self):
        return self._filename

    @property
    def fullname(self):
        return str(Path(self.prefix) / self.realname)

    @property
    def prefix(self):
        return self._prefixdir

    @property
    def family(self):
        if self.is_fontconfig():
            if self.__family is None:
                tree = etree.parse(self.fullname)
                family = tree.xpath('/fontconfig/alias/family/text()')
                if not family:
                    family = tree.xpath('/fontconfig/match/edit[@name=\'family\']/string/text()')
                    if not family:
                        raise ValueError('Unable to guess the targeted family name')
                family = list(set(family))
                if len(family) > 1:
                    print('Detected multiple family names: {}'.format(family), flush=True, file=sys.stderr)
                self.__family = family[0]
                return self.__family
            else:
                return self.__family
        else:
            return None

    def is_license(self):
        LICENSES = [ 'OFL', 'MIT', 'GPL' ]
        if re.search(r'(?i:license)', self.name) or re.search(re.compile('|'.join(LICENSES)), self.name):
            return True
        else:
            return False

    def is_doc(self):
        if re.search(r'(?i:readme)', self.name):
            return True
        elif self.name.endswith('.txt'):
            return True
        else:
            return False

    def is_font(self):
        if self.name.endswith('.otf') or self.name.endswith('.ttf') or self.name.endswith('.ttc'):
            return True
        else:
            return False

    def is_fontconfig(self):
        if re.search(r'(?i:fontconfig)', self.name) or self.name.endswith('.conf'):
            return True
        else:
            return False

if __name__ == '__main__':
    s = Source('./foo.zip')
    for x in s:
        print(s.root, x.prefix, x.name, x.is_license())
    s = Source('./requirements.txt')
    for x in s:
        print(x.prefix, x.name, x.is_doc())
    s = Source('./foo.conf')
    for x in s:
        print(x.family)
