'''
Created on Apr 27, 2015
@author: thansen

Modified on July 24, 2015
Elaine Hale
'''

import argparse
import os
from collections import OrderedDict

START_LICENSE = '[LICENSE]'
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','LICENSE')
END_LICENSE = '[/LICENSE]'


ARGS = OrderedDict()

ARGS['filename']     = ( [],
                        {'type'       :str, 
                         'help'       :'the python filename (or directory with [-d] or [--folder]) to add the license file to'} )

ARGS['-d']           = ( ['--folder'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) The provided first parameter is a directory.
                                         All .py files in the directory will add the license.
                                         Default: False"""} )

ARGS['-l']           = ( ['--license'],
                           {'default'    :LICENSE_FILE, 
                           'help'       :"""(optional) The filename of the license to add to the Python files"""} )

ARGS['-r']           = ( ['--recursive'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) Recursively add license to files. Only works if [-d] or [--folder] is specified."""} )

ARGS['-x']           = ( ['--remove'],
                          {'action'     :'store_true', 
                           'default'    :False, 
                           'help'       :"""(optional) Remove the license from the given file only, do not add the provided license."""} )


def get_file_linesep(s):
    lines_without = s.splitlines(False)
    lines_with = s.splitlines(True)
    if lines_without and lines_with:
        return lines_with[0][len(lines_without[0]):]
    return os.linesep


def get_header(s,sep=os.linesep):
    '''
    Splits .py file into its header and body. If no header is found on line 0, one is created.
    '''
    header = ''
    body = ''
    
    lines = s.splitlines(True)
    
    #check if has a header
    if (len(lines)) > 0 and (lines[0].startswith('#')):
        eoh = False
        for l in lines:
            if (not eoh) and (not l.startswith('#')):
                eoh = True
                if l == '' + sep:
                    # keep first blank line with header
                    header += l
                    continue
                else:
                    # make a blank line to keep
                    header += '' + sep
            if not eoh:
                header += l
            else:
                body += l
    else: #no header
        header = '' + sep
        body = s
    
    return header, body

def has_license(header):
    return (START_LICENSE in header) and (END_LICENSE in header)

def rem_license(header,sep=os.linesep):
    ret_header = ''
    if has_license(header):
        found_beg_license = False
        found_end_license = False
        for l in header.splitlines(True):
            #look for START_LICENSE
            if not found_beg_license:
                if START_LICENSE in l:
                    found_beg_license = True
                else:
                    ret_header += l
            #look for END_LICENSE if already found start
            elif not found_end_license:
                if END_LICENSE in l:
                    found_end_license = True
            #past the license portion, add remainder of header
            else:
                ret_header += l
            
    else: #no license to remove
        ret_header = header
        
    return ret_header

def add_license(header,lic,sep=os.linesep):
    if has_license(header):
        raise Exception('There is already a license in the provided header. Please rem_license prior to adding a new one.')
    
    ret_head = ''
    
    lines = header.splitlines(True)
    
    #add license to header
    ret_head += ('# ' + START_LICENSE + sep)
    count = 0
    for lic_l in lic.splitlines(True):
        ret_head += ('# ' + lic_l)
    ret_head += ('# ' + END_LICENSE + sep)
    
    #add the rest of the header
    for l in lines:
        ret_head += l
    
    return ret_head

def is_python_file(fname):
    return os.path.splitext(fname)[1].lower() == '.py'

def get_python_files(dirname):
    ret = []
    
    for item in os.listdir(dirname):
        full_path = os.path.join(dirname,item)
        if os.path.isfile(full_path) and is_python_file(item):
            ret.append(full_path)
    
    return ret

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Script for adding a license 
        to the header of Python files.""")
    
    #add the arguments from ARGS
    for key in ARGS.keys():
        parser.add_argument(key, *ARGS[key][0], **ARGS[key][1])
     
    args = parser.parse_args()
    
    #read current license
    with open(args.license) as f:
        current_license = f.read()
        
    #get filenames to change
    if not args.folder: #individual file
        if not is_python_file(args.filename):
            raise Exception('ERROR: \'%s\' is not a .py file' % args.filename)
        
        python_files = [args.filename]
    else: #directory
        python_files = []
        dirname = os.path.abspath(args.filename)
        if not args.recursive:
            python_files.extend(get_python_files(dirname))
        else:
            for cur_dir, sub_dirs, files in os.walk(dirname):
                python_files.extend(get_python_files(cur_dir))
        
    #iterate through files
    for current_file in python_files:
        if not args.remove:
            print('Adding license to: {}'.format(current_file))
        else:
            print('Removing license from: {}'.format(current_file))
        with open(current_file) as f:
            current_file_text = f.read()

        sep = get_file_linesep(current_file_text)
        header, body = get_header(current_file_text,sep=sep)
        
        if has_license(header):
            header = rem_license(header,sep=sep)
            
        #only add license if not remove-only
        if not args.remove:
            header = add_license(header,current_license,sep=sep)
        
        with open(current_file,'w') as f:
            f.write(header+body)
        
    