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

import shutil
import subprocess
import sys
from pyrpm.spec import Spec
from pyfontrpmspec import font_reader as fr
from pyfontrpmspec import sources as src
from pyfontrpmspec import template

def old2new(specfile, args):
    if not shutil.which('rpmspec'):
        print('rpmspec is not installed', flush=True, file=sys.stderr)
        return None
    origspec = Spec.from_file(specfile)
    ss = subprocess.run(['rpmspec', '-P', specfile], stdout=subprocess.PIPE)
    spec = Spec.from_string(ss.stdout.decode('utf-8'))
    exdata = {'sources': []}
    nsource = 20
    sources = src.Sources(arrays = spec.sources, sourcedir = args.sourcedir)
    for source in sources:
        for sf in source:
            if sf.is_license():
                if 'licenses' not in exdata:
                    exdata['licenses'] = []
                exdata['licenses'].append(sf)
            elif sf.is_doc():
                if 'docs' not in exdata:
                    exdata['docs'] = []
                exdata['docs'].append(sf)
            elif sf.is_fontconfig():
                if 'fontconfig' not in exdata:
                    exdata['fontconfig'] = {}
                if sf.family in exdata['fontconfig']:
                    print('Duplicate family name: {}'.format(sf.family), flush=True, file=sys.stderr)
                exdata['fontconfig'][sf.family] = sf
                if not source.is_archive():
                    source.ignore = True
            elif sf.is_font():
                if 'fonts' not in exdata:
                    exdata['fonts'] = []
                exdata['fonts'].append(sf)
                if 'fontinfo' not in exdata:
                    exdata['fontinfo'] = {}
                if sf.name not in exdata['fontinfo']:
                    exdata['fontinfo'][sf.name] = fr.font_meta_reader(sf.fullname)
                    exdata['foundry'] = exdata['fontinfo'][sf.name]['foundry']
                else:
                    print('Duplicate font files detected. this may not works as expected: {}'.format(sf.name), flush=True, file=sys.stderr)
                if not source.is_archive():
                    source.ignore = True
            else:
                print('Unknown type of file: {}'.format(sf.name), flush=True, file=sys.stderr)
                if not source.is_archive():
                    source.ignore = True

        if 'archive' not in exdata or exdata['archive'] == False:
            exdata['archive'] = source.is_archive()
        elif source.is_archive():
            raise AttributeError('Multiple archives are not supported')
        if 'root' not in exdata:
            if source.root != '{}-{}'.format(spec.name, spec.version):
                exdata['root'] = source.root
            else:
                exdata['root'] = ''
        if not source.ignore and not source.is_archive():
            exdata['sources'].append(source.realname)
            if 'nsources' not in exdata:
                exdata['nsources'] = {}
            exdata['nsources'][source.realname] = nsource
            nsource += 1

    if 'licenses' not in exdata:
        raise TypeError('No license files detected')
    if 'fonts' not in exdata:
        raise TypeError('No fonts files detected')
    if 'fontconfig' not in exdata:
        raise TypeError('No fontconfig files detected')

    if not exdata['archive']:
        exdata['setup'] = '-c -T'
    elif not exdata['root']:
        exdata['setup'] = ''
    elif exdata['root'] == '.':
        exdata['setup'] = '-c'
    else:
        exdata['setup'] = '-n {}'.format(exdata['root'])
    templates = None
    if len(spec.packages) == 1:
        package = spec.packages[0]
        fontinfo = exdata['fontinfo'][list(exdata['fontinfo'].keys())[0]]
        if 'WWS_Family_Name' in fontinfo:
            family = fontinfo['WWS_Family_Name']
        elif 'Typographic_Family' in fontinfo:
            family = fontinfo['Typographic_Family']
        else:
            family = fontinfo['Font_Family']
        if len(exdata['fontconfig']) > 1:
            raise TypeError('Multiple fontconfig files detected')
        if family not in exdata['fontconfig']:
            raise TypeError('No fontconfig file for {}'.format(family))
        # single template
        data = {
            'version': spec.version,
            'release': origspec.release,
            'url': spec.url,
            'source': origspec.sources[0],
            'exsources': exdata['sources'],
            'nsources': exdata['nsources'],
            'fontconfig': exdata['fontconfig'][family].name,
            'license': spec.license,
            'license_file': ' '.join([s.name if not s.is_source() else '%{{SOURCE{}}}'.format(exdata['nsources'][s.realname]) for s in exdata['licenses']]),
            'docs': ' '.join([s.name if not s.is_source() else '%{{SOURCE{}}}'.format(exdata['nsources'][s.realname]) for s in exdata['docs']]) if 'docs' in exdata else '%{nil}',
            'fonts': ' '.join([s.name for s in exdata['fonts']]),
            'foundry': exdata['foundry'],
            'family': family,
            'summary': spec.summary,
            'description': spec.description,
            'setup': exdata['setup'],
            'changelog': spec.changelog,
        }
        templates = template.get(1, data)
    else:
        print('Multiple sub-packages not yet supported', flush=True, file=sys.stderr)

    return templates
