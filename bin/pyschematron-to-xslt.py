#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys
from lxml import etree
from pyschematron.elements import Schema
from pyschematron.xsl_generator import schema_to_xsl

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the schematron file to process')
    parser.add_argument('-o', '--output-format', help='output format, one of minimal or xslt (default)')
    args = parser.parse_args()


    schema = Schema()
    schema.read_from_file(args.filename)
    schema.process_abstract_patterns()

    if args.output_format == 'xslt':
        print(schema_to_xsl(schema))
    else:
        print(etree.tostring(schema.to_minimal_xml(minimal=True), pretty_print=True).decode('utf-8'))

if __name__=='__main__':
    sys.exit(main())