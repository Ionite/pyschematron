#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys

from lxml import etree
from pyschematron.elements import Schema


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('schematron_file', help='the schematron file to process')
    parser.add_argument('xml_file', help='the xml file to validate')
    parser.add_argument('-v', '--verbosity', type=int, default=1, help='verbosity (0 for no output, 5 for full debug output)')
    args = parser.parse_args()

    schema = Schema(verbosity=args.verbosity)
    schema.read_from_file(args.schematron_file)
    schema.process_abstract_patterns()

    doc = etree.parse(args.xml_file)
    errors, warnings = schema.validate_document(doc)

    if args.verbosity > 0:
        for error in errors:
            print("Error: %s" % error.text)
        for warning in warnings:
            print("Error: %s" % warning.text)

    if args.verbosity > 0:
        print("File: %s" % args.xml_file)
    if len(errors) > 0:
        if args.verbosity > 0:
            print("%d errors in document" % len(errors))
        return -1
    if len(warnings) > 0:
        if args.verbosity > 0:
            print("%d warnings in document" % len(warnings))
        return 1
    if len(errors) == 0 and len(warnings) == 0:
        if args.verbosity > 0:
            print("All tests passed, no errors or warnings")
        return 0


if __name__ == '__main__':
    sys.exit(main())