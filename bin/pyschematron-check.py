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
    args = parser.parse_args()

    rcode = main(args.schematron_file, args.xml_file, args.phase, args.verbosity)
    sys.exit(rcode)