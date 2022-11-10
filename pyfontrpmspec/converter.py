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

import argparse
import os
import shutil
import subprocess
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from pyrpm.spec import Spec
from pyfontrpmspec import font_reader as fr
from pyfontrpmspec.messages import Message as m
from pyfontrpmspec import sources as src
from pyfontrpmspec import template
from pyfontrpmspec.package import Package


def old2new(specfile, args):
    if not shutil.which('rpmspec'):
        raise AttributeError(m().error('rpmspec is not installed'))
    origspec = Spec.from_file(specfile)
    ss = subprocess.run(['rpmspec', '-P', specfile], stdout=subprocess.PIPE)
    spec = Spec.from_string(ss.stdout.decode('utf-8'))
    exdata = src.extract(spec.name, spec.version, spec.sources, args.sourcedir)

    if 'licenses' not in exdata:
        raise TypeError(m().error('No license files detected'))
    if 'fonts' not in exdata:
        raise TypeError(m().error('No fonts files detected'))
    if 'fontconfig' not in exdata:
        raise TypeError(m().error('No fontconfig files detected'))
    if len(spec.patches) > 1:
        for p in spec.patches:
            m([': ']).info(p).warning('Ignoring patch file. they have to be done manually').out()

    if not exdata['archive']:
        exdata['setup'] = '-c -T'
    elif not exdata['root']:
        exdata['setup'] = ''
    elif exdata['root'] == '.':
        exdata['setup'] = '-c'
    else:
        exdata['setup'] = '-n {}'.format(exdata['root'])
    if len(spec.packages) == 1:
        fontinfo = exdata['fontinfo'][list(exdata['fontinfo'].keys())[0]]
        family = fontinfo['family']
        if len(exdata['fontconfig']) > 1:
            raise TypeError(m().error('Multiple fontconfig files detected'))
        if family not in exdata['fontconfig']:
            raise TypeError(m().error('No fontconfig file for').message(family))
        # single template
        data = {
            'version': spec.version,
            'release': origspec.release,
            'url': spec.url,
            'origsource': origspec.sources[0],
            'source': spec.sources[0],
            'copy_source': not exdata['archive'],
            'exsources': exdata['sources'],
            'nsources': exdata['nsources'],
            'patches': spec.patches,
            'fontconfig': exdata['fontconfig'][family].name,
            'license': spec.license,
            'license_file': ' '.join([s.name for s in exdata['licenses']]),
            'docs': ' '.join([s.name for s in exdata['docs']]) if 'docs' in exdata else '%{nil}',
            'fonts': ' '.join([s.name for s in exdata['fonts']]),
            'foundry': exdata['foundry'],
            'family': family,
            'summary': spec.summary,
            'description': spec.description.rstrip(),
            'setup': exdata['setup'],
            'changelog': origspec.changelog.rstrip(),
        }
    else:
        families = []
        fontconfig = []
        for k, v in fr.group(exdata['fontinfo']).items():
            if 'fontmap' in exdata and k in exdata['fontmap']:
                k = exdata['fontmap'][k]
            summary = None
            description = None
            for p in spec.packages:
                if Package.is_targeted_package(p.name, k):
                    if p.name == spec.name:
                        summary = spec.summary
                        description = spec.description
                    else:
                        summary = p.summary
                        description = p.description
            if not summary:
                m([': ']).info(k).warning('Unable to guess the existing package name. some information may be missing in the spec file').out()
            if k not in exdata['fontconfig']:
                m([': ']).info(k).warning('No fontconfig file')
            info = {
                'family': k,
                'summary': summary,
                'fonts': ' '.join([vv['file'] for vv in v]),
                'exfonts': '%{nil}',
                'conf': len(families) + 10 if k in exdata['fontconfig'] else '%{nil}',
                'exconf': '%{nil}',
                'description': description,
            }
            families.append(info)
            if k in exdata['fontconfig']:
                fontconfig.append(exdata['fontconfig'][k].name)
        data = {
            'version': spec.version,
            'release': origspec.release,
            'url': spec.url,
            'origsource': origspec.sources[0],
            'source': spec.sources[0],
            'copy_source': not exdata['archive'],
            'exsources': exdata['sources'],
            'nsources': exdata['nsources'],
            'patches': spec.patches,
            'license': spec.license,
            'license_file': ' '.join([s.name for s in exdata['licenses']]),
            'docs': ' '.join([s.name for s in exdata['docs']]) if 'docs' in exdata else '%{nil}',
            'foundry': exdata['foundry'],
            'fonts': families,
            'fontconfig': fontconfig,
            'setup': exdata['setup'],
            'changelog': origspec.changelog.rstrip(),
        }

    return template.get(len(spec.packages), data)


def main():
    parser = argparse.ArgumentParser(description='Fonts RPM spec file converter against guidelines',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--sourcedir',
                        default='.',
                        help='Source directory')
    parser.add_argument('-o', '--output',
                        default='-',
                        type=argparse.FileType('w'),
                        help='Output file')
    parser.add_argument('SPEC',
                        help='Spec file to convert')

    args = parser.parse_args()

    templates = old2new(args.SPEC, args)
    if templates is None:
        sys.exit(1)

    args.output.write(templates['spec'])
    args.output.close()
    print('\n', flush=True, file=sys.stderr)
    if args.output.name != '<stdout>':
        r = Package.source_name(args.output.name)
        if r is None:
            m().warning('Unable to guess the spec filename').out()
        elif r + '.spec' != args.output.name:
            m().message('Proposed spec filename is').info(r+'.spec').out()

    m([': ', ' ']).warning('Note').message('You have to review the result. this doesn\'t guarantee that the generated spec file can be necessarily built properly.').out()


if __name__ == '__main__':
    main()
