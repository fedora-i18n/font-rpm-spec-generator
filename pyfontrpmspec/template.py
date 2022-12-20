# template.py
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
"""Module to template a spec file."""

from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
from typing import Any


def get(npkgs: int, data: dict[str, Any]) -> str:
    """Generate a spec file from template."""
    try:
        ptempl = files('pyfontrpmspec.template').name()
    except TypeError:
        ptempl = files('pyfontrpmspec').joinpath('template')
    env = Environment(loader=FileSystemLoader(ptempl))
    template = {}

    if npkgs == 1:
        template['spec'] = env.get_template(
            'spectemplate-fonts-simple.spec').render(data)
    else:
        template['spec'] = env.get_template(
            'spectemplate-fonts-multi.spec').render(data)

    return template
