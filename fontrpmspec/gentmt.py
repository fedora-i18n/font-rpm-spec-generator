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
            flist = []
            alist = []
            llist = []
            for f in s:
                if f.is_fontconfig():
                    has_fc_conf = True
                if f.is_font():
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
            flist = list(set(flist))
            alist = list(set(alist))
            llist = list(set(llist))
            if len(flist) > 1 or len(alist) > 1:
                m([': ']).info(str(pkg)).warning('Generated file may not be correct').out()
            ss = subprocess.run(['rpm', '-qp', '--qf', '%{name}', str(pkg)], stdout=subprocess.PIPE)
            os.chdir(cwd)
            pkgname = ss.stdout.decode('utf-8')
            plandir = Path(args.outputdir) / 'plans'
            plandir.mkdir(parents=True, exist_ok=True)
            planfile = plandir / (pkgname + '.fmf')
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
                if args.add_prepare:
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
    FONT_ALIAS: {alist[0]}
    FONT_FAMILY: {flist[0]}
    FONT_LANG: {','.join(llist) or 'not detected'}
""")

        print('Done. Update lang in the generated file(s) if needed')

if __name__ == '__main__':
    main()
