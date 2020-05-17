#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys

from pyschematron.commands.convert import main

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the schematron file to procewss')
    parser.add_argument('-f', '--output-format', default='xslt', help='output format, one of minimal or xslt (default)')
    parser.add_argument('-o', '--output-file', help='Write output to file instead of stdout')
    args = parser.parse_args()

    if args.output_file is None:
        sys.exit(main(args.filename, sys.stdout, args.output_format))
    else:
        with open(args.output_file, 'w') as outfile:
            sys.exit(main(args.filename, outfile, args.output_format))