import argparse
import logging
import os
from subprocess import call, list2cmdline

from layerstack import start_console_log

logger = logging.getLogger(__name__)

def convert_files(file_registry):
    # registry is expected to contain paths relative to its location
    base_path = os.path.dirname(file_registry)

    if not os.path.exists(file_registry):
        raise ValueError("File registry {} not found".format(file_registry))

    # loop through registry of md files
    with open(file_registry,'r') as registry:
        for line in registry:
            if line:
                # non-empty
                p = os.path.join(base_path,line.strip())
                p_md = p + '.md'
                if not os.path.exists(p_md):
                    raise ValueError("There is no {} file.".format(p_md))
                # run pandoc
                p_rst = p + '.rst'
                try:
                    cmd_and_args = ['pandoc',p_md,'-o',p_rst]
                    call(cmd_and_args)
                except Exception as e:
                    try:
                        call(['pandoc'])
                    except:
                        logger.error("Call to pandoc fails")
                        raise e
                    if not os.path.exists(p_md):
                        logger.error("Input file {} does not exist".format(p_md))
                        raise e
                    logger.error("Call '{}' failed".format(list2cmdline(cmd_and_args)))
                    raise e
                # append .postfix
                p_postfix = p + '.postfix'
                if os.path.exists(p_postfix):
                    with open(p_rst,'a') as rst:
                        rst.write("\n")
                        with open(p_postfix,'r') as postfix:
                            rst.write(postfix.read())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Utility to convert Markdown 
        (.md) files to reStructuredText (.rst)""")
    parser.add_argument('file_registry',help="""Text file that lists the 
        markdown files to convert. Each line is the file path and name for an 
        .md file, where the path is relative to the location of file_registry, 
        and the .md extension is omitted.""")
    parser.add_argument("-d","--debug",action='store_true',default=False,
        help="Option to output debug information.")
    
    args = parser.parse_args()

    # start logging
    start_console_log(log_level=logging.DEBUG if args.debug else logging.INFO)

    # perform conversion
    convert_files(args.file_registry)
