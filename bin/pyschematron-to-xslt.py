#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys
from lxml import etree
from pyschematron.elements import Schema
from pyschematron.xml.xsl_generator import schema_to_xsl

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the schematron file to procewss')
    parser.add_argument('-o', '--output-format', default='xslt', help='output format, one of minimal or xslt (default)')
    args = parser.parse_args()


    schema = Schema()
    schema.read_from_file(args.filename)
    schema.process_abstract_patterns()

    if args.output_format == 'xslt':
        xsl_root = schema_to_xsl(schema)
        # Normalization: put all namespaces at the top level
        full_nsmap = xsl_root.nsmap
        #print(schema_to_xsl(schema))

        print(etree.tostring(xsl_root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8'))
    elif args.output_format == 'minimal':
        print(etree.tostring(schema.to_minimal_xml(minimal=True), pretty_print=True).decode('utf-8'))
    else:
        print("Unknown output format: %s" % args.output_format)
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())