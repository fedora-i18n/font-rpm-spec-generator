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
import textwrap
from collections import OrderedDict
from datetime import date
from babel.dates import format_date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
import pyfontrpmspec.errors as err
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
        'epoch' not in kwargs and kwargs.update({'epoch': None})
        'common_description' not in kwargs and kwargs.update(
            {'common_description': ''})
        'email' not in kwargs and kwargs.update(
            {'email': os.environ.get('EMAIL')})
        'excludepath' not in kwargs and kwargs.update({'excludepath': []})
        'ignore_error' not in kwargs and kwargs.update({'ignore_error': []})
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
        'vf_priority' not in kwargs and kwargs.update({'vf_priority': 68})
        'sourcedir' not in kwargs and kwargs.update({'sourcedir': '.'})
        'summary' not in kwargs and kwargs.update(
            {'summary': '{family}, {alias} typeface {type} font'})
        'username' not in kwargs and kwargs.update(
            {'username': pwd.getpwnam(getpass.getuser()).pw_gecos})
        'version' not in kwargs and kwargs.update({'version': None})
        'rpmautospec' not in kwargs and kwargs.update({'rpmautospec': True})
        'autorelease_opt' not in kwargs and kwargs.update(
            {'autorelease_opt': ''})
        'pkgheader' not in kwargs and kwargs.update({'pkgheader': {}})
        return func(**kwargs)

    return wrapper


@params
def generate(name: str, sources: str | list[str], url: str,
             **kwargs: Any) -> dict[str, Any]:
    """Generate a spec file.

    Currently following keyword arguments are supported:

    'name': str - Archive name.
    'sources': str|list[str] - the source files.
    'url': str - URL to the project.
    'alias': str (optional) - Alias name for targeted family.
    'changelog': str (optional) - changelog entry.
    'description': str (optional) - Package description.
    'epoch': int (optional) - Epoch number.
    'common_description': str (optional) - Common package description.
                                           This is used only when generating
                                           multi packages.
    'email': str (optional) - A mail address for maintainer.
    'excludepath': list[str] (optional) - A list of exclusive paths
                                          for sources.
    'ignore_error': list[str] (optional) - A list of exception name to ignore.
    'lang': list[str] (optional) - A list of targeted language for a font
    'license': str (optional) - License name.
    'priority': int (optional) - Number of Fontconfig config priority.
    'vf_priority': int (optional) - Number of Fontconfig config priority
                                    for variable font.
    'sourcedir': str (optional) - Source directory. current directory
                                  will be used if not.
    'summary': str (optional) - Summary of package.
    'username': str (optional) - A name of package maintainer.
    'version': str (optional) - Archive version. if not specified,
                                it will be guessed from the source.
    'rpmautospec': bool (optional) - True to use rpmautospec otherwise False.
    'autorelease_opt': str (optional) - Extra arguments to %autorelease.
    'pkgheader': dict[str, list[str]] (optional) - Package header lines.

    This function returns dict with following key and values:
    'spec': str - RPM spec
    'fontconfig': FontconfigGenerator - fontconfig file to be output
    """
    kwargs['name'] = name
    kwargs['sources'] = sources
    kwargs['url'] = url
    kwargs['common_description'] is None and kwargs.update(
        {'common_description': ''})
    kwargs['autorelease_opt'] is None and kwargs.update(
        {'autorelease_opt': ''})
    retval = {'spec': None, 'fontconfig': []}
    extra_headers = {}

    ma = re.match(
        r'^{}-v?(((?!tar|zip)[0-9.a-zA-Z])+)\..*'.format(kwargs['name']),
        Path(src.Source(kwargs['sources'][0]).name).name)
    version = kwargs['version'] if kwargs['version'] is not None else ma.group(
        1) if ma else None
    if version is None:
        raise TypeError(m().error('Unable to guess version number'))
    v = version.split(':')
    (kwargs['epoch'],
     kwargs['version']) = v if len(v) == 2 else (kwargs['epoch'], v[0])
    kwargs['epoch'] is not None and extra_headers.update(
        {'Epoch': kwargs['epoch']})

    exdata = src.extract(**kwargs)

    if len(exdata['licenses']) == 0:
        m().error('No license files detected').throw(err.MissingFileError,
                                                     kwargs['ignore_error'])
    if len(exdata['fonts']) == 0:
        # Ignoring this isn't useful at all. don't pass kwargs['ignore_error']
        # intentionally
        m().error('No fonts files detected').throw(err.MissingFileError)

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
    for k, v in OrderedDict(sorted(fr.group(
            exdata['fontinfo']).items())).items():
        if len(v[0]['fontinfo']['alias']) > 1:
            m([': '
               ]).info(k).warning('Multiple generic alias was detected').info(
                   v[0]['fontinfo']['alias']).out()
        if kwargs['alias'] == 'auto':
            kwargs['alias'] = v[0]['fontinfo']['alias'][0]
        pkgheader = [] if k not in kwargs['pkgheader'] else kwargs[
            'pkgheader'][k]
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
            'pkgheader':
            '\n'.join(pkgheader)
        }
        families.append(info)
        c = FontconfigGenerator()
        for a in [vvv for vv in v for vvv in vv['fontinfo']['alias']]:
            c.add(a, v[0]['fontinfo']['family'], kwargs['lang'],
                  v[0]['fontinfo']['hashint'])
        c.set_fn(
            kwargs['priority']
            if not v[0]['fontinfo']['variable'] else kwargs['vf_priority'],
            str(
                FamilyString(exdata['foundry'] + ' ' + re.sub(
                    r'^{}'.format(exdata['foundry']), '', k)).normalize()) +
            '-fonts')
        retval['fontconfig'].append(c)
        fontconfig.append(c.get_fn())

    source = kwargs['sources'][0] if urlparse(
        kwargs['sources'][0], allow_fragments=True).scheme else Path(
            kwargs['sources'][0]).name
    release = '1' if not kwargs['rpmautospec'] else '%autorelease{}{}'.format(
        '' if len(kwargs['autorelease_opt']) == 0 else ' ',
        kwargs['autorelease_opt'])
    changelog = '* {} {} <{}> - {}-1\n- {}'.format(
        format_date(date.today(), "EEE MMM dd yyyy",
                    locale='en'), kwargs['username'], kwargs['email'], version,
        kwargs['changelog']) if not kwargs['rpmautospec'] else '%autochangelog'
    data = {
        'version':
        kwargs['version'],
        'release':
        release,
        'url':
        kwargs['url'],
        'extra_headers':
        '\n'.join(['{}: {}'.format(k, v) for k, v in extra_headers.items()]),
        'common_description':
        '\n'.join(textwrap.wrap(kwargs['common_description'])),
        'source':
        source,
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
        ' '.join([s.name for s in exdata['docs']])
        if len(exdata['docs']) > 0 else '%{nil}',
        'foundry':
        exdata['foundry'],
        'fonts':
        families,
        'fontconfig':
        fontconfig,
        'setup':
        exdata['setup'],
        'changelog':
        changelog,
    }
    if len(families) == 1:
        data['family'] = families[0]['family']
        data['summary'] = families[0]['summary']
        data['description'] = '\n'.join(
            textwrap.wrap(families[0]['description']))
        data['fontconfig'] = '%{nil}' if len(
            data['fontconfig']) == 0 else data['fontconfig'][0]
        data['fonts'] = families[0]['fonts']
        data['pkgheader'] = families[0]['pkgheader']

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
    parser.add_argument(
        '--common-description',
        help=('Common package description. '
              'this is only used when generating multi packages.'))
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
    parser.add_argument(
        '--vf-priority',
        type=int,
        default=68,
        help='Number of Fontconfig config priority for variable font')
    parser.add_argument('-e',
                        '--excludepath',
                        action='append',
                        help='Exclude path from source archives')
    parser.add_argument('--rpmautospec',
                        action=argparse.BooleanOptionalAction,
                        default=True,
                        help='Use rpmautospec.')
    parser.add_argument('--autorelease-opt',
                        help='Extra arguments to %autorelease.')
    parser.add_argument('--ignore-error',
                        nargs='*',
                        help='Deal with the specific error as warning')
    parser.add_argument('NAME', help='Package name')
    parser.add_argument('VERSION', nargs='?', help='Package version')
    parser.add_argument('URL', help='Project URL')

    args = parser.parse_args()
    if args.json_file:
        args = __load_config(args.json_file, args)
    if args.source is None or len(args.source) == 0:
        parser.print_usage()
        sys.exit(1)

    templates = generate(name=args.NAME,
                         version=args.VERSION,
                         url=args.URL,
                         license=args.license,
                         sources=args.source,
                         sourcedir=args.sourcedir,
                         changelog=args.changelog,
                         email=args.email,
                         username=args.username,
                         summary=args.summary,
                         description=args.description,
                         common_description=args.common_description,
                         alias=args.alias,
                         lang=args.lang,
                         priority=args.priority,
                         vf_priority=args.vf_priority,
                         excludepath=args.excludepath,
                         ignore_error=args.ignore_error,
                         rpmautospec=args.rpmautospec,
                         autorelease_opt=args.autorelease_opt)
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
