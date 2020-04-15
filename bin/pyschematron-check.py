#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys

from pyschematron import *
from elementpath import ElementPathError, XPath2Parser, XPathContext, select, iter_select


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('schematron_file', help='the schematron file to process')
    parser.add_argument('xml_file', help='the xml file to validate')
    args = parser.parse_args()

    schema = Schema()
    schema.read_from_file(args.schematron_file)
    schema.process_abstract_patterns()

    doc = etree.parse(args.xml_file)
    errors, warnings = schema.validate_document(doc)

    for error in errors:
        print("Error: %s" % error.text)
    for warning in warnings:
        print("Error: %s" % warning.text)

    print("File: %s" % args.xml_file)
    if len(errors) > 0:
        print("%d errors in document" % len(errors))
    if len(warnings) > 0:
        print("%d warnings in document" % len(warnings))
    if len(errors) == 0 and len(warnings) == 0:
        print("All tests passed, no errors or warnings")


if __name__ == '__main__':
    sys.exit(main())