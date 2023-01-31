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
"""Module to convert a RPM spec file."""

import argparse
import shutil
import subprocess
import sys
from collections import OrderedDict
from pyrpm.spec import Spec
from typing import Any
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
import pyfontrpmspec.errors as err
from pyfontrpmspec import font_reader as fr
from pyfontrpmspec.messages import Message as m
from pyfontrpmspec import sources as src
from pyfontrpmspec import template
from pyfontrpmspec.package import Package


def validate_exdata(exdata):
    """Validate exdata returned by sources.extract."""
    if 'licenses' not in exdata:
        raise TypeError(m().error('No license files detected'))
    if 'fonts' not in exdata:
        raise TypeError(m().error('No fonts files detected'))
    if 'fontconfig' not in exdata:
        raise TypeError(m().error('No fontconfig files detected'))


def params(func):
    """Decorate function to initialize default parameters."""

    def wrapper(*args, **kwargs):
        kwargs.update(zip(func.__code__.co_varnames, args))
        # Add default values for optional parameters.
        'sourcedir' not in kwargs and kwargs.update({'sourcedir': '.'})
        'excludepath' not in kwargs and kwargs.update({'excludepath': []})
        'ignore_error' not in kwargs and kwargs.update({'ignore_error': []})
        'pkgheader' not in kwargs and kwargs.update({'pkgheader': {}})

        return func(**kwargs)

    return wrapper


@params
def old2new(specfile: str, **kwargs: Any) -> str:
    """Convert `specfile` to new one against Packaging Guidelines.

    Currently following keyward arguments are supported:

    'specfile': str - RPM SPEC filename to convert.
    'sourcedir': str (optional) - Source directory. current directory
                                  will be used if not.
    'excludepath': list[str] (optional) - A list of exclusive paths
                                          for sources.
    'ignore_error': list[str] (optional) - A list of exception name to ignore.
    'pkgheader': dict[str, list[str]] (optional) - A list of package header lines.
    """
    kwargs['specfile'] = specfile

    if not shutil.which('rpmspec'):
        raise AttributeError(m().error('rpmspec is not installed'))
    origspec = Spec.from_file(specfile)
    ss = subprocess.run(['rpmspec', '-P', specfile], stdout=subprocess.PIPE)
    spec = Spec.from_string(ss.stdout.decode('utf-8'))
    exdata = src.extract(spec.name, spec.version, spec.sources, **kwargs)
    extra_headers = {}
    spec.epoch and extra_headers.update({'Epoch': spec.epoch})

    validate_exdata(exdata)
    if len(spec.patches) > 1:
        for p in spec.patches:
            m([': ']).info(p).warning(
                'Ignoring patch file. they have to be done manually').out()

    exdata['setup'] = '-c -T' if not exdata['archive'] else '' if not exdata[
        'root'] else '-c' if exdata['root'] == '.' else '-n {}'.format(
            exdata['root'])
    families = []
    fontconfig = []
    for k, v in OrderedDict(fr.group(exdata['fontinfo']).items()).items():
        if 'fontmap' in exdata and k in exdata['fontmap']:
            k = exdata['fontmap'][k]
        summary = None
        description = None
        pkgheader = [] if k not in kwargs['pkgheader'] else kwargs[
            'pkgheader'][k]
        for p in spec.packages:
            if Package.is_targeted_package(p.name, exdata['foundry'], k):
                (summary,
                 description) = (spec.summary, spec.description
                                 ) if p.name == spec.name else (p.summary,
                                                                p.description)
        if not summary:
            m([': ']).info(k).warning(
                ('Unable to guess the existing package name. '
                 'some information may be missing in the spec file')).out()
        if k not in exdata['fontconfig']:
            m([': ']).info(k).warning('No fontconfig file')
        info = {
            'family': k,
            'summary': summary,
            'fonts': ' '.join([vv['file'] for vv in v]),
            'exfonts': '%{nil}',
            'conf':
            len(families) + 10 if k in exdata['fontconfig'] else '%{nil}',
            'exconf': '%{nil}',
            'description': description,
            'pkgheader': '\n'.join(pkgheader),
        }
        families.append(info)
        if k in exdata['fontconfig']:
            fontconfig.append(exdata['fontconfig'][k].name)
    data = {
        'version':
        spec.version,
        'release':
        origspec.release,
        'url':
        spec.url,
        'extra_headers':
        '\n'.join(['{}: {}'.format(k, v) for k, v in extra_headers.items()]),
        'common_description':
        '',
        'origsource':
        origspec.sources[0],
        'source':
        spec.sources[0],
        'copy_source':
        not exdata['archive'],
        'exsources':
        exdata['sources'],
        'nsources':
        exdata['nsources'],
        'patches':
        spec.patches,
        'license':
        spec.license,
        'license_file':
        ' '.join([s.name for s in exdata['licenses']]),
        'docs':
        ' '.join([s.name
                  for s in exdata['docs']]) if 'docs' in exdata else '%{nil}',
        'foundry':
        exdata['foundry'],
        'fonts':
        families,
        'fontconfig':
        fontconfig,
        'setup':
        exdata['setup'],
        'changelog':
        origspec.changelog.rstrip(),
    }
    if len(spec.packages) == 1:
        if len(exdata['fontconfig']) > 1:
            m().error('Multiple fontconfig files detected').throw(
                err.DuplidateFileError, kwargs['ignore_error'])
        data['family'] = families[0]['family']
        if data['family'] not in exdata['fontconfig']:
            m().error('No fontconfig file for').message(data['family']).throw(
                err.DuplidateFileError, kwargs['ignore_error'])
        data['summary'] = families[0]['summary']
        data['description'] = families[0]['description']
        data['fontconfig'] = '%{nil}' if len(
            data['fontconfig']) == 0 else data['fontconfig'][0]
        data['fonts'] = families[0]['fonts']
        data['pkgheader'] = families[0]['pkgheader']

    return template.get(len(spec.packages), data)


def main():
    """Endpoint function to convert a RPM spec file from given parameters."""
    parser = argparse.ArgumentParser(
        description='Fonts RPM spec file converter against guidelines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--sourcedir', default='.', help='Source directory')
    parser.add_argument('-o',
                        '--output',
                        default='-',
                        type=argparse.FileType('w'),
                        help='Output file')
    parser.add_argument('--ignore-error',
                        nargs='*',
                        help='Deal with the specific error as warning')
    parser.add_argument('SPEC', help='Spec file to convert')

    args = parser.parse_args()

    templates = old2new(args.SPEC,
                        sourcedir=args.sourcedir,
                        ignore_error=args.ignore_error)
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
            m().message('Proposed spec filename is').info(r + '.spec').out()

    m([': ', ' ']).warning('Note').message(
        ('You have to review the result. '
         'this doesn\'t guarantee that the generated spec file'
         ' can be necessarily built properly.')).out()


if __name__ == '__main__':
    main()
