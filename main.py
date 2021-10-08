from re import template
from jinja2.filters import do_list
import fontforge as ff
from fontTools.ttLib import TTFont
import sys, os, json
from jinja2 import Environment, FileSystemLoader

fontfile = '/usr/share/fonts/smc-meera/Meera-Regular.ttf'

def main():
    
    with open('template/config.json') as fobj:
        font_meta_data = json.load(fobj)

    font = ff.open(fontfile)
    font_meta_data["fontName"] = font.fontname
    font_meta_data["fontFamily"] = font.familyname
    font_meta_data["fontVersion"] = font.version
    
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)
    template = dict()

    template[f"{font_meta_data['fontName'].lower()}-fonts.spec"] = env.get_template('font.spec').render(font_meta_data)
    template[f"{font_meta_data['fontName'].lower()}-fontconfig.conf"] = env.get_template('fontconfig.conf').render(font_meta_data)
    template[f"{font_meta_data['fontName'].lower()}.metainfo.xml"] = env.get_template('font.metainfo.xml').render(font_meta_data)

    draft_dir = os.path.join(os.getcwd(),"draft")
    
    for filename,data in template.items():
        with open(os.path.join(draft_dir,filename),"w") as fobj:
            fobj.writelines(data)
    
if __name__ == "__main__":
    main()