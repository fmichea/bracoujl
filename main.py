#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import sys

import bracoujl.graph
import bracoujl.writers.dotwriter
import bracoujl.writers.asciiwriter

def main():
    parser = argparse.ArgumentParser(description='Some debugging tool.')
    parser.add_argument('-o', '--output', action='store', required=False,
                        metavar='directory', help='output directory.')
    parser.add_argument('log', action='append', nargs='+',
                        help='log file correctly formatted.')
    args = parser.parse_args(sys.argv[1:])

#    output_filename = args.output if args.output else none
#    writer = bracoujl.writers.dotwriter.dotwriter(output_filename)
#    writer.generate(args.log[0])
#
#    sys.exit(0)

if __name__ == '__main__':
    main()
