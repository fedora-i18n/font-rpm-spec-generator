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

import shutil
import subprocess
from pyrpm.spec import Spec

class Package:

    def source_name(self, src):
        if src.endswith('.spec'):
            if not shutil.which('rpmspec'):
                raise AttributeError('rpmspec is not installed')
            ss = subprocess.run(['rpmspec', '-P', src], stdout=subprocess.PIPE)
            spec = Spec.from_string(ss.stdout.decode('utf-8'))
            return spec.name
        else:
            raise AttributeError('Unsupported filetype {}'.format(src))
