# generator.py
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
"""Module to generate a RPM spec file."""

import argparse
import getpass
import json
import os
import pwd
import re
import sys
from datetime import date
from babel.dates import format_date
from pathlib import Path
from typing import Any
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
from pyfontrpmspec import font_reader as fr
from pyfontrpmspec.messages import Message as m
from pyfontrpmspec import sources as src
from pyfontrpmspec import template
from pyfontrpmspec.package import Package, FamilyString


def params(func):
    """Decorate function to initialize default parameters."""

    def wrapper(*args, **kwargs):
        kwargs.update(zip(func.__code__.co_varnames, args))
        # Add default values for optional parameters.
        'alias' not in kwargs and kwargs.update({'alias': 'auto'})
        'changelog' not in kwargs and kwargs.update(
            {'changelog': 'Initial import'})
        'description' not in kwargs and kwargs.update({
            'description': ('This package contains {family} which is a {alias}'
                            ' typeface of {type} font.')
        })
        'email' not in kwargs and kwargs.update(
            {'email': os.environ.get('EMAIL')})
        'excludepath' not in kwargs and kwargs.update({'excludepath': None})
        'lang' not in kwargs and kwargs.update({'lang': None})
        'license' not in kwargs and kwargs.update({'license': 'OFL-1.1'})
        'output' not in kwargs and kwargs.update({'output': '-'})
        if not (hasattr(kwargs['output'], 'write')
                and hasattr(kwargs['output'], 'close')):
            kwargs['output'] = sys.stdout if kwargs['output'] == '-' else open(
                kwargs['output'], 'w')
        if 'sources' in kwargs and not isinstance(kwargs['sources'], list):
            kwargs['sources'] = list(kwargs['sources'])
        'outputdir' not in kwargs and kwargs.update({'outputdir': '.'})
        'priority' not in kwargs and kwargs.update({'priority': 69})
        'sourcedir' not in kwargs and kwargs.update({'sourcedir': '.'})
        'summary' not in kwargs and kwargs.update(
            {'summary': '{family}, {alias} typeface {type} font'})
        'username' not in kwargs and kwargs.update(
            {'username': pwd.getpwnam(getpass.getuser()).pw_gecos})
        return func(*args, **kwargs)

    return wrapper


@params
def generate(name, sources, url, **kwargs: Any) -> dict[str, Any]:
    """Generate a spec file.

    Currently following keyword arguments are supported:

    'name': str - Archive name.
    'sources': str|list[str] - the source files.
    'url': str - URL to the project.
    'alias': str (optional) - Alias name for targeted family.
    'changelog': str (optional) - changelog entry.
    'description': str (optional) - Package description.
    'email': str (optional) - A mail address for maintainer.
    'excludepath': list[str] (optional) - A list of exclusive paths
                                          for sources.
    'lang': list[str] (optional) - A list of targeted language for a font
    'license': str (optional) - License name.
    'priority': int (optional) - Number of Fontconfig config priority.
    'sourcedir': str (optional) - Source directory. current directory
                                  will be used if not.
    'summary': str (optional) - Summary of package.
    'username': str (optional) - A name of package maintainer.
    'version': str (optional) - Archive version. if not specified,
                                it will be guessed from the source.

    This function returns dict with following key and values:
    'spec': str - RPM spec
    'fontconfig': FontconfigGenerator - fontconfig file to be output
    """
    kwargs['name'] = name
    kwargs['sources'] = sources
    kwargs['url'] = url
    retval = {'spec': None, 'fontconfig': []}

    ma = re.match(
        r'^{}-v?(((?!tar|zip)[0-9.a-zA-Z])+)\..*'.format(kwargs['name']),
        kwargs['sources'][0])
    version = kwargs['version'] if kwargs['version'] is not None else ma.group(
        1) if ma else None
    if version is None:
        raise TypeError(m().error('Unable to guess version number'))
    exdata = src.extract(kwargs['name'],
                         version,
                         kwargs['sources'],
                         kwargs['sourcedir'],
                         excludepath=kwargs['excludepath'])

    if 'licenses' not in exdata:
        raise TypeError(m().error('No license files detected'))
    if 'fonts' not in exdata:
        raise TypeError(m().error('No fonts files detected'))

    if not exdata['archive']:
        exdata['setup'] = '-c -T'
    elif not exdata['root']:
        exdata['setup'] = ''
    elif exdata['root'] == '.':
        exdata['setup'] = '-c'
    else:
        exdata['setup'] = '-n {}'.format(exdata['root'])

    data = {}
    families = []
    fontconfig = []
    for k, v in fr.group(exdata['fontinfo']).items():
        if len(v[0]['fontinfo']['alias']) > 1:
            m([': '
               ]).info(k).warning('Multiple generic alias was detected').info(
                   v[0]['fontinfo']['alias']).out()
        if kwargs['alias'] == 'auto':
            kwargs['alias'] = v[0]['fontinfo']['alias'][0]
        info = {
            'family':
            k,
            'summary':
            kwargs['summary'].format(family=k,
                                     alias=kwargs['alias'],
                                     type=v[0]['fontinfo']['type']),
            'fonts':
            ' '.join([vv['file'] for vv in v]),
            'exfonts':
            '%{nil}',
            'conf':
            len(families) + 10,
            'exconf':
            '%{nil}',
            'description':
            kwargs['description'].format(family=k,
                                         alias=kwargs['alias'],
                                         type=v[0]['fontinfo']['type']),
        }
        families.append(info)
        c = FontconfigGenerator()
        for a in [vvv for vv in v for vvv in vv['fontinfo']['alias']]:
            c.add(a, k, kwargs['lang'], v[0]['fontinfo']['hashint'])
        c.set_fn(
            kwargs['priority'],
            str(
                FamilyString(exdata['foundry'] + ' ' + re.sub(
                    r'^{}'.format(exdata['foundry']), '', k)).normalize()) +
            '-fonts')
        retval['fontconfig'].append(c)
        fontconfig.append(c.get_fn())

    data = {
        'version':
        version,
        'release':
        1,
        'url':
        kwargs['url'],
        'source':
        Path(kwargs['sources'][0]).name,
        'copy_source':
        not exdata['archive'],
        'exsources':
        exdata['sources'],
        'nsources':
        exdata['nsources'],
        'license':
        kwargs['license'],
        'license_file':
        ' '.join([s.name for s in exdata['licenses']]),
        'docs':
        ' '.join([s.name for s in exdata['docs']]),
        'foundry':
        exdata['foundry'],
        'fonts':
        families,
        'fontconfig':
        fontconfig,
        'setup':
        exdata['setup'],
        'changelog':
        '* {} {} <{}> - {}-1\n- {}'.format(
            format_date(date.today(), "EEE MMM dd yyyy", locale='en'),
            kwargs['username'], kwargs['email'], version, kwargs['changelog']),
    }
    if len(families) == 1:
        data['family'] = families[0]['family']
        data['summary'] = families[0]['summary']
        data['description'] = families[0]['description']
        data['fontconfig'] = '%{nil}' if len(
            data['fontconfig']) == 0 else data['fontconfig'][0]
        data['fonts'] = families[0]['fonts']

    retval.update(template.get(len(families), data))
    return retval


class FontconfigEntry:
    """Class to hold font information."""

    def __init__(self,
                 family: str,
                 lang: str | list[str] = None,
                 hashint: bool = False):
        """Initialize a FontconfigEntry class."""
        self.family = family
        self.lang = lang
        self.hashint = hashint


class FontconfigGenerator:
    """Class to generate a fontconfig config file."""

    def __init__(self):
        """Initialize a FontconfigGenerator class."""
        self._families = {}
        self.path = None
        self._confname = ''

    def add(self,
            alias: str,
            family: str,
            lang: str | list[str] = None,
            hashint: bool = False) -> None:
        """Add the information of fonts into the object."""
        if alias not in self._families:
            self._families[alias] = []
        if not isinstance(lang, list):
            lang = [lang]
        for v in self._families[alias]:
            if v.family == family and set(
                    v.lang) == set(lang) and v.hashint == hashint:
                return
        self._families[alias].append(FontconfigEntry(family, lang, hashint))

    def set_fn(self, priority: int, fn: str) -> None:
        """Set a filename."""
        self._confname = "{:02}-{}.conf".format(priority, fn)

    def get_fn(self) -> str:
        """Get a real filename which contains a fontconfig config."""
        return self._confname

    def write(self) -> None:
        """Write a content of fontconfig config into a file."""
        if self._confname is None:
            raise TypeError(
                m().warning('filename isn\'t yet set for fontconfig.').out())

        template = ('<?xml version="1.0"?>\n'
                    '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                    '<fontconfig>\n'
                    '{rules}'
                    '</fontconfig>\n')
        generic = ('  <match>\n'
                   '{langrule}'
                   '    <test name="family">\n'
                   '      <string>{alias}</string>\n'
                   '    </test>\n'
                   '    <edit name="family" mode="prepend">\n'
                   '      <string>{family}</string>\n'
                   '    </edit>\n'
                   '    <edit name="fonthashint" mode="append">\n'
                   '      <bool>{hashint}</bool>\n'
                   '    </edit>\n'
                   '  </match>\n')
        default = ('  <alias>\n'
                   '    <family>{family}</family>\n'
                   '    <default>\n'
                   '      <family>{alias}</family>\n'
                   '    </default>\n'
                   '  </alias>\n')
        langrule = ('    <test name="lang" compare="contains">\n'
                    '      <string>{lang}</string>\n'
                    '    </test>\n')
        rules = []
        for k, v in self._families.items():
            for vv in v:
                for ll in vv.lang:
                    if ll is None:
                        lv = ''
                    else:
                        lv = langrule.format(lang=ll)
                    s = generic.format(langrule=lv,
                                       alias=k,
                                       family=vv.family,
                                       hashint=str(vv.hashint).lower())
                    rules.append(s)
                s = default.format(alias=k, family=vv.family)
                rules.append(s)

        if self.path is None:
            raise ValueError('Set a path first.')
        with open(Path(self.path) / self._confname, 'w') as f:
            m([': ', ' ']).info(
                self._confname).message('fontconfig file was stored at').info(
                    self.path).out()
            f.write(template.format(rules=''.join(rules)))


class dotdict(dict):
    """Wrapper class to convert dict to Object."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def __load_config(config, args):
    with open(config) as f:
        confdata = json.load(f)

    args = vars(args)
    for k, v in confdata.items():
        # override missing values only.
        # have a priority to properties given by options
        if k not in args.keys():
            args[k] = v

    return dotdict(args)


def main():
    """Endpoint function to generate a RPM spec file from given parameters."""
    parser = argparse.ArgumentParser(
        description='Fonts RPM spec file generator against guidelines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-f',
                        '--json-file',
                        help='Config file written in JSON')
    parser.add_argument('-l',
                        '--license',
                        default='OFL-1.1',
                        help='License name of this project')
    parser.add_argument('-o',
                        '--output',
                        default='-',
                        type=argparse.FileType('w'),
                        help='Output file')
    parser.add_argument('--outputdir', default='.', help='Output directory')
    parser.add_argument('--sourcedir', default='.', help='Source directory')
    parser.add_argument('-s', '--source', action='append', help='Source file')
    parser.add_argument('-u', '--url', help='Project URL')
    parser.add_argument('-c',
                        '--changelog',
                        default='Initial import',
                        help='Changelog entry')
    parser.add_argument('--email',
                        default=os.environ.get('EMAIL'),
                        help='email address to put into changelog')
    parser.add_argument('--username',
                        default=pwd.getpwnam(getpass.getuser()).pw_gecos,
                        help='Real user name to put into changelog')
    parser.add_argument('--summary',
                        default='{family}, {alias} typeface {type} font',
                        help='Summary text for package')
    parser.add_argument(
        '--description',
        default=('This package contains {family} which is a {alias}'
                 ' typeface of {type} font.'),
        help='Package description')
    parser.add_argument('-a',
                        '--alias',
                        default='auto',
                        help=('Set an alias name for family, '
                              'such as sans-serif, serif, monospace'))
    parser.add_argument('--lang',
                        nargs='*',
                        help='Targetted language for a font')
    parser.add_argument('--priority',
                        type=int,
                        default=69,
                        help='Number of Fontconfig config priority')
    parser.add_argument('-e',
                        '--excludepath',
                        action='append',
                        help='Exclude path from source archives')
    parser.add_argument('NAME', help='Package name')
    parser.add_argument('VERSION', nargs='?', help='Package version')

    args = parser.parse_args()
    if args.json_file:
        args = __load_config(args.json_file, args)
    if args.source is None or len(args.source) == 0:
        parser.print_usage()
        sys.exit(1)

    templates = generate(name=args.NAME,
                         version=args.VERSION,
                         url=args.url,
                         sources=args.source,
                         sourcedir=args.sourcedir,
                         excludepath=args.excludepath)
    if templates is None:
        sys.exit(1)

    for f in templates['fontconfig']:
        f.path = args.outputdir
        f.write()
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
