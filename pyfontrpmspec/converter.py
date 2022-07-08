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
import shutil
import subprocess
import sys
from pyrpm.spec import Spec
from pyfontrpmspec import font_reader as fr
from pyfontrpmspec.messages import Message as m
from pyfontrpmspec import sources as src
from pyfontrpmspec import template
from pyfontrpmspec import package

def old2new(specfile, args):
    if not shutil.which('rpmspec'):
        raise AttributeError(m().error('rpmspec is not installed'))
    origspec = Spec.from_file(specfile)
    ss = subprocess.run(['rpmspec', '-P', specfile], stdout=subprocess.PIPE)
    spec = Spec.from_string(ss.stdout.decode('utf-8'))
    exdata = {'sources': [], 'nsources': {}}
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
                    m([': ', ' ']).info(sf.family).warning('Duplicate family name').out()
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
                    m([': ', ' ']).info(sf.name).warning('Duplicate font files detected. this may not works as expected').out()
                if not source.is_archive():
                    source.ignore = True
            elif sf.is_appstream_file():
                m([': ', ' ']).info(sf.name).warning('AppStream file is no longer needed. this will be generated by the macro automatically').out()
                if not source.is_archive():
                    source.ignore = True
            else:
                m([': ', ' ']).info(sf.name).warning('Unknown type of file').out()
                if not source.is_archive():
                    source.ignore = True

        if 'archive' not in exdata or exdata['archive'] == False:
            exdata['archive'] = source.is_archive()
        elif source.is_archive():
            raise AttributeError(m().error('Multiple archives are not supported'))
        if 'root' not in exdata:
            if source.root != '{}-{}'.format(spec.name, spec.version):
                exdata['root'] = source.root
            else:
                exdata['root'] = ''
        if not source.ignore and not source.is_archive():
            exdata['sources'].append(source.realname)
            exdata['nsources'][source.realname] = nsource
            nsource += 1

    if 'licenses' not in exdata:
        raise TypeError(m().error('No license files detected'))
    if 'fonts' not in exdata:
        raise TypeError(m().error('No fonts files detected'))
    if 'fontconfig' not in exdata:
        raise TypeError(m().error('No fontconfig files detected'))
    if len(spec.patches) > 1:
        for p in spec.patches:
            m([': ']).info(p).warning('Ignoring patch file. they have to be done manually.').out()

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
            'changelog': spec.changelog.rstrip(),
        }
        templates = template.get(1, data)
    else:
        m().error('Multiple sub-packages not yet supported').out()

    return templates

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
    if args.output.name != '<stdout>':
        pkg = package.Package()
        r = pkg.source_name(args.output.name)
        if r != args.output.name:
            m().message('Proposed spec filename is').info(r).out()

    m([': ', ' ']).warning('Note').message('You have to review the result. this doesn\'t guarantee that the generated spec file can be necessarily built properly.').out()

if __name__ == '__main__':
    main()
