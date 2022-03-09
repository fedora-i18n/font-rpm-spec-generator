#!/usr/bin/python3
import json, os
from src_lib import TemplateGenerator as TG
import argparse
import sys
import datetime

def arg_parse():
    
    parser = argparse.ArgumentParser(prog='main',
                                    usage='%(prog)s [options]',
                                    description='Font packaging tool',
                                    epilog='Happy Packaging :)')
    
    parser.add_argument("-D", "--dir", help="Font dir path")
    parser.add_argument("-l", "--lang", help="Specify lang which fontfile comply")
    parser.add_argument("-d", "--description", help="Description of your fontfile")
    parser.add_argument("-s", "--summary", help="short summary of your fontfile")
    parser.add_argument("-u", "--url", help="Font Project URL")
    parser.add_argument("-S", "--source", help="Font source tar or path")

    return (parser.parse_args(), parser)

def conf_file_parser(config_file,input_data):

    # compare cli args and conf.json and override input data
    with open(config_file) as f:
        confdata = json.load(f)
       
    for conf,value in confdata.items():
        if conf not in input_data.keys():
            input_data[conf] = value
        elif value == "":
            input_data[conf] = None
        elif (input_data[conf] == None and value != ""):
            input_data[conf] = value
    
    return input_data


if __name__ == "__main__":

    input_data = dict()
    args, parser_obj = arg_parse()
    
    # if len(sys.argv) < 2:
    #     parser_obj.print_help()
    #     sys.exit(1)

    # parse input and add into dict
    for arg in vars(args):
        input_data[arg] = getattr(args, arg)
    
    # compare cli args and conf.json and override input data
    input_data = conf_file_parser("./config.json", input_data)
    
    # # default if no args passed
    # if len(sys.argv)==1 and ('file' not in input_data.keys() or 'dir' not in input_data.keys()):
    #     args.print_help(sys.stderr)
    #     sys.exit(1)
    
    # data for changelog & metainfo.xml entries 
    input_data['username'] = os.environ.get("USERNAME")
    input_data['datetime'] = datetime.datetime.now().strftime("%a %b %d %Y")

    # template generator
    tg_obj = TG()
    tg_obj.template_generator(input_data)