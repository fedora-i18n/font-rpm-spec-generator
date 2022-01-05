import json
from src_lib import TemplateGenerator as TG
import argparse
import sys

def arg_parse():

    parser = argparse.ArgumentParser(prog='main',
                                    usage='%(prog)s [options]',
                                    description='Font packaging tool',
                                    epilog='Happy Packaging :)')
    
    parser.add_argument("-f", "--file", help="Font file path")
    parser.add_argument("-D", "--dir", help="Font dir path")
    parser.add_argument("-l", "--lang", help="Specify lang which fontfile comply")
    parser.add_argument("-d", "--description", help="Description of your fontfile")
    parser.add_argument("-s", "--summary", help="short summary of your fontfile")
    parser.add_argument("-u", "--url", help="Font Project URL")
    parser.add_argument("-S", "--source", help="Font source tar or path")

    return parser.parse_args()


if __name__ == "__main__":

    
    args = arg_parse()
    input_data = dict()
    # parse input and add into dict
    for arg in vars(args):
        input_data[arg] = getattr(args, arg)
    
    #fontfile = '/usr/share/fonts/smc-meera/Meera-Regular.ttf'
    # fontfile = '/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf'
    
    # compare cli args and conf.json and override input data
    with open('./config.json') as f:
        confdata = json.load(f)
       
    for conf,value in confdata.items():
        if conf not in input_data.keys():
            input_data[conf] = value
        elif value == "":
            input_data[conf] = None
        elif (input_data[conf] == None and value != ""):
            input_data[conf] = value
    
    # default if no args passed
    if len(sys.argv)==1 and ('file' not in input_data.keys() or 'dir' not in input_data.keys()):
        args.print_help(sys.stderr)
        sys.exit(1)
        
    tg_obj = TG()
    tg_obj.template_generator(input_data)