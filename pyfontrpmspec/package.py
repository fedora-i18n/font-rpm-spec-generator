# package.py
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
"""Module to deal with packages."""

import re
import shutil
import subprocess
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
from pyfontrpmspec.messages import Message as m
from pyrpm.spec import Spec


class Package:
    """Package related class."""

    @staticmethod
    def source_name(src: str) -> str:
        """Get a Source package name for RPM spec file."""
        if src.endswith('.spec'):
            if not shutil.which('rpmspec'):
                raise AttributeError(m().error('rpmspec is not installed'))
            ss = subprocess.run(['rpmspec', '-P', src], stdout=subprocess.PIPE)
            spec = Spec.from_string(ss.stdout.decode('utf-8'))
            return spec.name
        else:
            raise AttributeError(
                m().error('Unsupported filetype:').message(src))

    @staticmethod
    def build_package_name(foundry: str, family: str) -> str:
        """Build a package name for foundry and family."""
        return str(
            FamilyString(foundry + ' ' + re.sub(r'^{}'.format(
                foundry), '', family)).normalize()) + '-fonts'

    @staticmethod
    def is_targeted_package(pkg: str, foundry: str, family: str) -> bool:
        """Check `pkg` is a package name for `foundry` and `family`."""
        return pkg == Package.build_package_name(foundry, family)


class FamilyString:
    """Wrapper class to deal with a string of font family name."""

    def __init__(self, string: str):
        """Initialize a FamilyString."""
        self.__string = string

    def __normalize(self, name):
        norm = re.sub(r'-$', '', re.sub(r'^-', '',
                                        re.sub(r'[\W_]+', '-', name))).lower()
        return norm

    def __normalize_mutable(self):
        self.__string = self.__normalize(self.__string)
        return self

    def __dropsuffix(self, slist):
        n = self.__string
        for s in slist:
            n, c = re.subn(r'-{}$'.format(self.__normalize(s)), '', n)
            if c == 1:
                break
        self.__string = n
        return self

    def __dropduplicate(self):
        tokens = ['font', 'fonts']
        s = ''
        for t in self.__string.split('-'):
            if t not in tokens:
                s = s + '-' + t
                tokens.append(t)
        self.__string = re.sub(r'^-', '', s)
        return self

    def normalize(self) -> str:
        """Normalize a family name in string."""
        return self.__normalize_mutable().__dropsuffix(
            ['normal', 'book', 'regular', 'upright']).__dropsuffix([
                'italic', 'ita', 'ital', 'cursive', 'kursiv', 'oblique',
                'inclined', 'backslanted', 'backslant', 'slanted'
            ]).__dropsuffix([
                'ultracondensed', 'extra-compressed', 'ext-compressed',
                'ultra-compressed', 'ultra-condensed', 'extracondensed',
                'compressed', 'extra-condensed', 'ext-condensed', 'extra-cond',
                'semicondensed', 'narrow', 'semi-condens', 'semiexpanded',
                'wide', 'semi-expanded', 'semi-extended', 'extraexpanded',
                'extra-expanded', 'ext-expanded', 'extra-extended',
                'ext-extended', 'ultraexpanded', 'ultra-expanded',
                'ultra-extended', 'condensed', 'cond', 'expanded', 'extended'
            ]).__dropsuffix([
                'thin', 'extra-thin', 'ext-thin', 'ultra-thin', 'extralight',
                'extra-light', 'ext-light', 'ultra-light', 'demibold',
                'semi-bold', 'demi-bold', 'extrabold', 'extra-bold',
                'ext-bold', 'ultra-bold', 'extrablack', 'extra-black',
                'ext-black', 'ultra-black', 'bold', 'thin', 'light', 'medium',
                'black', 'heavy', 'nord', 'demi', 'ultra'
            ]).__dropduplicate()

    def __str__(self) -> str:
        """Represent a string held in FamilyString class."""
        return self.__string
