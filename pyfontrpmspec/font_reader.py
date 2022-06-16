from fontTools.ttLib import TTFont
import sys
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
    
    
def font_meta_reader(fontfile):
    meta_data = dict()
    try:
        font = TTFont(fontfile)
        # variable fmd denotes font meta data or fonts meta attributes
        for fmd in font['name'].names:
            if (fmd.platformID == 3 and fmd.langID == 0x0409) or (fmd.platformID == 1 and fmd.langID == 0):
                meta_data[NAME_TABLE.get(fmd.nameID, False)] = fmd.toStr()
        return meta_data
    except FileNotFoundError:
        print("invalid font file path")
        sys.exit(1)

if __name__ == "__main__":
    fontfile = "/home/vvijayra/git_projects/liberation-fonts/liberation-fonts-ttf-2.1.5/LiberationSans-Bold.ttf"
    print(font_meta_reader(fontfile))
