# Copyright (C) 2024 font-rpm-spec-generator Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Module to generate a test case based on tmt"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
from fontrpmspec.messages import Message as m
from fontrpmspec import sources as src


def generate_listdata(pkgname, alias, family, languages):
    return f'{pkgname};{alias};{",".join(languages)};normal;{family};0;0;0;0;0;;;;;'


def generate_plan(planfile, has_fc_conf, has_lang, add_prepare, pkgname,
                  alias, family, languages, warn, is_single_plan, pkglist,
                  is_local):
    if warn:
        m([': ']).info(str(planfile)).warning('Generated file may not be correct').out()
    m([': ']).info(str(planfile)).message('Generating...').out()
    with planfile.open(mode='w') as f:
        if not has_fc_conf:
            disabled = """    exclude:
        - generic_alias
"""
        else:
            disabled = ''
        if not has_lang:
            if not disabled:
                disabled = """    exclude:
        - lang_coverage
        - default_fonts
"""
            else:
                disabled += '        - lang_coverage\n        - default_fonts\n'
        if add_prepare:
            if is_single_plan:
                if is_local:
                    tmpl_pkg = f'{planfile.parents[1].absolute() / 'noarch'}'
                else:
                    tmpl_pkg = '\n' + '\n'.join([f'        - {s}' for s in list(set(pkglist))])
            else:
                tmpl_pkg = pkgname
            prepare = f"""prepare:
    name: tmt
    how: install
    {"directory" if is_local else "package"}: {tmpl_pkg}
"""
        else:
            prepare = ''
        lang = f"    FONT_LANG: {','.join(languages)}" if len(languages) > 0 else ''
        if is_single_plan:
            environment = f'    VARLIST: {"local" if is_local else pkgname}.list'
        else:
            environment = f"""    PACKAGE: {pkgname}
    FONT_ALIAS: {alias}
    FONT_FAMILY: {family}
{lang}"""
        f.write(f"""summary: Fonts related tests
discover:
    how: fmf
    url: https://src.fedoraproject.org/tests/fonts
{disabled}{prepare}execute:
    how: tmt
environment:
{environment}""")


def main():
    """Endpoint function to generate tmt plans from RPM spec file"""
    parser = argparse.ArgumentParser(description='TMT plan generator',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--extra-buildopts',
                        help='Extra buildopts to build package')
    parser.add_argument('-a', '--add-prepare',
                        action='store_true',
                        help='Add prepare section for local testing')
    parser.add_argument('-l', '--local', metavar='FILE',
                        help='Generate a fmf file for local testing. '
                        '`fedpkg local` must be run before `tmt run`',
                        nargs='?',
                        const='local.fmf',
                        default=False)
    parser.add_argument('-s', '--single-plan',
                        action='store_true',
                        help='Generate single plan with list file')
    parser.add_argument('-O', '--outputdir', help='Output directory')
    parser.add_argument('-v', '--verbose',
                        action='store_true', help='Show more detailed logs')
    parser.add_argument('REPO', help='Package repository path')

    args = parser.parse_args()

    cwd = os.getcwd()
    if args.outputdir is None:
        args.outputdir = args.REPO
    if not shutil.which('fedpkg'):
        m([': ', '']).error('E').message('fedpkg is not installed').out()
        sys.exit(1)
    if not shutil.which('rpm'):
        m([': ', '']).error('E').message('rpm is not installed').out()
        sys.exit(1)
    if not shutil.which('fc-query'):
        m([': ', '']).error('E').message('fc-query is not installed').out()
        sys.exit(1)
    if not shutil.which('tmt'):
        m([': ', '']).error('E').message('tmt is not installed').out()
        sys.exit(1)

    if args.local and not args.single_plan:
        m([': ', '']).warning('W').message('--local option expects to work'
                                           ' with --single-plan.').out()
        args.single_plan = True
    if args.local and not args.add_prepare:
        m([': ', '']).warning('W').message('--local option expects to work'
                                           ' with --add-prepare.').out()
        args.add_prepare = True
    cmd = ['tmt', 'init']
    if args.verbose:
        m([' ']).info('#').message(' '.join(cmd)).out()
    subprocess.run(cmd, cwd=args.REPO)
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['fedpkg', 'local', '--define', '_rpmdir {}'.format(tmpdir)]
        if args.extra_buildopts:
            cmd.insert(1, args.extra_buildopts)
        if args.verbose:
            m([' ']).info('#').message(' '.join(cmd)).out()
        subprocess.run(cmd, cwd=args.REPO)

        plandir = Path(args.outputdir) / 'plans'
        plandir.mkdir(parents=True, exist_ok=True)
        listdata = []
        pkglist = []

        for pkg in sorted((Path(tmpdir) / 'noarch').glob('*.rpm')):
            s = src.Source(str(pkg))
            has_fc_conf = False
            has_lang = False
            has_fonts = False
            is_ttc = False
            flist = []
            alist = []
            llist = []
            pfamily = None
            for f in s:
                if f.is_fontconfig():
                    has_fc_conf = True
                if f.is_font():
                    has_fonts = True
                    ss = subprocess.run(['fc-query', '-f', '%{lang}\n', f.fullname],
                                        stdout=subprocess.PIPE)
                    ll = list(filter(None, re.split(r'[,|\n]',
                                                    ss.stdout.decode('utf-8'))))
                    has_lang = has_lang or len(ll) > 0
                    if len(ll) == 1:
                        llist = ll
                    ss = subprocess.run(['fc-scan', '-f', '%{family[0]}\n', f.fullname],
                                        stdout=subprocess.PIPE)
                    pfamily = ss.stdout.decode('utf-8').splitlines()[0]
                try:
                    if f.families is not None:
                        flist += f.families
                except ValueError:
                    if pfamily is not None:
                        flist += [pfamily]
                    has_fc_conf = False
                if f.aliases is not None:
                    alist += f.aliases
                if not llist and f.languages is not None:
                    llist += f.languages
                if f.is_fontcollection():
                    is_ttc = True
            flist = list(dict.fromkeys(flist))
            print(flist)
            alist = list(dict.fromkeys(alist))
            llist = list(dict.fromkeys(llist))
            ss = subprocess.run(['rpm', '-qp', '--qf', '%{name}', str(pkg)],
                                stdout=subprocess.PIPE)
            os.chdir(cwd)
            pkgname = ss.stdout.decode('utf-8')
            if not has_fonts:
                m([': ']).info(pkgname).message('Skipping. No tmt plan is needed.').out()
                continue
            planfile = plandir / (pkgname + '.fmf')
            if is_ttc:
                for fn in flist:
                    sub = fn.replace(flist[0], '').strip().lower()
                    name = pkgname + '.fmf' if not sub else pkgname + '_' + sub + '.fmf'
                    planfile = plandir / name
                    if args.single_plan:
                        listdata.append(generate_listdata(pkgname,
                                                          alist[0] if len(alist) > 0 else None,
                                                          fn, llist))
                        pkglist.append(pkgname)
                    else:
                        generate_plan(planfile, has_fc_conf, has_lang,
                                      args.add_prepare, pkgname,
                                      alist[0] if len(alist) > 0 else None,
                                      fn, llist,
                                      len(flist) > 1 or len(alist) > 1,
                                      args.single_plan, [], False)
            else:
                if args.single_plan:
                    listdata.append(generate_listdata(pkgname,
                                                      alist[0] if len(alist) > 0 else None,
                                                      flist[0] if len(flist) > 0 else None,
                                                      llist))
                    pkglist.append(pkgname)
                else:
                    generate_plan(planfile, has_fc_conf, has_lang,
                                  args.add_prepare, pkgname,
                                  alist[0] if len(alist) > 0 else None,
                                  flist[0] if len(flist) > 0 else None,
                                  llist,
                                  len(flist) > 1 or len(alist) > 1,
                                  args.single_plan, [], False)

        if args.single_plan:
            if not args.local:
                specfile = list(Path(args.REPO).glob('*.spec'))[0]
                pkgname = str(specfile.with_suffix(''))
                planfile = plandir / specfile.with_suffix('.fmf')
                listfile = plandir / (pkgname + '.list')
            else:
                planfile = plandir / 'local.fmf'
                listfile = plandir / 'local.list'
            with listfile.open(mode='w') as fl:
                fl.write('# PACKAGE;FONT_ALIAS;FONT_LANG;FONT_WIDTH;'
                         'FONT_FAMILY;DEFAULT_SANS;DEFAULT_SERIF;DEFAULT_MONO;'
                         'DEFAULT_EMOJI;DEFAULT_MATH;FONT_LANG_EXCLUDE_FILES;'
                         'FONT_VALIDATE_EXCLUDE_FILES;FONT_CONF_EXCLUDE_FILES;'
                         'FONT_VALIDATE_INDEXES;\n')
                for ld in listdata:
                    fl.write(ld + '\n')
            generate_plan(planfile, True, True, args.add_prepare, pkgname,
                          None, None, [], False, True, pkglist,
                          not not args.local)

        print('Done. Update lang in the generated file(s) if needed')


if __name__ == '__main__':
    main()
