# Font RPM Spec Generator
[![pip version badge](https://img.shields.io/pypi/v/fontrpmspec)](https://pypi.org/project/fontrpmspec/)
[![tag badge](https://img.shields.io/github/v/tag/fedora-i18n/font-rpm-spec-generator)](https://github.com/fedora-i18n/font-rpm-spec-generator/tags)
[![license badge](https://img.shields.io/github/license/fedora-i18n/font-rpm-spec-generator)](./LICENSE)

This tool generates RPM [specfile](https://docs.fedoraproject.org/en-US/packaging-guidelines/FontsPolicy/) for a given font.

## setup & use
```
$ pip3 install build
$ python3 -m build
$ pip3 install --user dist/fontrpmspec*.whl
```

## usage

### fontrpmspec-gen
```
usage: fontrpmspec-gen [-h] [-f JSON_FILE] [-l LICENSE] [-o OUTPUT]
                       [--outputdir OUTPUTDIR] [--sourcedir SOURCEDIR]
                       [-s SOURCE] [-c CHANGELOG] [--email EMAIL]
                       [--username USERNAME] [--summary SUMMARY]
                       [--description DESCRIPTION]
                       [--common-description COMMON_DESCRIPTION] [-a ALIAS]
                       [--lang [LANG ...]] [--priority PRIORITY]
                       [--vf-priority VF_PRIORITY] [--foundry FOUNDRY]
                       [-e EXCLUDEPATH] [--rpmautospec | --no-rpmautospec]
                       [--autorelease-opt AUTORELEASE_OPT]
                       [--ignore-error [IGNORE_ERROR ...]]
                       NAME [VERSION] URL

Fonts RPM spec file generator against guidelines

positional arguments:
  NAME                  Package name
  VERSION               Package version (default: None)
  URL                   Project URL

options:
  -h, --help            show this help message and exit
  -f, --json-file JSON_FILE
                        Config file written in JSON (default: None)
  -l, --license LICENSE
                        License name of this project (default: OFL-1.1)
  -o, --output OUTPUT   Output file (default: -)
  --outputdir OUTPUTDIR
                        Output directory (default: .)
  --sourcedir SOURCEDIR
                        Source directory (default: .)
  -s, --source SOURCE   Source file (default: None)
  -c, --changelog CHANGELOG
                        Changelog entry (default: Initial import)
  --email EMAIL         email address to put into changelog (default:
                        tagoh@redhat.com)
  --username USERNAME   Real user name to put into changelog (default: Akira
                        TAGOH)
  --summary SUMMARY     Summary text for package (default: {family}, {alias}
                        typeface {type} font)
  --description DESCRIPTION
                        Package description (default: This package contains
                        {family} which is a {alias} typeface of {type} font.)
  --common-description COMMON_DESCRIPTION
                        Common package description. this is only used when
                        generating multi packages. (default: None)
  -a, --alias ALIAS     Set an alias name for family, such as sans-serif,
                        serif, monospace (default: auto)
  --lang [LANG ...]     Targetted language for a font (default: None)
  --priority PRIORITY   Number of Fontconfig config priority (default: 69)
  --vf-priority VF_PRIORITY
                        Number of Fontconfig config priority for variable font
                        (default: 68)
  --foundry FOUNDRY     Use this as foundry name instead of figuring out from
                        a font (default: None)
  -e, --excludepath EXCLUDEPATH
                        Exclude path from source archives (default: None)
  --rpmautospec, --no-rpmautospec
                        Use rpmautospec. (default: True)
  --autorelease-opt AUTORELEASE_OPT
                        Extra arguments to %autorelease. (default: None)
  --ignore-error [IGNORE_ERROR ...]
                        Deal with the specific error as warning (default:
                        None)
```

### fontrpmspec-conv
```
usage: fontrpmspec-conv [-h] [--foundry FOUNDRY] [--sourcedir SOURCEDIR]
                        [-o OUTPUT] [--ignore-error [IGNORE_ERROR ...]]
                        SPEC

Fonts RPM spec file converter against guidelines

positional arguments:
  SPEC                  Spec file to convert

options:
  -h, --help            show this help message and exit
  --foundry FOUNDRY     Use this as foundry name instead of figuring out from
                        a font. (default: None)
  --sourcedir SOURCEDIR
                        Source directory (default: .)
  -o, --output OUTPUT   Output file (default: -)
  --ignore-error [IGNORE_ERROR ...]
                        Deal with the specific error as warning (default:
                        None)
```

Note:
- You may need to update `BuildRequires` section as per your font requiremnts in your spec.
- Also update the `%build` section if your font uses some other build process.

### fontrpmspec-gentmt
```
usage: fontrpmspec-gentmt [-h] [--extra-buildopts EXTRA_BUILDOPTS] [-a] [-l [FILE]]
                          [-s] [-O OUTPUTDIR] [-v]
                          REPO

TMT plan generator

positional arguments:
  REPO                  Package repository path

options:
  -h, --help            show this help message and exit
  --extra-buildopts EXTRA_BUILDOPTS
                        Extra buildopts to build package (default: None)
  -a, --add-prepare     Add prepare section for local testing (default: False)
  -l, --local [FILE]    Generate a fmf file for local testing. `fedpkg local`
                        must be run before `tmt run` (default: False)
  -s, --single-plan     Generate single plan with list file (default: False)
  -O, --outputdir OUTPUTDIR
                        Output directory (default: None)
  -v, --verbose         Show more detailed logs (default: False)
```

Happy Packaging :)
