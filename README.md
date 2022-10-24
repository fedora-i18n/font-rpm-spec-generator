# Font RPM Spec Generator
This tool generates RPM [specfile](https://docs.fedoraproject.org/en-US/packaging-guidelines/FontsPolicy/) for a given font.

## setup & use
```
$ python3 -m build
$ pip3 install --user dist/fontrpmspec*.whl
```

## usage
```
usage: main.py  [options]

Font packaging tool

options:
  -h, --help                      	  Show this help message and exit
  -D DIR, --dir DIR          	  Font dir path
  -l LANG, --lang LANG		Specify lang which fontfile comply
  -d DESCRIPTION, --description DESCRIPTION
                        					Description of your fontfile
  -s SUMMARY, --summary SUMMARY
                        					short summary of your fontfile
  -u URL, --url URL     	 	Font Project URL
  -S SOURCE, --source SOURCE
                        					Font source tar or path
```

### fontrpmspec-conv
```
usage: fontrpmspec-conv [-h] [--sourcedir SOURCEDIR] [-o OUTPUT] SPEC

Fonts RPM spec file converter against guidelines

positional arguments:
  SPEC                  Spec file to convert

options:
  -h, --help            show this help message and exit
  --sourcedir SOURCEDIR
                        Source directory (default: .)
  -o OUTPUT, --output OUTPUT
                        Output file (default: -)
```

Note:
- Tool will generate all required (.spec, .config, .metainfo.xml) files in draft dir of the project.
- You may need to update `BuildRequires` section as per your font requiremnts in your spec.
- Also update the `%build` section if your font uses some other build process.

Happy Packaging :)
