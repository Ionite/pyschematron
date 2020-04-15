#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys

from pyschematron import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the schematron file to process')
    args = parser.parse_args()


    schema = Schema()
    schema.read_from_file(args.filename)
    schema.process_abstract_patterns()

    print(schema.to_xsl_str())

if __name__=='__main__':
    sys.exit(main())