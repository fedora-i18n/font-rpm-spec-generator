# converter.py
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
import subprocess
import sys
from pyrpm.spec import Spec
from pyfontrpmspec import extract
from pyfontrpmspec import template

def old2new(specfile, args):
    origspec = Spec.from_file(specfile)
    ss = subprocess.run(['rpmspec', '-P', specfile], stdout=subprocess.PIPE)
    spec = Spec.from_string(ss.stdout.decode('utf-8'))
    fcfiles = [s for s in spec.sources if 'fontconfig' in s]
    if len(fcfiles) == 0:
        print('Unable to guess fontconfig file.', flush=True, file=sys.stderr)
        return None
    source = os.path.basename(spec.sources[0])
    exdata = extract.extract(os.path.join(args.sourcedir, source), spec.name, spec.version)
    if exdata is None:
        return None
    if not exdata['root']:
        exdata['setup'] = ''
    else:
        exdata['setup'] = '-n {}'.format(exdata['root'])
    if len(spec.packages) == 1:
        if len(fcfiles) > 1:
            print('Detected multiple fontconfig files.', flush=True, file=sys.stderr)
            return None
        package = spec.packages[0]
        fontinfo = exdata['fontinfo'][list(exdata['fontinfo'].keys())[0]]
        if 'WWS_Family_Name' in fontinfo:
            family = fontinfo['WWS_Family_Name']
        elif 'Typographic_Family' in fontinfo:
            family = fontinfo['Typographic_Family']
        else:
            family = fontinfo['Font_Family']
        # single template
        data = {
            'version': spec.version,
            'release': origspec.release,
            'url': spec.url,
            'source': spec.sources[0],
            'fontconfig': fcfiles[0],
            'license': spec.license,
            'license_file': ' '.join(exdata['license']),
            'docs': ' '.join(exdata['docs']),
            'fonts': ' '.join(exdata['fonts']),
            'foundry': exdata['foundry'],
            'family': family,
            'summary': spec.summary,
            'description': spec.description,
            'setup': exdata['setup'],
            'changelog': spec.changelog,
        }
        templates = template.get(1, data)

    return templates
