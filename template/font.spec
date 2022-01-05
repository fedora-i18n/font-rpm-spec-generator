Version:	{{ Version }}
Release:	0%{?dist}
URL:		{{ url }}
%global	fontname	{{ Font_Family }}
%global	foundry	{{ Manufacturer_Name }}
%global	fontlicense	{{ License_Description }}
%global fontlicenses {{ License_file }}
%global fontdocs {{ font_docs }}
%global	fontfamily	{{ Font_Family }}    
%global	fonts	{{ font_binary_path }}
%global	fontconfs	%{SOURCE1}
%global	fontdescription	%{expand:	
{{ description }} .}

Source0:	{{ source }}
Source1:	%{fontname}.fontconfig.conf
Source2:	%{fontname}.metainfo.xml
BuildRequires: 	make
BuildRequires:	fontpackages-devel
BuildRequires:	libappstream-glib
BuildRequires:	fontforge-devel
BuildRequires:	python3
BuildRequires:	python3-fonttools
Requires:	fontpackages-filesystem


%fontpkg

%patchlist

%prep
%autosetup -n meera-Version%{version}
chmod 644 *.txt
rm -rf ttf

%build 
make PY=python3
%fontbuild


%install
%fontinstall

%check	
%fontcheck

%fontfiles

%changelog
* Thu Dec 09 2021 Vishal Vijayraghavan <vishalvijayraghavan@gmail.com> - {{ Version }}-0
- first update spec release of smc-meera fonts