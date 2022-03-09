import os
import fnmatch, functools, itertools
from re import split, template
import sys
from jinja2.filters import do_list
from jinja2 import Environment, FileSystemLoader
from src_lib import *

# https://fedoraproject.org/wiki/Licensing:Main?rd=Licensing#Font_Licenses
LICENSES = {
    "SIL Open Font License":"OFL",
    "Adobe/TUG Utopia license agreement":"Utopia",
    "AMS Bluesky Font License":"AMS",
    "Arphic Public License":"Arphic",
    "Atkinson Hyperlegible Font License":"AHFL",
    "Baekmuk License":"Baekmuk",
    "Bitstream Vera Font License":"Bitstream Vera",
    "Charter License":"Charter",
    "Creative Commons Attribution license":"CC-BY",
    "DoubleStroke Font License":"DoubleStroke",
    "ec Font License":"ec",
    "Elvish Font License":"Elvish",
    "GUST Font License":"LPPL",
    "Hack Open Font License":"HOFL",
    "Hershey Font License":"Hershey",
    "IPA Font License":"IPA",
    "Liberation Font License":"Liberation",
    "LaTeX Project Public License":"LPPL",
    "Lucida Legal Notice":"Lucida",
    "MgOpen Font License":"MgOpen",
    "mplus Font License":"mplus",
    "ParaType Font License":"PTFL",
    "Punknova Font License":"Punknova",
    "STIX Fonts User License":"STIX",
    "TTYP0 License":"MIT",
    "Wadalab Font License":"Wadalab",
    "XANO Mincho Font License":"XANO",  
}

class TemplateGenerator:

    def metadata_cleaner(self, metadata, inputdata):
        '''
        parse the font metadata and clean
        '''
        #version validation
        metadata['Version'] = metadata['Version'].removeprefix("Version ")
        
        #license validation
        for key,val in LICENSES.items():
            if key in metadata['License_Description'] or key in metadata['License_Info_URL']:
                metadata['License_Description'] = LICENSES[key]

        for input,value in inputdata.items():
            if input not in metadata.keys():
                metadata[input] = value
        
        return metadata

    def template_generator(self, input_data):
        '''
        spec, fontconfig & metainfo file generator using jinja templating
        '''
        meta_data = None

        if 'dir' in input_data.keys() and input_data['dir'] != None:
            fontfile_paths = self.findfiles(pattern=["*.ttf","*.otf"], path=input_data['dir'],getabs=True)
            for fontfile in fontfile_paths: 
                meta_data = font_meta_reader(fontfile)
        
        elif 'file' in input_data.keys() and input_data['file'] != None:
            meta_data = font_meta_reader(input_data['file'])
        else:
            print("Error: No fontfile passed in config or as cli argument")
            sys.exit(1)

        meta_data = self.metadata_cleaner(meta_data, input_data)

        # get file paths for readme, license , doc & etc
        meta_data['License_file'] = self.findfiles(pattern=["LICENSE","OFL.txt"], path=meta_data['dir'])[0] 
        meta_data['font_docs'] = " ".join(self.findfiles(pattern=["README.md","README.rst","*.pdf","*.docs"], path=meta_data['dir']))
        fontfile_paths = self.findfiles(pattern=["*.ttf","*.otf"], path=meta_data['dir'],getabs=True)
        font_bin_path = set()
        for font_file in fontfile_paths:
            if font_file.endswith(".ttf"):
                font_bin_path.add(os.path.dirname(font_file)+"/*.ttf")
            elif font_file.endswith(".otf"):
                font_bin_path.add(os.path.dirname(font_file)+"/*.otf")
                
        meta_data['font_binary_path'] = list(font_bin_path)[0].replace(meta_data['dir'],"")

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

    def findfiles(self, pattern, path, getabs=False):
        result = []
        path = path or "."
        path_patterns = pattern or ["*"]
        for root, dirs, files in os.walk(path):
            filter_partial = functools.partial(fnmatch.filter, files)
            for file_name in itertools.chain(*map(filter_partial, path_patterns)):
                if getabs:
                    f_name = os.path.join(root, file_name)    
                else:    
                    f_name = os.path.join(root.replace(path,""), file_name) 
                    if f_name.startswith("/"):
                        f_name = f_name.replace("/","")
                result.append(f_name)
        return result