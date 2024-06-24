# Copyright (C) 2024 font-rpm-spec-generator Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Module to generate a test case based on tmt"""

import argparse
import glob
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
    parser.add_argument('-O', '--outputdir', help='Output directory')
    parser.add_argument('-v', '--verbose',
                        action='store_true', help='Show more detailed logs')
    parser.add_argument('REPO', default='.', help='Package repository path')

    args = parser.parse_args()

    if args.outputdir is None:
        args.outputdir = args.REPO
    if not shutil.which('fedpkg'):
        print('fedpkg is not installed')
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
            flist = []
            alist = []
            for f in s:
                if f.is_fontconfig():
                    has_fc_conf = True
                if f.families is not None:
                    flist += f.families
                if f.aliases is not None:
                    alist += f.aliases
            flist = list(set(flist))
            alist = list(set(alist))
            if len(flist) > 1 or len(alist) > 1:
                m([': ']).info(str(pkg)).warning('Generated file may not be correct').out()
            ss = subprocess.run(['rpm', '-qp', '--qf', '%{name}', str(pkg)], stdout=subprocess.PIPE)
            pkgname = ss.stdout.decode('utf-8')
            plandir = Path(args.outputdir) / 'plans'
            plandir.mkdir(exist_ok = True)
            planfile = plandir / (pkgname + '.fmf')
            m([': ']).info(str(planfile)).message('Generating...').out()
            with planfile.open(mode='w') as f:
                if not has_fc_conf:
                    disabled = """
                    exclude:
                      - generic_alias
                    """
                else:
                    disabled = ''
                f.write(f"""
summary: Fonts related tests
discover:
    how: fmf
    url: https://src.fedoraproject.org/tests/fonts
{disabled}execute:
    how: tmt
environment:
    PACKAGE: {pkgname}
    FONT_ALIAS: {alist[0]}
    FONT_FAMILY: {flist[0]}
    FONT_LANG: __LANG__
""")

        print('Done. Update lang in the generated file(s) if needed')

if __name__ == '__main__':
    main()
