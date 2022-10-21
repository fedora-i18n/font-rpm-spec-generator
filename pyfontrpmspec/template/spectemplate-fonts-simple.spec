# Packaging template: basic single-family fonts packaging.
#
# SPDX-License-Identifier: MIT
#
# This template documents the minimal set of spec declarations, necessary to
# package a single font family, from a single dedicated source archive.
#
# It is part of the following set of packaging templates:
# “fonts-0-simple”: basic single-family fonts packaging
# “fonts-1-full”:   less common patterns for single-family fonts packaging
# “fonts-2-multi”:  multi-family fonts packaging
# “fonts-3-sub”:    packaging fonts, released as part of something else
#
# A font family is composed of font files, that share a single design, and
# differ ONLY in:
# — Weight        Bold, Black…
# – Width∕Stretch Narrow, Condensed, Expanded…
# — Slope/Slant   Italic, Oblique
# Optical sizing  Caption…
#
# Those parameters correspond to the default axes of OpenType variable fonts:
# https://docs.microsoft.com/en-us/typography/opentype/spec/dvaraxisreg#registered-axis-tags
# The variable fonts model is an extension of the WWS model described in the
# WPF Font Selection Model whitepaper (2007):
# https://msdnshared.blob.core.windows.net/media/MSDNBlogsFS/prod.evol.blogs.msdn.com/CommunityServer.Components.PostAttachments/00/02/24/90/36/WPF%20Font%20Selection%20Model.pdf
#
# Do not rely on the naming upstream chose, to define family boundaries, it
# will often be wrong.
#
# Declaration order is chosen to limit divergence between those templates, and
# simplify cut and pasting.
#
Version: {{ version }}
Release: {{ release }}
URL:     {{ url }}
BuildRequires: fonts-rpm-macros >= 1:2.0.5-9

# The identifier of the entity, that released the font family.
%global foundry           {{ foundry }}
# The font family license identifier. Adjust as necessary. The OFL is our
# recommended font license.
%global fontlicense       {{ license }}
#
# The following directives are lists of space-separated shell globs
#   – matching files associated with the font family,
#   – as they exist in the build root,
#   — at the end of the %build stage:
# – legal files (licensing…)
%global fontlicenses      {{ license_file }}
# – documentation files
%global fontdocs          {{ docs }}
# – exclusions from the ”fontdocs” list
%global fontdocsex        %{fontlicenses}

# The human-friendly font family name, whitespace included, restricted to the
# the Basic Latin Unicode block.
%global fontfamily        {{ family }}
%global fontsummary       {{ summary }}
#
# More shell glob lists:
# – font family files
%global fonts             {{ fonts }}
# – fontconfig files
%global fontconfs         %{SOURCE10}
#
# A multi-line description block for the generated package.
%global fontdescription   %{expand:
{{ description }}
}

# {{ origsource }}
Source0:  {{ source }}
# Adjust as necessary. Keeping the filename in sync with the package name is a good idea.
# See the fontconfig templates in fonts-rpm-templates for information on how to
# write good fontconfig files and choose the correct priority [number].
Source10: {{ fontconfig }}{% for s in exsources %}
Source{{ nsources[s] }}: {{ s }}{% endfor %}{% set n = [0] %}{% for s in patches %}
Patch{{ n[0] }}: {{ s }}{% set _ = n.append(n[0] + 1) %}{% set _ = n.pop(0) %}{% endfor %}

%fontpkg

%prep
%setup -q {{ setup }}{% if copy_source %}
cp %{SOURCE0} .{% endif %}{% for s in exsources %}
cp %{SOURCE{{ nsources[s] }}} .{% endfor %}

%build
%fontbuild

%install
%fontinstall

%check
%fontcheck

%fontfiles

%changelog
{{ changelog }}
