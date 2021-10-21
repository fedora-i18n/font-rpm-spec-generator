from re import template
from jinja2.filters import do_list
from jinja2 import Environment, FileSystemLoader
import os
from src_lib import font_meta_reader

def template_generator(fontfile):
    
    meta_data=font_meta_reader(fontfile)
    
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)
    template = dict()

    #spec file
    template[f"{meta_data['Font_Family'].lower()}-fonts.spec"] = env.get_template('font.spec').render(meta_data)
    #fontconfig file
    template[f"{meta_data['Font_Family'].lower()}-fontconfig.conf"] = env.get_template('fontconfig.conf').render(meta_data)
    #metainfo file
    template[f"{meta_data['Font_Family'].lower()}.metainfo.xml"] = env.get_template('font.metainfo.xml').render(meta_data)

    # Dir where all our spec and config file will be created
    draft_dir = os.path.join(os.getcwd(),"draft")
    
    for filename,data in template.items():
        with open(os.path.join(draft_dir,filename),"w") as fobj:
            fobj.writelines(data)