# setup.py
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

import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='fontrpmspec',
    description='Font packaging library in Fedora',
    long_description_content_type='text/markdown',
    long_description=long_description,
    version='0.1',
    license='GPLv3',
    author='Fedora I18N team',
    author_email='i18n@lists.fedoraproject.org',
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'fontrpmspec-conv=pyfontrpmspec.converter:main',
        ],
    },
    url='https://github.com/fedora-i18n/font-rpm-spec-generator',
    keywords='fedora fonts packaging',
    install_requires=[
        'fonttools',
        'jinja2',
        'termcolor',
    ],
)
