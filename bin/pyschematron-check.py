#!/usr/bin/env python3

# Copyright (c) 2020 Ionite
# See LICENSE for the license

import argparse
import sys
from pyschematron.commands.validate import main

if __name__ == '__main__':
    #sys.exit(main())
    parser = argparse.ArgumentParser()
    parser.add_argument('schematron_file', help='the schematron file to process')
    parser.add_argument('xml_file', help='the xml file to validate')
    parser.add_argument('-p', '--phase', default="#DEFAULT", help="The phase to run")
    parser.add_argument('-v', '--verbosity', type=int, default=1, help='verbosity (0 for no output, 5 for full debug output)')
    parser.add_argument('-t', '--output-type', default='text', help='output type (text, svrl)')
    parser.add_argument('-o', '--output-file', help='Write output to file instead of stdout')
    args = parser.parse_args()

    if args.output_file:
        with open(args.output_file, 'w') as outfile:
            rcode = main(args.schematron_file, args.xml_file, args.phase, args.output_type, outfile, args.verbosity)
    else:
        rcode = main(args.schematron_file, args.xml_file, args.phase, args.output_type, sys.stdout, args.verbosity)
    sys.exit(rcode)