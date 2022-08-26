# Packaging template: multi-family fonts packaging.
#
# SPDX-License-Identifier: MIT
#
# This template documents spec declarations, used when packaging multiple font
# families, from a single dedicated source archive. The source rpm is named
# after the first (main) font family). Look up “fonts-3-sub” when the source
# rpm needs to be named some other way.
#
# It is part of the following set of packaging templates:
# “fonts-0-simple”: basic single-family fonts packaging
# “fonts-1-full”:   less common patterns for single-family fonts packaging
# “fonts-2-multi”:  multi-family fonts packaging
# “fonts-3-sub”:    packaging fonts, released as part of something else
#
Version: {{ version }}
Release: {{ release }}
URL:     {{ url }}
BuildRequires: fonts-rpm-macros >= 1:2.0.5-9

# The following declarations will be aliased to [variable]0 and reused for all
# generated *-fonts packages unless overriden by a specific [variable][number]
# declaration.
%global foundry           {{ foundry }}
%global fontlicense       {{ license }}
%global fontlicenses      {{ license_file }}
%global fontdocs          {{ docs }}
%global fontdocsex        %{fontlicenses}

# A text block that can be reused as part of the description of each generated
# subpackage.
%global common_description %{expand:
}

# Declaration for the subpackage containing the first font family. Also used as
# source rpm info. All the [variable]0 declarations are equivalent and aliased
# to [variable].
{% for n in range(fonts| length) %}
%global fontfamily{{ n }}       {{ fonts[n]['family'] }}
%global fontsummary{{ n }}      {{ fonts[n]['summary'] }}
%global fontpkgheader{{ n }}    %{expand:
}
%global fonts{{ n }}            {{ fonts[n]['fonts'] }}
%global fontsex{{ n }}          {{ fonts[n]['exfonts'] }}
%global fontconfs{{ n }}        %{SOURCE{{ fonts[n]['conf'] }}}
%global fontconfsex{{ n }}      {{ fonts[n]['exconf'] }}
%global fontdescription{{ n }}  %{expand:
%{common_description}
{{ fonts[n]['description'] }}
}
{% endfor %}

Source0:  {{ source }}{% for n in range(fonts| length) %}
Source{{ n + 10 }}: {{ fontconfig[n] }}{% endfor %}{% for s in exsources %}
Source{{ nsources[s] }}: {{ s }}{% endfor %}{% set n = [0] %}{% for s in patches %}
Patch{{ n[0] }}:   {{ s }}{% set _ = n.append(n[0] + 1) %}{% set _ = n.pop(0) %}{% endfor %}

# “fontpkg” will generate the font subpackage headers corresponding to the
# elements declared above.
# “fontpkg” accepts the following selection arguments:
# – “-a”          process everything
# – “-z [number]” process a specific declaration block
# If no flag is specified it will only process the zero/nosuffix block.
%fontpkg -a

# “fontmetapkg” will generate a font meta(sub)package header for all the font
# subpackages generated in this spec. Optional arguments:
# – “-n [name]”      use [name] as metapackage name
# – “-s [variable]”  use the content of [variable] as metapackage summary
# – “-d [variable]”  use the content of [variable] as metapackage description
# – “-z [numbers]”   restrict metapackaging to [numbers] comma-separated list
#                    of font package suffixes
%fontmetapkg

%prep
%setup -q {{ setup }}{% if copy_source %}
cp %{SOURCE0} .{% endif %}{% for s in exsources %}
cp %{SOURCE{{ nsources[s] }}} .{% endfor %}

%build
# “fontbuild” accepts the usual selection arguments:
# – “-a”          process everything
# – “-z [number]” process a specific declaration block
# If no flag is specified it will only process the zero/nosuffix block.
%fontbuild -a

%install
# “fontinstall” accepts the usual selection arguments:
# – “-a”          process everything
# – “-z [number]” process a specific declaration block
# If no flag is specified it will only process the zero/nosuffix block.
%fontinstall -a

%check
# “fontcheck” accepts the usual selection arguments:
# – “-a”          process everything
# – “-z [number]” process a specific declaration block
# If no flag is specified it will only process the zero/nosuffix block.
%fontcheck -a

# “fontfiles” accepts the usual selection arguments:
# – “-a”          process everything
# – “-z [number]” process a specific declaration block
# If no flag is specified it will only process the zero/nosuffix block
%fontfiles -a

%changelog
{{ changelog }}
