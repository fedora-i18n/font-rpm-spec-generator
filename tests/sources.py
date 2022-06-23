# sources.py
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

from pathlib import Path
import unittest
import sys
sys.path.append(str(Path(__file__).parents[1]))
from pyfontrpmspec import sources as src

class TestSource(unittest.TestCase):

    def setUp(self):
        self.license_from_source = src.Source('LICENSE.txt', '/path/to/source')
        self.doc_from_source = src.Source('README.txt', '/path/to/source')
        self.font_from_source = src.Source('foo.ttf', '/path/to/source')
        self.font_from_web = src.Source('http://example.com/foo.ttf', '/path/to/source')
        self.font_from_web_frag = src.Source('http://example.com/foo.ttf#/bar.ttf', '/path/to/source')
        self.font_from_web_query = src.Source('http://android.git.kernel.org/?p=platform/frameworks/base.git;a=blob_plain;f=data/fonts/MTLc3m.ttf', '/path/to/source')
        self.fc_from_source = src.Source('foo.conf', '/path/to/source')
        self.archive_from_source = src.Source('foo.zip', '/path/to/source')
        self.archive_from_web = src.Source('http://example.com/foo.zip', '/path/to/source')
        self.archive_from_web_frag = src.Source('http://example.com/foo#/bar.zip', '/path/to/source')

    def test_name(self):
        self.assertEqual(self.license_from_source.name, 'LICENSE.txt')
        self.assertEqual(self.doc_from_source.name, 'README.txt')
        self.assertEqual(self.font_from_source.name, 'foo.ttf')
        self.assertEqual(self.font_from_web.name, 'foo.ttf')
        self.assertEqual(self.font_from_web_frag.name, 'bar.ttf')
        self.assertEqual(self.font_from_web_query.name, 'MTLc3m.ttf')
        self.assertEqual(self.fc_from_source.name, 'foo.conf')
        self.assertEqual(self.archive_from_source.name, 'foo.zip')
        self.assertEqual(self.archive_from_web.name, 'foo.zip')
        self.assertEqual(self.archive_from_web_frag.name, 'bar.zip')

    def test_realname(self):
        self.assertEqual(self.license_from_source.realname, 'LICENSE.txt')
        self.assertEqual(self.doc_from_source.realname, 'README.txt')
        self.assertEqual(self.font_from_source.realname, 'foo.ttf')
        self.assertEqual(self.font_from_web.realname, 'http://example.com/foo.ttf')
        self.assertEqual(self.font_from_web_frag.realname, 'http://example.com/foo.ttf#/bar.ttf')
        self.assertEqual(self.font_from_web_query.realname, 'http://android.git.kernel.org/?p=platform/frameworks/base.git;a=blob_plain;f=data/fonts/MTLc3m.ttf')
        self.assertEqual(self.fc_from_source.realname, 'foo.conf')
        self.assertEqual(self.archive_from_source.realname, 'foo.zip')
        self.assertEqual(self.archive_from_web.realname, 'http://example.com/foo.zip')
        self.assertEqual(self.archive_from_web_frag.realname, 'http://example.com/foo#/bar.zip')

    def test_fullname(self):
        self.assertEqual(self.license_from_source.fullname, '/path/to/source/LICENSE.txt')
        self.assertEqual(self.doc_from_source.fullname, '/path/to/source/README.txt')
        self.assertEqual(self.font_from_source.fullname, '/path/to/source/foo.ttf')
        self.assertEqual(self.font_from_web.fullname, '/path/to/source/foo.ttf')
        self.assertEqual(self.font_from_web_frag.fullname, '/path/to/source/bar.ttf')
        self.assertEqual(self.font_from_web_query.fullname, '/path/to/source/MTLc3m.ttf')
        self.assertEqual(self.fc_from_source.fullname, '/path/to/source/foo.conf')
        self.assertEqual(self.archive_from_source.fullname, '/path/to/source/foo.zip')
        self.assertEqual(self.archive_from_web.fullname, '/path/to/source/foo.zip')
        self.assertEqual(self.archive_from_web_frag.fullname, '/path/to/source/bar.zip')

class TestFile(unittest.TestCase):

    def setUp(self):
        self.license_from_source = src.File('LICENSE.txt', '/path/to/source', True)
        self.doc_from_source = src.File('README.txt', '/path/to/source', True)
        self.doc_from_archive = src.File('./README.md', '/tmp/foo', False)
        self.doc_from_archive_sub = src.File('foo-1.0/README.md', '/tmp/foo', False)
        self.font_from_source = src.File('foo.ttf', '/path/to/source', True)
        self.font_from_web = src.File('http://example.com/baz/foo.ttf', '/path/to/source', True)
        self.font_from_web_frag = src.File('http://example.com/foo.ttf#/bar.ttf', '/path/to/source', True)
        self.font_from_web_query = src.File('http://android.git.kernel.org/?p=platform/frameworks/base.git;a=blob_plain;f=data/fonts/MTLc3m.ttf', '/path/to/source', True)
        self.font_from_archive = src.File('ttf/foo.ttf', '/tmp/foo', False)
        self.font_from_archive_sub = src.File('foo-1.0/ttf/foo.ttf', '/tmp/foo', False)
        self.fc_from_source = src.File('foo.conf', '/path/to/source', True)

    def test_name(self):
        self.assertEqual(self.license_from_source.name, 'LICENSE.txt')
        self.assertEqual(self.doc_from_source.name, 'README.txt')
        self.assertEqual(self.doc_from_archive.name, 'README.md')
        self.assertEqual(self.doc_from_archive_sub.name, 'README.md')
        self.assertEqual(self.font_from_source.name, 'foo.ttf')
        self.assertEqual(self.font_from_web.name, 'foo.ttf')
        self.assertEqual(self.font_from_web_frag.name, 'bar.ttf')
        self.assertEqual(self.font_from_web_query.name, 'MTLc3m.ttf')
        self.assertEqual(self.font_from_archive.name, 'foo.ttf')
        self.assertEqual(self.font_from_archive_sub.name, 'ttf/foo.ttf')
        self.assertEqual(self.fc_from_source.name, 'foo.conf')

    def test_realname(self):
        self.assertEqual(self.license_from_source.realname, 'LICENSE.txt')
        self.assertEqual(self.doc_from_source.realname, 'README.txt')
        self.assertEqual(self.doc_from_archive.realname, './README.md')
        self.assertEqual(self.doc_from_archive_sub.realname, 'foo-1.0/README.md')
        self.assertEqual(self.font_from_source.realname, 'foo.ttf')
        self.assertEqual(self.font_from_web.realname, 'http://example.com/baz/foo.ttf')
        self.assertEqual(self.font_from_web_frag.realname, 'http://example.com/foo.ttf#/bar.ttf')
        self.assertEqual(self.font_from_web_query.realname, 'http://android.git.kernel.org/?p=platform/frameworks/base.git;a=blob_plain;f=data/fonts/MTLc3m.ttf')
        self.assertEqual(self.font_from_archive.realname, 'ttf/foo.ttf')
        self.assertEqual(self.font_from_archive_sub.realname, 'foo-1.0/ttf/foo.ttf')
        self.assertEqual(self.fc_from_source.realname, 'foo.conf')

    def test_fullname(self):
        self.assertEqual(self.license_from_source.fullname, '/path/to/source/LICENSE.txt')
        self.assertEqual(self.doc_from_source.fullname, '/path/to/source/README.txt')
        self.assertEqual(self.doc_from_archive.fullname, '/tmp/foo/README.md')
        self.assertEqual(self.doc_from_archive_sub.fullname, '/tmp/foo/foo-1.0/README.md')
        self.assertEqual(self.font_from_source.fullname, '/path/to/source/foo.ttf')
        self.assertEqual(self.font_from_web.fullname, '/path/to/source/foo.ttf')
        self.assertEqual(self.font_from_web_frag.fullname, '/path/to/source/bar.ttf')
        self.assertEqual(self.font_from_web_query.fullname, '/path/to/source/MTLc3m.ttf')
        self.assertEqual(self.font_from_archive.fullname, '/tmp/foo/ttf/foo.ttf')
        self.assertEqual(self.font_from_archive_sub.fullname, '/tmp/foo/foo-1.0/ttf/foo.ttf')
        self.assertEqual(self.fc_from_source.fullname, '/path/to/source/foo.conf')

    def test_prefix(self):
        self.assertEqual(self.license_from_source.prefix, '/path/to/source')
        self.assertEqual(self.doc_from_source.prefix, '/path/to/source')
        self.assertEqual(self.doc_from_archive.prefix, '/tmp/foo')
        self.assertEqual(self.doc_from_archive_sub.prefix, '/tmp/foo')
        self.assertEqual(self.font_from_source.prefix, '/path/to/source')
        self.assertEqual(self.font_from_web.prefix, '/path/to/source')
        self.assertEqual(self.font_from_web_frag.prefix, '/path/to/source')
        self.assertEqual(self.font_from_web_query.prefix, '/path/to/source')
        self.assertEqual(self.font_from_archive.prefix, '/tmp/foo')
        self.assertEqual(self.font_from_archive_sub.prefix, '/tmp/foo')
        self.assertEqual(self.fc_from_source.prefix, '/path/to/source')

    def test_is_license(self):
        self.assertEqual(self.license_from_source.is_license(), True)
        self.assertEqual(self.doc_from_source.is_license(), False)
        self.assertEqual(self.doc_from_archive.is_license(), False)
        self.assertEqual(self.doc_from_archive_sub.is_license(), False)
        self.assertEqual(self.font_from_source.is_license(), False)
        self.assertEqual(self.font_from_web.is_license(), False)
        self.assertEqual(self.font_from_web_frag.is_license(), False)
        self.assertEqual(self.font_from_web_query.is_license(), False)
        self.assertEqual(self.font_from_archive.is_license(), False)
        self.assertEqual(self.font_from_archive_sub.is_license(), False)
        self.assertEqual(self.fc_from_source.is_license(), False)

    def test_is_doc(self):
        self.assertEqual(self.license_from_source.is_doc(), True)
        self.assertEqual(self.doc_from_source.is_doc(), True)
        self.assertEqual(self.doc_from_archive.is_doc(), True)
        self.assertEqual(self.doc_from_archive_sub.is_doc(), True)
        self.assertEqual(self.font_from_source.is_doc(), False)
        self.assertEqual(self.font_from_web.is_doc(), False)
        self.assertEqual(self.font_from_web_frag.is_doc(), False)
        self.assertEqual(self.font_from_web_query.is_doc(), False)
        self.assertEqual(self.font_from_archive.is_doc(), False)
        self.assertEqual(self.font_from_archive_sub.is_doc(), False)
        self.assertEqual(self.fc_from_source.is_doc(), False)

    def test_is_font(self):
        self.assertEqual(self.license_from_source.is_font(), False)
        self.assertEqual(self.doc_from_source.is_font(), False)
        self.assertEqual(self.doc_from_archive.is_font(), False)
        self.assertEqual(self.doc_from_archive_sub.is_font(), False)
        self.assertEqual(self.font_from_source.is_font(), True)
        self.assertEqual(self.font_from_web.is_font(), True)
        self.assertEqual(self.font_from_web_frag.is_font(), True)
        self.assertEqual(self.font_from_web_query.is_font(), True)
        self.assertEqual(self.font_from_archive.is_font(), True)
        self.assertEqual(self.font_from_archive_sub.is_font(), True)
        self.assertEqual(self.fc_from_source.is_font(), False)

    def test_is_fontconfig(self):
        self.assertEqual(self.license_from_source.is_fontconfig(), False)
        self.assertEqual(self.doc_from_source.is_fontconfig(), False)
        self.assertEqual(self.doc_from_archive.is_fontconfig(), False)
        self.assertEqual(self.doc_from_archive_sub.is_fontconfig(), False)
        self.assertEqual(self.font_from_source.is_fontconfig(), False)
        self.assertEqual(self.font_from_web.is_fontconfig(), False)
        self.assertEqual(self.font_from_web_frag.is_fontconfig(), False)
        self.assertEqual(self.font_from_web_query.is_fontconfig(), False)
        self.assertEqual(self.font_from_archive.is_fontconfig(), False)
        self.assertEqual(self.font_from_archive_sub.is_fontconfig(), False)
        self.assertEqual(self.fc_from_source.is_fontconfig(), True)

    def test_is_source(self):
        self.assertEqual(self.license_from_source.is_source(), True)
        self.assertEqual(self.doc_from_source.is_source(), True)
        self.assertEqual(self.doc_from_archive.is_source(), False)
        self.assertEqual(self.doc_from_archive_sub.is_source(), False)
        self.assertEqual(self.font_from_source.is_source(), True)
        self.assertEqual(self.font_from_web.is_source(), True)
        self.assertEqual(self.font_from_web_frag.is_source(), True)
        self.assertEqual(self.font_from_web_query.is_source(), True)
        self.assertEqual(self.font_from_archive.is_source(), False)
        self.assertEqual(self.font_from_archive_sub.is_source(), False)
        self.assertEqual(self.fc_from_source.is_source(), True)

if __name__ == '__main__':
    unittest.main()
