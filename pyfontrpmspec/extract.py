# extract.py
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
from pyfontrpmspec import font_reader as fr

def drop_root(fn):
    return os.path.join(*os.path.normpath(fn).split(os.sep)[1:])

def get_root(fn):
    return os.path.normpath(fn).split(os.sep)[0]

def extract(archive, name, version):
    retval = {}
    with tempfile.TemporaryDirectory() as tempdir:
        shutil.unpack_archive(archive, tempdir)
        for root, dirs, files in os.walk(tempdir):
            for fn in files:
                if not 'root' in retval:
                    parent = get_root(os.path.relpath(root, tempdir))
                    if parent != '{}-{}'.format(name, version):
                        retval['root'] = parent
                    else:
                        retval['root'] = ''
                if re.search(r'(?i:license)', fn):
                    if not 'license' in retval:
                        retval['license'] = []
                    retval['license'].append(drop_root(os.path.join(os.path.relpath(root, tempdir), fn)))
                elif re.search(r'(?i:readme)', fn):
                    if not 'docs' in retval:
                        retval['docs'] = []
                    retval['docs'].append(drop_root(os.path.join(os.path.relpath(root, tempdir), fn)))
                else:
                    if fn.endswith('.txt'):
                        if not 'docs' in retval:
                            retval['docs'] = []
                        retval['docs'].append(drop_root(os.path.join(os.path.relpath(root, tempdir), fn)))
                    elif fn.endswith('.otf') or fn.endswith('.ttf'):
                        if not 'fonts' in retval:
                            retval['fonts'] = []
                        fontfn = os.path.join(root, fn)
                        kfn = drop_root(os.path.relpath(fontfn, tempdir))
                        retval['fonts'].append(kfn)
                        if not 'fontinfo' in retval:
                            retval['fontinfo'] = {}
                        if not kfn in retval['fontinfo']:
                            retval['fontinfo'][kfn] = fr.font_meta_reader(fontfn)
                            retval['foundry'] = retval['fontinfo'][kfn]['foundry']
                        else:
                            print('Duplicate font files detected. this may not works as expected: {}'.format(fontfn), flush=True, file=sys.stderr)
                            return None

        if not 'fonts' in retval:
            print('Unable to find out any fonts files in {}'.format(archive), flush=True, file=sys.stderr)
            return None

        return retval
