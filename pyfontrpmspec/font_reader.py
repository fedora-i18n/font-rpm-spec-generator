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

import re
from fontTools.ttLib import TTFont

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
    
def transform_foundry(id):
    '''
    4 letter characters from OS/2 table isn't hard to recognize what it is.
    particularly foundry property in macro affects the package name.
    mapping it to the human readable/recognizable name.
    '''
    FOUNDARIES = {
        'ADBO': 'adobe',
        'MTY ': 'Motoya',
    }
    return FOUNDARIES[id] if id in FOUNDARIES else id

def font_meta_reader(fontfile, font_number = 0):
    meta_data = dict()
    font = TTFont(fontfile, fontNumber = font_number)
    # variable fmd denotes font meta data or fonts meta attributes
    for fmd in font['name'].names:
        if (fmd.platformID == 3 and fmd.langID == 0x0409) or (fmd.platformID == 1 and fmd.langID == 0):
            meta_data[NAME_TABLE.get(fmd.nameID, False)] = fmd.toStr()
    meta_data['foundry'] = transform_foundry(font['OS/2'].achVendID)
    meta_data['family'] = get_better_family(meta_data)
    return meta_data

def get_better_family(meta):
    if 'WWS_Family_Name' in meta:
        family = meta['WWS_Family_Name']
    elif 'Typographic_Family' in meta:
        family = meta['Typographic_Family']
    else:
        family = meta['Font_Family']
    return family

def group(families):
    retval = {}
    x = sorted(families.items(), key=lambda x: len(x[1]['family']))
    for k, v in x:
        found = False
        for f in retval.keys():
            if re.match(r'{}'.format(f), v['family']):
                retval[v['family']].append({'fontinfo': v, 'file': k})
                found = True
        if not found:
            retval[v['family']] = [{'fontinfo': v, 'file': k}]
    return retval

if __name__ == "__main__":
    fontfile = "/home/vvijayra/git_projects/liberation-fonts/liberation-fonts-ttf-2.1.5/LiberationSans-Bold.ttf"
    print(font_meta_reader(fontfile))
