# Copyright (C) 2024 font-rpm-spec-generator Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Module to generate a test case based on tmt"""

import argparse
import glob
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
import fontrpmspec.errors as err
from fontrpmspec.messages import Message as m
from fontrpmspec import sources as src


def generate_plan(planfile, has_fc_conf, has_lang, add_prepare, pkgname, alias, family, languages, warn):
    if warn:
        m([': ']).info(str(planfile)).warning('Generated file may not be correct').out()
    m([': ']).info(str(planfile)).message('Generating...').out()
    with planfile.open(mode='w') as f:
        if not has_fc_conf:
            disabled = """exclude:
    - generic_alias
"""
        else:
            disabled = ''
        if not has_lang:
            if not disabled:
                disabled = """exclude:
    - lang_coverage
"""
            else:
                disabled += '    - lang_coverage\n'
        if add_prepare:
            prepare = f"""prepare:
    name: tmt
    how: install
    package: {pkgname}
"""
        else:
            prepare = ''
        f.write(f"""summary: Fonts related tests
discover:
    how: fmf
    url: https://src.fedoraproject.org/tests/fonts
{disabled}{prepare}execute:
    how: tmt
environment:
    PACKAGE: {pkgname}
    FONT_ALIAS: {alias}
    FONT_FAMILY: {family}
    FONT_LANG: {','.join(languages) or 'not detected'}
""")

def main():
    """Endpoint function to generate tmt plans from RPM spec file"""
    parser = argparse.ArgumentParser(description='TMT plan generator',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--extra-buildopts', help='Extra buildopts to build package')
    parser.add_argument('-a', '--add-prepare',
                        action='store_true', help='Add prepare section for local testing')
    parser.add_argument('-O', '--outputdir', help='Output directory')
    parser.add_argument('-v', '--verbose',
                        action='store_true', help='Show more detailed logs')
    parser.add_argument('REPO', help='Package repository path')

    args = parser.parse_args()

    cwd = os.getcwd()
    if args.outputdir is None:
        args.outputdir = args.REPO
    if not shutil.which('fedpkg'):
        print('fedpkg is not installed')
        sys.exit(1)
    if not shutil.which('rpm'):
        print('rpm is not installed')
        sys.exit(1)
    if not shutil.which('fc-query'):
        print('fc-query is not installed')
        sys.exit(1)
    if not shutil.which('tmt'):
        print('tmt is not installed')
        sys.exit(1)

    cmd = ['tmt', 'init']
    if args.verbose:
        print('# ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=args.REPO)
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['fedpkg', 'local', '--define', '_rpmdir {}'.format(tmpdir)]
        if args.extra_buildopts:
            cmd.insert(1, args.extra_buildopts)
        if args.verbose:
            print('# ' + ' '.join(cmd))
        subprocess.run(cmd, cwd=args.REPO)
        for pkg in sorted((Path(tmpdir) / 'noarch').glob('*.rpm')):
            s = src.Source(str(pkg))
            has_fc_conf = False
            has_lang = False
            has_fonts = False
            is_ttc = False
            flist = []
            alist = []
            llist = []
            for f in s:
                if f.is_fontconfig():
                    has_fc_conf = True
                if f.is_font():
                    has_fonts = True
                    ss = subprocess.run(['fc-query', '-f', '%{lang}\n', f.fullname], stdout=subprocess.PIPE)
                    l = re.split(r'[,|]', ss.stdout.decode('utf-8'))
                    has_lang = len(l) > 0
                    if len(l) == 1:
                        llist = l
                if f.families is not None:
                    flist += f.families
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
            ss = subprocess.run(['rpm', '-qp', '--qf', '%{name}', str(pkg)], stdout=subprocess.PIPE)
            os.chdir(cwd)
            pkgname = ss.stdout.decode('utf-8')
            if not has_fonts:
                m([': ']).info(pkgname).message('Skipping. No tmt plan is needed.').out()
                continue
            plandir = Path(args.outputdir) / 'plans'
            plandir.mkdir(parents=True, exist_ok=True)
            planfile = plandir / (pkgname + '.fmf')
            if is_ttc:
                for fn in flist:
                    sub = fn.replace(flist[0], '').strip().lower()
                    name = pkgname + '.fmf' if not sub else pkgname + '_' + sub + '.fmf'
                    planfile = plandir / name
                    generate_plan(planfile, has_fc_conf, has_lang, args.add_prepare, pkgname, alist[0] if len(alist) > 0 else None, fn, llist, len(flist) > 1 or len(alist) > 1)
            else:
                generate_plan(planfile, has_fc_conf, has_lang, args.add_prepare, pkgname, alist[0] if len(alist) > 0 else None, flist[0] if len(flist) > 0 else None, llist, len(flist) > 1 or len(alist) > 1)

        print('Done. Update lang in the generated file(s) if needed')

if __name__ == '__main__':
    main()
