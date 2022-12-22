# font_reader.py
# Copyright (C) 2021-2022 Red Hat, Inc.
#
# Authors:
#   Vishal Vijayraghavan <vvijayra AT redhat DOT com>
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
"""Module to deal with font metadata."""

import re
from typing import Any
from fontTools.ttLib import TTFont
try:
    import _debugpath  # noqa: F401
except ModuleNotFoundError:
    pass
from pyfontrpmspec.messages import Message as m

NAME_TABLE = {
    0: 'CopyrightNotice',
    1: 'Font_Family',
    2: 'SubFamily',
    3: 'Unique_Font_Identifier',
    4: 'Full_Font_Name',
    5: 'Version',
    6: 'PostScript_Name',
    7: 'Trademark',
    8: 'Manufacturer_Name',
    9: 'Designer',
    10: 'Description',
    11: 'Vendor_URL',
    12: 'Designer_URL',
    13: 'License_Description',
    14: 'License_Info_URL',
    15: 'Reserved',
    16: 'Typographic_Family',
    17: 'Typographic_SubFamily',
    18: 'Compatible_Full',
    19: 'Sample_Text',
    20: 'PostScript_CID_Find_Fontname',
    21: 'WWS_Family_Name',
    22: 'WWS_SubFamily_Name',
    23: 'Light_Background_Pallete',
    24: 'Dark_Background_Pallete',
    25: 'Variations_PostScript_Name_Prefix'
}


def transform_foundry(id: str) -> str:
    """Transform 4-character foundry string to the human-readable string."""
    """
    4 letter characters from OS/2 table isn't hard to recognize what it is.
    particularly foundry property in macro affects the package name.
    mapping it to the human readable/recognizable name.
    """
    FOUNDARIES = {
        'ADBO': 'adobe',
        'MTY ': 'Motoya',
    }
    return FOUNDARIES[id] if id in FOUNDARIES else id


def font_meta_reader(fontfile: str, font_number: int = 0) -> dict[str, Any]:
    """Read metadata from `fontfile`."""
    meta_data = dict()
    font = TTFont(fontfile, fontNumber=font_number)
    # variable fmd denotes font meta data or fonts meta attributes
    for fmd in font['name'].names:
        if (fmd.platformID == 3
                and fmd.langID == 0x0409) or (fmd.platformID == 1
                                              and fmd.langID == 0):
            meta_data[NAME_TABLE.get(fmd.nameID, False)] = fmd.toStr()
    meta_data['foundry'] = transform_foundry(font['OS/2'].achVendID)
    meta_data['family'] = get_better_family(meta_data)
    meta_data[
        'type'] = 'OpenType' if font.sfntVersion == 'OTTO' else 'TrueType'
    fc = FontClass(fontfile, faceId=font_number)
    meta_data['alias'] = fc.get_alias_name()
    meta_data['hashint'] = True if 'prep' in font or 'cvt' in font else False
    return meta_data


def get_better_family(meta: dict[str, Any]) -> str:
    """Get better family name from metadata."""
    if 'WWS_Family_Name' in meta:
        family = meta['WWS_Family_Name']
    elif 'Typographic_Family' in meta:
        family = meta['Typographic_Family']
    else:
        family = meta['Font_Family']
    return family


def group(families: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Restructure metadata against related family names."""
    retval = {}
    x = sorted(families.items(), key=lambda x: len(x[1]['family']))
    for k, v in x:
        found = False
        for f in retval.keys():
            if re.fullmatch(r'{}'.format(f), v['family']):
                retval[v['family']].append({'fontinfo': v, 'file': k})
                found = True
        if not found:
            retval[v['family']] = [{'fontinfo': v, 'file': k}]
    return retval


class FontClass:
    """Classified font class."""

    TYPE_SANS_SERIF = 0
    TYPE_SERIF = 1
    TYPE_MONOSPACE = 2
    TYPE_CURSIVE = 3
    TYPE_FANTASY = 4
    TYPE_EMOJI = 5
    TYPE_MATH = 6
    TYPE_END = 7

    def __init__(self, fn: str, faceId: int = -1):
        """Initialize `FontClass`."""
        self.file = fn
        self.index = faceId

    def __get_type_id(self, n):
        return 1 << n

    def __guess_class(self):
        retval = 0
        tt = TTFont(self.file, fontNumber=self.index)
        os2 = tt['OS/2']
        cls_id = (os2.sFamilyClass >> 8) & 0xff
        subcls_id = os2.sFamilyClass & 0xff
        match cls_id:
            case 0 | 6 | 11 | 13 | 14:
                pass
            case 1:
                retval |= self.__get_type_id(FontClass.TYPE_SERIF)
                if subcls_id == 8:
                    retval |= self.__get_type_id(FontClass.TYPE_CURSIVE)
            case 2 | 3:
                retval |= self.__get_type_id(FontClass.TYPE_SERIF)
                if subcls_id == 2:
                    retval |= self.__get_type_id(FontClass.TYPE_CURSIVE)
            case 4 | 5 | 7:
                retval |= self.__get_type_id(FontClass.TYPE_SERIF)
            case 8:
                retval |= self.__get_type_id(FontClass.TYPE_SANS_SERIF)
            case 9 | 12:
                retval |= self.__get_type_id(FontClass.TYPE_FANTASY)
            case 10:
                retval |= self.__get_type_id(FontClass.TYPE_CURSIVE)
            case _:
                m([':', ': ']).info(self.file).info(self.index).warning(
                    'Unknown sFamilyClass class ID: {}'.format(cls_id)).out()
        ft = os2.panose.bFamilyType
        ss = os2.panose.bSerifStyle
        pp = os2.panose.bProportion
        if ft == 3:
            retval |= self.__get_type_id(FontClass.TYPE_CURSIVE)
        elif ft >= 4 and ft <= 5:
            retval |= self.__get_type_id(FontClass.TYPE_FANTASY)
        elif ft == 2 and ((ss >= 11 and ss <= 13) or ss == 15):
            retval |= self.__get_type_id(FontClass.TYPE_SANS_SERIF)
        elif ft == 1:
            pass
        elif ft == 0 and ss == 1:
            pass
        else:
            retval |= self.__get_type_id(FontClass.TYPE_SERIF)
        if (ft == 2 and pp == 9) or (ft == 3 and pp == 3) or (
                ft == 4 and pp == 9) or (ft == 5 and pp == 3):
            retval |= self.__get_type_id(FontClass.TYPE_MONOSPACE)

        return retval

    def get_alias_name(self) -> list[str]:
        """Get alias name corresponding to the font."""
        alias = [
            'sans-serif', 'serif', 'monospace', 'cursive', 'fantasy', 'emoji',
            'math'
        ]
        id = self.__guess_class()
        retval = []
        if id == 0:
            return ''
        for i in range(FontClass.TYPE_END):
            if (id & self.__get_type_id(i)) == self.__get_type_id(i):
                retval.append(alias[i])

        return retval
